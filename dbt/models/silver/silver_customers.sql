with latest as (
    {{ latest_rows('customers') }}
)

select
    {{ field('customer_id') }}               as customer_id,
    {{ field('customer_unique_id') }}        as customer_unique_id,  -- the real person (one per customer_id per order)
    {{ field('customer_zip_code_prefix') }}  as zip_code_prefix,
    {{ field('customer_city') }}             as city,
    {{ field('customer_state') }}            as state
from latest
