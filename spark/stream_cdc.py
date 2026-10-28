"""Stream Debezium change events from Redpanda into an Iceberg bronze table.

Exactly-once, in two halves:
  1. Spark's checkpoint remembers which Kafka offsets were processed, so a restart resumes there.
  2. If a micro-batch is retried after a crash, the MERGE skips rows whose
     (topic, partition, offset) is already in the table, so nothing is written twice.

Bronze keeps every change as raw JSON (before/after). A new MySQL column therefore
never breaks this job; dbt picks the fields it needs later (schema evolution).
"""

import os

from pyspark.sql import SparkSession
from pyspark.sql import functions as F

KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP", "redpanda:9092")
TOPIC_PATTERN = os.getenv("TOPIC_PATTERN", r"shop\.shop\..*")
CHECKPOINT = os.getenv("CHECKPOINT_DIR", "/checkpoints/bronze_cdc_events")
TRIGGER = os.getenv("TRIGGER_INTERVAL", "15 seconds")
TABLE = "lake.bronze.cdc_events"

spark = SparkSession.builder.appName("cdc-to-bronze").getOrCreate()
spark.sparkContext.setLogLevel("WARN")

spark.sql("CREATE NAMESPACE IF NOT EXISTS lake.bronze")
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {TABLE} (
        source_table     STRING    COMMENT 'MySQL table the change came from',
        op               STRING    COMMENT 'c=create, u=update, d=delete, r=snapshot read',
        row_key          STRING    COMMENT 'primary key of the changed row, as JSON',
        before           STRING    COMMENT 'row before the change, as JSON (null for inserts)',
        after            STRING    COMMENT 'row after the change, as JSON (null for deletes)',
        source_ts_ms     BIGINT    COMMENT 'when MySQL committed the change',
        binlog_file      STRING,
        binlog_pos       BIGINT,
        gtid             STRING,
        kafka_topic      STRING,
        kafka_partition  INT,
        kafka_offset     BIGINT,
        kafka_timestamp  TIMESTAMP,
        ingested_at      TIMESTAMP COMMENT 'when Spark wrote it to the lake'
    )
    USING iceberg
    PARTITIONED BY (source_table)
""")

raw = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP)
    .option("subscribePattern", TOPIC_PATTERN)
    .option("startingOffsets", "earliest")
    .option("maxOffsetsPerTrigger", 50000)
    .option("failOnDataLoss", "false")
    .load()
)

value = F.col("value").cast("string")
events = (
    raw.where(F.col("value").isNotNull())  # Debezium sends an empty "tombstone" after each delete
    .select(
        F.get_json_object(value, "$.source.table").alias("source_table"),
        F.get_json_object(value, "$.op").alias("op"),
        F.col("key").cast("string").alias("row_key"),
        F.get_json_object(value, "$.before").alias("before"),
        F.get_json_object(value, "$.after").alias("after"),
        F.get_json_object(value, "$.source.ts_ms").cast("bigint").alias("source_ts_ms"),
        F.get_json_object(value, "$.source.file").alias("binlog_file"),
        F.get_json_object(value, "$.source.pos").cast("bigint").alias("binlog_pos"),
        F.get_json_object(value, "$.source.gtid").alias("gtid"),
        F.col("topic").alias("kafka_topic"),
        F.col("partition").alias("kafka_partition"),
        F.col("offset").alias("kafka_offset"),
        F.col("timestamp").alias("kafka_timestamp"),
        F.current_timestamp().alias("ingested_at"),
    )
)


def write_batch(batch, batch_id):
    """Idempotent write: a retried batch inserts only the rows that are not there yet."""
    batch.createOrReplaceTempView("incoming")
    batch.sparkSession.sql(f"""
        MERGE INTO {TABLE} t
        USING incoming s
        ON  t.source_table    = s.source_table
        AND t.kafka_topic     = s.kafka_topic
        AND t.kafka_partition = s.kafka_partition
        AND t.kafka_offset    = s.kafka_offset
        WHEN NOT MATCHED THEN INSERT *
    """)
    print(f"batch {batch_id}: {batch.count()} change events", flush=True)


query = (
    events.writeStream.foreachBatch(write_batch)
    .option("checkpointLocation", CHECKPOINT)
    .trigger(processingTime=TRIGGER)
    .start()
)
query.awaitTermination()
