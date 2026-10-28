with latest as (
    {{ latest_rows('sellers') }}
)

select
    {{ field('seller_id') }}               as seller_id,
    {{ field('seller_zip_code_prefix') }}  as zip_code_prefix,
    {{ field('seller_city') }}             as city,
    {{ field('seller_state') }}            as state
from latest
