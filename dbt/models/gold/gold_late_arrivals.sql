-- Late-arriving data: reviews written long after the order was delivered.
-- Because gold is computed by event time, these still land on the right order and month.

select
    date_trunc('month', f.delivered_at)                               as delivery_month,
    count(*)                                                          as reviews,
    count_if(date_diff('day', f.delivered_at, r.created_at) > 30)     as reviews_over_30_days_late,
    max(date_diff('day', f.delivered_at, r.created_at))               as max_days_late
from {{ ref('silver_order_reviews') }} r
join {{ ref('gold_order_facts') }} f on r.order_id = f.order_id
where f.delivered_at is not null
group by 1
