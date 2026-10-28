select
    coalesce(customer_state, 'unknown')                             as customer_state,
    count(*)                                                        as orders,
    coalesce(sum(order_value) filter (where not is_cancelled), 0)   as revenue
from {{ ref('gold_order_facts') }}
group by 1
