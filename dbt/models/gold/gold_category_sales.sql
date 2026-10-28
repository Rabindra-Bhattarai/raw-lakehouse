select
    p.category,
    count(distinct i.order_id)          as orders,
    sum(i.price)                        as revenue
from {{ ref('silver_order_items') }} i
join {{ ref('silver_products') }} p on i.product_id = p.product_id
join {{ ref('gold_order_facts') }} f on i.order_id = f.order_id
where not f.is_cancelled
group by p.category
