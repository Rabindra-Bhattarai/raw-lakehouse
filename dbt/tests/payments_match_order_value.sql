-- Data quality: what the customer paid should equal items + shipping (within 1 BRL).
-- Real Olist data has a few mismatches (vouchers, instalment interest), so this warns instead of failing.
{{ config(severity='warn') }}

select order_id, order_value, paid_value
from {{ ref('gold_order_facts') }}
where paid_value is not null
  and items > 0
  and abs(paid_value - order_value) > 1
