{#-
  Bronze holds every change ever made. The current state of a row is its newest change
  (highest Kafka offset for its primary key), unless that change was a delete.
-#}
{% macro latest_rows(source_table) %}
    select after, source_ts_ms, ingested_at
    from (
        select
            after,
            op,
            source_ts_ms,
            ingested_at,
            row_number() over (partition by row_key order by kafka_offset desc) as rn
        from {{ source('bronze', 'cdc_events') }}
        where source_table = '{{ source_table }}'
    )
    where rn = 1 and op <> 'd'
{% endmacro %}

{#- Read a text field from the row's JSON. -#}
{% macro field(name) -%}
    json_extract_scalar(after, '$.{{ name }}')
{%- endmacro %}

{#- Debezium sends MySQL DATETIME as epoch milliseconds. -#}
{% macro ts_field(name) -%}
    cast(from_unixtime(cast(json_extract_scalar(after, '$.{{ name }}') as bigint) / 1000.0) as timestamp(6))
{%- endmacro %}

{#- Debezium sends DECIMAL as a string (decimal.handling.mode=string), so no precision is lost. -#}
{% macro money_field(name) -%}
    cast(json_extract_scalar(after, '$.{{ name }}') as decimal(12, 2))
{%- endmacro %}
