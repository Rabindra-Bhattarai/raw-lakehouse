# raw-lakehouse

A real-time **CDC (Change Data Capture) lakehouse** that runs locally in Docker, built step by step while learning data engineering.

It takes a real e-commerce database, catches every change as it happens, and turns it into a live dashboard.

> 🚧 **Work in progress.** Step 1 of 8 is underway. See [Progress](#progress).

## Architecture (planned)

```
MySQL ──► Debezium ──► Redpanda ──► Spark Structured Streaming ──► Apache Iceberg on MinIO ──► Trino ──► dbt ──► Superset
source    reads the     event         streams changes               lakehouse tables            SQL       bronze →   dashboard
database  binlog        stream        into the lake                 (S3-compatible storage)     engine    silver →
                                                                                                           gold
```

| Layer | Tool | Role |
|---|---|---|
| Source | MySQL 8.4 | The shop's operational database, with the binlog enabled |
| Capture | Debezium | Reads every insert, update and delete from the binlog |
| Transport | Redpanda | Kafka-compatible stream that holds change events in order |
| Processing | Spark Structured Streaming (PySpark) | Writes the changes into the lakehouse |
| Storage | Apache Iceberg on MinIO | Tables with history, on S3-compatible object storage |
| Query | Trino | SQL over the lakehouse |
| Transform | dbt | Bronze → silver → gold models |
| Serve | Superset | Dashboards |

Planned topics: exactly-once processing, schema changes, late-arriving data, data quality checks, tests, and GitHub Actions CI.

## Dataset

The project uses the real [Olist Brazilian E-Commerce dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce): about 100k orders from 2016–2018, with customers, sellers, products, payments and reviews. It is licensed **CC BY-NC-SA 4.0** and is **not included in this repository**.

The dataset is a snapshot, so a replay script (in progress) turns it back into a stream of events: order placed → approved → shipped → delivered → reviewed. Those events are applied to MySQL in time order, so it behaves like a live shop.

**To get the data:**
1. Download it from Kaggle (a free account is needed).
2. Unzip the CSV files into `data/olist/`, for example `data/olist/olist_orders_dataset.csv`.

## Getting started

Requirements: Docker Desktop (with WSL 2 on Windows) and Python 3.

**1. Start MySQL**
```bash
docker compose up -d
docker compose ps        # mysql should show "Up"
```
MySQL is exposed on host port **3307**. The data folder `data/olist` is mounted at `/var/lib/mysql-files`, the only folder MySQL may load files from.

**2. Create the activity tables** (customers, orders, order items, payments, reviews)
```bash
docker exec -i mysql mysql -uroot -prootpass shop < mysql/activity_tables.sql
```
On Windows PowerShell:
```powershell
Get-Content mysql\activity_tables.sql | docker exec -i mysql mysql -uroot -prootpass shop
```

**3. Python environment for the replay script**
```bash
python -m venv .venv
.venv\Scripts\activate          # Windows  (Linux/macOS: source .venv/bin/activate)
pip install -r replayer/requirements.txt
```

> The credentials in `docker-compose.yml` are local demo values only. Never use them in a real system.

## Project structure

```
raw-lakehouse/
├── docker-compose.yml        # MySQL with binlog + GTID enabled for CDC
├── mysql/
│   └── activity_tables.sql   # empty tables filled by the replay script
├── replayer/
│   └── requirements.txt      # pymysql, cryptography, pandas
└── data/olist/               # Olist CSVs (downloaded separately, git-ignored)
```

## Progress

- [ ] **Step 1: MySQL source + real data**
  - [x] MySQL in Docker with binlog, GTID and full row images
  - [x] Catalog tables loaded: sellers (3,095), products (32,951), categories (71)
  - [x] Activity tables created
  - [ ] Save the catalog load SQL as a file
  - [ ] Replay script: stream orders into MySQL in time order
- [ ] Step 2: Debezium + Redpanda: capture the changes
- [ ] Step 3: MinIO + Iceberg + Spark streaming job
- [ ] Step 4: Trino: query the lakehouse
- [ ] Step 5: dbt models: bronze → silver → gold
- [ ] Step 6: Superset dashboard
- [ ] Step 7: Exactly-once, schema changes, late-arriving data
- [ ] Step 8: Data quality, tests, CI, final docs

## Data notes

Real data is messy. Issues found while profiling the dataset, to be handled in later steps:

- 775 orders have no items.
- 1,359 orders were handed to the carrier before they were approved (out-of-order timestamps).
- 547 orders have more than one review.
- 13 products use a category with no English translation.
- Product columns are misspelled in the source (`lenght`); they are renamed to `length` on load.
- Some reviews arrive up to 106 days after delivery, which is real late-arriving data.
