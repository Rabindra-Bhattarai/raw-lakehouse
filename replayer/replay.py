import time

import pandas as pd
import pymysql

DATA_DIR = "data/olist"
EVENTS_PER_SECOND = 20

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
def place_order(cur, order):
    """INSERT a new order, with its customer, items and payments."""
    customer = customers.loc[order["customer_id"]]
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
    if order["order_id"] in items_by_order:
        cur.executemany(
            "INSERT INTO order_items VALUES (%s, %s, %s, %s, %s, %s, %s)",
            items_by_order[order["order_id"]],
        )
    if order["order_id"] in payments_by_order:
        cur.executemany(
            "INSERT INTO order_payments VALUES (%s, %s, %s, %s, %s)",
            payments_by_order[order["order_id"]],
        )


def apply_event(cur, event):
    """Run the SQL for one event."""
    when, status, order_id = event
    order = orders.loc[order_id]
    if status == "placed":
        place_order(cur, order)
    elif status in STATUS_COLUMN:
        column = STATUS_COLUMN[status]
        cur.execute(
            f"UPDATE orders SET order_status = %s, {column} = %s WHERE order_id = %s",
            (status, order[column], order_id),
        )
    else:
        cur.execute(
            "UPDATE orders SET order_status = %s WHERE order_id = %s",
            (status, order_id),
        )
# ---------- load the data ----------
orders = read_csv("orders").set_index("order_id", drop=False)
customers = read_csv("customers").set_index("customer_id", drop=False)
items = read_csv("order_items")
payments = read_csv("order_payments")

items_by_order = {}
for row in items.itertuples(index=False, name=None):
    items_by_order.setdefault(row[0], []).append(row)

payments_by_order = {}
for row in payments.itertuples(index=False, name=None):
    payments_by_order.setdefault(row[0], []).append(row)

all_events = []
for _, order in orders.iterrows():
    all_events.extend(order_to_events(order))
all_events.sort(key=lambda event: event[0])
print("total events:", len(all_events))


conn = pymysql.connect(
    host="127.0.0.1",
    port=3307,
    user="shop",
    password="shop",
    database="shop",
)

with conn.cursor() as cur:
    cur.execute("SELECT next_event FROM replay_state WHERE id = 1")
    start = cur.fetchone()[0]
    print("starting at event", start)
    for number in range(start, len(all_events)):
        event = all_events[number]
        apply_event(cur, event)
        cur.execute("UPDATE replay_state SET next_event = %s WHERE id = 1", (number + 1,))
        conn.commit()
        print(number + 1, event)
        time.sleep(1 / EVENTS_PER_SECOND)


conn.close()
