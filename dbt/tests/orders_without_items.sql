-- Data quality: 775 real Olist orders have no items. Report them, but don't block the pipeline.
{{ config(severity='warn') }}

select order_id, order_status
from {{ ref('gold_order_facts') }}
where items = 0
  and not is_cancelled
