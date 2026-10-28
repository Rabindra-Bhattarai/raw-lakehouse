-- One row of headline numbers, plus how fresh the pipeline is.

select
    count(*)                                                        as total_orders,
    coalesce(sum(order_value) filter (where not is_cancelled), 0)   as total_revenue,
    round(avg(review_score), 2)                                     as avg_review_score,
    round(100.0 * count_if(is_late) / nullif(count_if(delivered_at is not null), 0), 1) as late_delivery_pct,
    max(purchased_at)                                               as shop_clock,
    max(ingested_at)                                                as last_ingested_at,
    date_diff('second', max(ingested_at), cast(current_timestamp as timestamp(6))) as seconds_since_last_ingest
from {{ ref('gold_order_facts') }}
