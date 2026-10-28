-- Exactly-once check: every Kafka message must be in bronze exactly one time,
-- even after Spark crashes and retries a batch.

select kafka_topic, kafka_partition, kafka_offset, count(*) as copies
from {{ source('bronze', 'cdc_events') }}
group by kafka_topic, kafka_partition, kafka_offset
having count(*) > 1
