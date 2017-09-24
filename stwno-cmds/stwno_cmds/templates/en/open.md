{% import 'en/utils.md' as utils %}
Cafete {{ location.name }}
{%- if not open_info %}
 closed in this timeframe.
{% elif open_info.offset == 0 and datetime.time() < open_info.open %}
 closed, but opens at {{ open_info.open|format_time('short', locale=locale) }}.
{% elif open_info.offset == 0 %}
 open until {{ open_info.close|format_time('short', locale=locale) }}.
{% else %}
 closed, opens {{ utils.date(open_info.day, now, locale) }} at {{ open_info.open|format_time('short', locale=locale) }}.
{% endif %}
```text
{% for row in schedule -%}
{{ row.day|format_date('EEE ', locale=locale) }}
{%- if (row.open, row.close) == NOT_OPEN -%}
closed
{%- else -%}
{{ row.open|format_time('short', locale=locale) }} - {{ row.close|format_time('short', locale=locale) }}
{%- endif %}

{% endfor %}
```
