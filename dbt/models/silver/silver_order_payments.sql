with latest as (
    {{ latest_rows('order_payments') }}
)

select
    {{ field('order_id') }}                                as order_id,
    cast({{ field('payment_sequential') }} as integer)     as payment_sequential,
    {{ field('payment_type') }}                            as payment_type,
    cast({{ field('payment_installments') }} as integer)   as payment_installments,
    {{ money_field('payment_value') }}                     as payment_value
from latest
