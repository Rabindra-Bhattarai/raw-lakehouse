{#- Fails for every combination of the columns that appears more than once (the table's grain is broken). -#}
{% test unique_combination(model, columns) %}
select {{ columns | join(', ') }}, count(*) as copies
from {{ model }}
group by {{ columns | join(', ') }}
having count(*) > 1
{% endtest %}
