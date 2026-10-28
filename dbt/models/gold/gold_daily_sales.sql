-- Sales per day, by event time (the day the customer bought), not by when we received the data.
-- So a late change to an old order corrects that old day instead of inflating today.
-- Cancelled orders are counted, but never included in revenue.

select
    order_date,
    count(*)                                                        as orders,
    count_if(is_cancelled)                                          as cancelled_orders,
    coalesce(sum(order_value) filter (where not is_cancelled), 0)   as revenue,
    round(avg(order_value) filter (where not is_cancelled), 2)      as avg_order_value
from {{ ref('gold_order_facts') }}
group by order_date
