-- One row per order with everything the dashboards need. The other gold models build on this.

with items as (
    select
        order_id,
        count(*)            as items,
        sum(price)          as items_value,
        sum(freight_value)  as freight_value
    from {{ ref('silver_order_items') }}
    group by order_id
),

payments as (
    select order_id, sum(payment_value) as paid_value
    from {{ ref('silver_order_payments') }}
    group by order_id
),

reviews as (
    -- 547 orders have more than one review; use the newest one.
    select order_id, review_score, created_at as reviewed_at
    from (
        select *, row_number() over (partition by order_id order by created_at desc) as rn
        from {{ ref('silver_order_reviews') }}
    )
    where rn = 1
)

select
    o.order_id,
    o.order_status,
    o.purchased_at,
    cast(o.purchased_at as date)                        as order_date,
    date_trunc('month', o.purchased_at)                 as order_month,
    c.state                                             as customer_state,
    coalesce(i.items, 0)                                as items,
    coalesce(i.items_value, 0) + coalesce(i.freight_value, 0) as order_value,
    p.paid_value,
    o.order_status in ('canceled', 'unavailable')       as is_cancelled,
    o.delivered_at,
    o.estimated_delivery_at,
    date_diff('day', o.purchased_at, o.delivered_at)    as delivery_days,
    case
        when o.delivered_at is null then null
        else o.delivered_at > o.estimated_delivery_at
    end                                                 as is_late,
    r.review_score,
    r.reviewed_at,
    o.changed_at,
    o.ingested_at
from {{ ref('silver_orders') }} o
left join items i       on o.order_id = i.order_id
left join payments p    on o.order_id = p.order_id
left join reviews r     on o.order_id = r.order_id
left join {{ ref('silver_customers') }} c on o.customer_id = c.customer_id
