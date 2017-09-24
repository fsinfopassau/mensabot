{% import 'de/utils.md' as utils %}
Cafete {{ location.name }}
{%- if not open_info %}
 zur Zeit geschlossen.
{% elif open_info.offset == 0 and datetime.time() < open_info.open %}
 geschlossen, öffnet um {{ open_info.open|format_time('short', locale=locale) }} Uhr.
{% elif open_info.offset == 0 %}
 offen bis {{ open_info.close|format_time('short', locale=locale) }} Uhr.
{% else %}
 geschlossen, öffnet {{ utils.date(open_info.day, now, locale) }} um {{ open_info.open|format_time('short', locale=locale) }} Uhr.
{% endif %}
```text
{% for row in schedule -%}
{{ row.day|format_date('EEE ', locale=locale) }}
{%- if (row.open, row.close) == NOT_OPEN -%}
geschlossen
{%- else -%}
{{ row.open|format_time('short', locale=locale) }} - {{ row.close|format_time('short', locale=locale) }}
{%- endif %}

{% endfor %}
```
