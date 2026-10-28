"""Replay the real Olist dataset into MySQL, in time order.

Olist is a snapshot: each order row already holds its whole history.
This script splits that history back into events, sorts them by time and
applies them one by one, so MySQL changes the way it did when the shop was live.

Settings come from environment variables, with defaults for running on the host:
    MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE,
    DATA_DIR, EVENTS_PER_SECOND
"""

import os
import time

import pandas as pd
import pymysql

DATA_DIR = os.getenv("DATA_DIR", "data/olist")
EVENTS_PER_SECOND = float(os.getenv("EVENTS_PER_SECOND", "20"))

# (column that holds the time, status the order moves to)
LIFECYCLE = [
    ("order_approved_at", "approved"),
    ("order_delivered_carrier_date", "shipped"),
    ("order_delivered_customer_date", "delivered"),
]

# status -> the column that stores its time, e.g. "shipped" -> "order_delivered_carrier_date"
STATUS_COLUMN = {status: column for column, status in LIFECYCLE}


def read_csv(name):
    """Read one Olist CSV as text, with empty cells as None (SQL NULL)."""
    df = pd.read_csv(f"{DATA_DIR}/olist_{name}_dataset.csv", dtype=str)
    return df.astype(object).where(df.notna(), None)


def order_to_events(order):
    """Split one order row into its events, never going back in time."""
    events = [(order["order_purchase_timestamp"], "placed", order["order_id"])]
    last_status = "created"
    for column, status in LIFECYCLE:
        when = order[column]
        if pd.notna(when):
            when = max(when, events[-1][0])
            events.append((when, status, order["order_id"]))
            last_status = status
    if order["order_status"] != last_status:
        last_time = events[-1][0]
        events.append((last_time, order["order_status"], order["order_id"]))
    return events


def review_to_events(review, review_number, placed_at):
    """A review is written (and maybe answered) after its order was placed.

    Reviews are the dataset's real late-arriving data: some come months after delivery.
    """
    if review["review_creation_date"] is None:
        return []
    created = max(review["review_creation_date"], placed_at)
    events = [(created, "review", review_number)]
    if review["review_answer_timestamp"] is not None:
        answered = max(review["review_answer_timestamp"], created)
        events.append((answered, "review_answered", review_number))
    return events


def build_timeline(orders, reviews):
    """All events of the shop, sorted by time (stable, so same-time events keep their order)."""
    events = []
    for _, order in orders.iterrows():
        events.extend(order_to_events(order))
    placed_at = orders["order_purchase_timestamp"]
    for number, review in enumerate(reviews):
        if review["order_id"] in placed_at.index:
            events.extend(review_to_events(review, number, placed_at[review["order_id"]]))
    events.sort(key=lambda event: event[0])
    return events


def load_data():
    """Read the CSVs and build fast lookups by id."""
    orders = read_csv("orders").set_index("order_id", drop=False)
    items_by_order = {}
    for row in read_csv("order_items").itertuples(index=False, name=None):
        items_by_order.setdefault(row[0], []).append(row)
    payments_by_order = {}
    for row in read_csv("order_payments").itertuples(index=False, name=None):
        payments_by_order.setdefault(row[0], []).append(row)
    return {
        "orders": orders,
        "customers": read_csv("customers").set_index("customer_id", drop=False),
        "items_by_order": items_by_order,
        "payments_by_order": payments_by_order,
        "reviews": read_csv("order_reviews").to_dict("records"),
    }


def place_order(cur, data, order):
    """INSERT a new order, with its customer, items and payments."""
    customer = data["customers"].loc[order["customer_id"]]
    cur.execute(
        "INSERT INTO customers (customer_id, customer_unique_id, customer_zip_code_prefix, "
        "customer_city, customer_state) VALUES (%s, %s, %s, %s, %s)",
        tuple(customer),
    )
    cur.execute(
        "INSERT INTO orders (order_id, customer_id, order_status, order_purchase_timestamp, "
        "order_estimated_delivery_date) VALUES (%s, %s, 'created', %s, %s)",
        (order["order_id"], order["customer_id"],
         order["order_purchase_timestamp"], order["order_estimated_delivery_date"]),
    )
    if order["order_id"] in data["items_by_order"]:
        cur.executemany(
            "INSERT INTO order_items VALUES (%s, %s, %s, %s, %s, %s, %s)",
            data["items_by_order"][order["order_id"]],
        )
    if order["order_id"] in data["payments_by_order"]:
        cur.executemany(
            "INSERT INTO order_payments VALUES (%s, %s, %s, %s, %s)",
            data["payments_by_order"][order["order_id"]],
        )


def apply_event(cur, data, event):
    """Run the SQL for one event."""
    _, action, key = event
    if action == "review":
        review = data["reviews"][key]
        cur.execute(
            "INSERT INTO order_reviews (review_id, order_id, review_score, review_comment_title, "
            "review_comment_message, review_creation_date) VALUES (%s, %s, %s, %s, %s, %s)",
            (review["review_id"], review["order_id"], review["review_score"],
             review["review_comment_title"], review["review_comment_message"],
             review["review_creation_date"]),
        )
    elif action == "review_answered":
        review = data["reviews"][key]
        cur.execute(
            "UPDATE order_reviews SET review_answer_timestamp = %s "
            "WHERE review_id = %s AND order_id = %s",
            (review["review_answer_timestamp"], review["review_id"], review["order_id"]),
        )
    elif action == "placed":
        place_order(cur, data, data["orders"].loc[key])
    elif action in STATUS_COLUMN:
        column = STATUS_COLUMN[action]
        cur.execute(
            f"UPDATE orders SET order_status = %s, {column} = %s WHERE order_id = %s",
            (action, data["orders"].loc[key][column], key),
        )
    else:
        cur.execute(
            "UPDATE orders SET order_status = %s WHERE order_id = %s",
            (action, key),
        )


def connect():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST", "127.0.0.1"),
        port=int(os.getenv("MYSQL_PORT", "3307")),
        user=os.getenv("MYSQL_USER", "shop"),
        password=os.getenv("MYSQL_PASSWORD", "shop"),
        database=os.getenv("MYSQL_DATABASE", "shop"),
    )


def main():
    data = load_data()
    all_events = build_timeline(data["orders"], data["reviews"])
    print("total events:", len(all_events), flush=True)

    conn = connect()
    log_every = max(1, int(EVENTS_PER_SECOND))  # about one log line per second
    with conn.cursor() as cur:
        cur.execute("SELECT next_event FROM replay_state WHERE id = 1")
        start = cur.fetchone()[0]
        print("starting at event", start, flush=True)
        for number in range(start, len(all_events)):
            event = all_events[number]
            apply_event(cur, data, event)
            # Same transaction as the event: both are saved, or neither is (exactly-once).
            cur.execute("UPDATE replay_state SET next_event = %s WHERE id = 1", (number + 1,))
            conn.commit()
            if number % log_every == 0:
                print(number + 1, event, flush=True)
            time.sleep(1 / EVENTS_PER_SECOND)
    conn.close()
    print("finished: the whole dataset has been replayed", flush=True)


if __name__ == "__main__":
    main()
