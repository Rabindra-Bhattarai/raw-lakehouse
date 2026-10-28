-- Products with their English category name. 13 products use a category missing from the
-- translation table; for those we keep the Portuguese name instead of showing NULL.

with products as (
    {{ latest_rows('products') }}
),

translations as (
    select
        {{ field('product_category_name') }}          as category_pt,
        {{ field('product_category_name_english') }}  as category_en
    from ({{ latest_rows('product_category_name_translation') }})
)

select
    {{ field('product_id') }}                                    as product_id,
    {{ field('product_category_name') }}                         as category_pt,
    coalesce(t.category_en, {{ field('product_category_name') }}, 'unknown') as category,
    cast({{ field('product_weight_g') }} as integer)             as weight_g,
    cast({{ field('product_photos_qty') }} as integer)           as photos_qty
from products p
left join translations t
    on {{ field('product_category_name') }} = t.category_pt
