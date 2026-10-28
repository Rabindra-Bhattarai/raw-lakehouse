-- Are deliveries on time, and do late deliveries get worse reviews?

select
    order_month,
    count(*)                                            as delivered_orders,
    count_if(is_late)                                   as late_orders,
    round(100.0 * count_if(is_late) / count(*), 1)      as late_pct,
    round(avg(delivery_days), 1)                        as avg_delivery_days,
    round(avg(review_score) filter (where not is_late), 2) as avg_review_on_time,
    round(avg(review_score) filter (where is_late), 2)     as avg_review_late
from {{ ref('gold_order_facts') }}
where delivered_at is not null
group by order_month
