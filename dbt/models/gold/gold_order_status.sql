-- How many orders are in each stage right now. Changes every few seconds while the shop runs.

select
    order_status,
    count(*) as orders
from {{ ref('silver_orders') }}
group by order_status
