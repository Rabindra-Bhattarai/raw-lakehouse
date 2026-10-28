with latest as (
    {{ latest_rows('order_reviews') }}
)

select
    {{ field('review_id') }}                         as review_id,
    {{ field('order_id') }}                          as order_id,
    cast({{ field('review_score') }} as integer)     as review_score,
    {{ field('review_comment_message') }} is not null as has_comment,
    {{ ts_field('review_creation_date') }}           as created_at,
    {{ ts_field('review_answer_timestamp') }}        as answered_at
from latest
