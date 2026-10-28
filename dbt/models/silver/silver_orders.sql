-- Current state of every order, typed and cleaned.
-- *_at columns are event time (when it happened in the shop);
-- changed_at is processing time (when MySQL saw the latest change).

with latest as (
    {{ latest_rows('orders') }}
)

select
    {{ field('order_id') }}                          as order_id,
    {{ field('customer_id') }}                       as customer_id,
    {{ field('order_status') }}                      as order_status,
    {{ ts_field('order_purchase_timestamp') }}       as purchased_at,
    {{ ts_field('order_approved_at') }}              as approved_at,
    {{ ts_field('order_delivered_carrier_date') }}   as shipped_at,
    {{ ts_field('order_delivered_customer_date') }}  as delivered_at,
    {{ ts_field('order_estimated_delivery_date') }}  as estimated_delivery_at,
    -- Schema evolution: this column was added to MySQL later (scripts/schema_change_demo.sql).
    -- Older change events don't have it, so it is NULL for them instead of breaking the model.
    {{ field('sales_channel') }}                     as sales_channel,
    cast(from_unixtime(source_ts_ms / 1000.0) as timestamp(6)) as changed_at,
    ingested_at
from latest
