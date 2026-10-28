"""Create the lakehouse dashboard through Superset's REST API.

Idempotent: objects are looked up by name first, so running it again changes nothing.
The gold views must exist (run dbt first); missing ones are skipped with a message.
"""

import json
import os
import time

import requests

BASE = "http://localhost:8088"
DB_NAME = "Lakehouse (Trino)"
DB_URI = os.getenv("TRINO_SQLALCHEMY_URI", "trino://superset@trino:8080/iceberg")
DASHBOARD = "Olist Live Lakehouse"


def sql_metric(expression, label):
    return {"expressionType": "SQL", "sqlExpression": expression, "label": label}


# (title, dataset, viz_type, extra params, width)
CHARTS = [
    ("Total orders", "gold_kpis", "big_number_total",
     {"metric": sql_metric("MAX(total_orders)", "Orders"), "y_axis_format": ",d"}, 3),
    ("Revenue (BRL)", "gold_kpis", "big_number_total",
     {"metric": sql_metric("MAX(total_revenue)", "Revenue"), "y_axis_format": ",.0f"}, 3),
    ("Average review", "gold_kpis", "big_number_total",
     {"metric": sql_metric("MAX(avg_review_score)", "Avg review"), "y_axis_format": ".2f"}, 3),
    ("Late deliveries %", "gold_kpis", "big_number_total",
     {"metric": sql_metric("MAX(late_delivery_pct)", "Late %"), "y_axis_format": ".1f"}, 3),
    ("Revenue per month", "gold_daily_sales", "echarts_timeseries_line",
     {"x_axis": "order_date", "time_grain_sqla": "P1M",
      "metrics": [sql_metric("SUM(revenue)", "Revenue")]}, 8),
    ("Orders by status (live)", "gold_order_status", "pie",
     {"groupby": ["order_status"], "metric": sql_metric("SUM(orders)", "Orders"),
      "show_labels": True}, 4),
    ("Revenue by state", "gold_sales_by_state", "echarts_timeseries_bar",
     {"x_axis": "customer_state", "metrics": [sql_metric("SUM(revenue)", "Revenue")],
      "row_limit": 10, "x_axis_sort": "Revenue", "x_axis_sort_asc": False}, 6),
    ("Late deliveries % per month", "gold_delivery_performance", "echarts_timeseries_line",
     {"x_axis": "order_month", "time_grain_sqla": "P1M",
      "metrics": [sql_metric("MAX(late_pct)", "Late %")]}, 6),
    ("Top categories", "gold_category_sales", "table",
     {"query_mode": "aggregate", "groupby": ["category"],
      "metrics": [sql_metric("SUM(revenue)", "Revenue"), sql_metric("SUM(orders)", "Orders")],
      "row_limit": 10, "order_desc": True,
      "timeseries_limit_metric": sql_metric("SUM(revenue)", "Revenue")}, 12),
]


def wait_for_server():
    for _ in range(120):
        try:
            if requests.get(f"{BASE}/health", timeout=5).ok:
                return
        except requests.RequestException:
            pass
        time.sleep(5)
    raise SystemExit("[setup] Superset did not start")


def login():
    session = requests.Session()
    token = session.post(f"{BASE}/api/v1/security/login", json={
        "username": os.getenv("ADMIN_USER", "admin"),
        "password": os.getenv("ADMIN_PASSWORD", "admin"),
        "provider": "db", "refresh": True,
    }).json()["access_token"]
    session.headers["Authorization"] = f"Bearer {token}"
    csrf = session.get(f"{BASE}/api/v1/security/csrf_token/").json()["result"]
    session.headers.update({"X-CSRFToken": csrf, "Referer": BASE})
    return session


def find(session, resource, column, value):
    query = json.dumps({"filters": [{"col": column, "opr": "eq", "value": value}]})
    result = session.get(f"{BASE}/api/v1/{resource}/", params={"q": query}).json().get("result", [])
    return result[0]["id"] if result else None


def create(session, resource, payload):
    response = session.post(f"{BASE}/api/v1/{resource}/", json=payload)
    if not response.ok:
        raise RuntimeError(f"{resource}: {response.status_code} {response.text[:300]}")
    return response.json()["id"]


def main():
    wait_for_server()
    session = login()

    if find(session, "dashboard", "dashboard_title", DASHBOARD):
        print("[setup] dashboard already exists, nothing to do")
        return

    db_id = find(session, "database", "database_name", DB_NAME) or create(session, "database", {
        "database_name": DB_NAME, "sqlalchemy_uri": DB_URI, "expose_in_sqllab": True,
    })

    datasets = {}
    for name in sorted({chart[1] for chart in CHARTS}):
        ds_id = find(session, "dataset", "table_name", name)
        if not ds_id:
            try:
                ds_id = create(session, "dataset", {"database": db_id, "schema": "gold", "table_name": name})
            except RuntimeError as error:
                print(f"[setup] skipping {name} (run dbt first?): {error}")
                continue
        datasets[name] = ds_id

    rows, row, row_width, chart_ids = [], [], 0, []
    for title, dataset, viz, params, width in CHARTS:
        if dataset not in datasets:
            continue
        ds_id = datasets[dataset]
        chart_id = create(session, "chart", {
            "slice_name": title, "viz_type": viz,
            "datasource_id": ds_id, "datasource_type": "table",
            "params": json.dumps({"viz_type": viz, "datasource": f"{ds_id}__table", **params}),
        })
        chart_ids.append(chart_id)
        if row_width + width > 12:
            rows.append(row)
            row, row_width = [], 0
        row.append((chart_id, width))
        row_width += width
    if row:
        rows.append(row)

    # Superset's layout format: ROOT -> GRID -> ROW -> CHART
    position = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {"type": "GRID", "id": "GRID_ID", "children": [], "parents": ["ROOT_ID"]},
        "HEADER_ID": {"type": "HEADER", "id": "HEADER_ID", "meta": {"text": DASHBOARD}},
    }
    for r, charts in enumerate(rows):
        row_id = f"ROW-{r}"
        position["GRID_ID"]["children"].append(row_id)
        position[row_id] = {"type": "ROW", "id": row_id, "children": [],
                            "parents": ["ROOT_ID", "GRID_ID"], "meta": {"background": "BACKGROUND_TRANSPARENT"}}
        for chart_id, width in charts:
            key = f"CHART-{chart_id}"
            position[row_id]["children"].append(key)
            position[key] = {"type": "CHART", "id": key, "children": [],
                             "parents": ["ROOT_ID", "GRID_ID", row_id],
                             "meta": {"chartId": chart_id, "width": width, "height": 50}}

    dashboard_id = create(session, "dashboard", {
        "dashboard_title": DASHBOARD, "slug": "olist-live", "published": True,
        "position_json": json.dumps(position),
        "json_metadata": json.dumps({"refresh_frequency": 30}),  # live: re-query every 30 s
    })
    for chart_id in chart_ids:
        session.put(f"{BASE}/api/v1/chart/{chart_id}", json={"dashboards": [dashboard_id]})
    print(f"[setup] dashboard ready: {BASE}/superset/dashboard/olist-live/")


if __name__ == "__main__":
    main()
