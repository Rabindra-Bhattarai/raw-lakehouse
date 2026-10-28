with latest as (
    {{ latest_rows('order_items') }}
)

select
    {{ field('order_id') }}                          as order_id,
    cast({{ field('order_item_id') }} as integer)    as order_item_id,
    {{ field('product_id') }}                        as product_id,
    {{ field('seller_id') }}                         as seller_id,
    {{ ts_field('shipping_limit_date') }}            as shipping_limit_at,
    {{ money_field('price') }}                       as price,
    {{ money_field('freight_value') }}               as freight_value
from latest
