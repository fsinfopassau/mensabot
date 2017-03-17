Cafete {{ loc }} 
{%- if not open_info %}
 closed in this timeframe
{% elif open_info.offset == 0 and date.time() < open_info.open %}
 closed, but opens at {{ open_info.open }}
{% elif open_info.offset == 0 %}
 open until {{ open_info.close }}
{% else %}
 closed, opens in {{ open_info.offset }} days at {{ open_info.open }}
{% endif %}
```text
{% for row in schedule -%}
{{ "{:%a} ".format(row.day) }}
{%- if (row.open, row.close) == NOT_OPEN -%}
closed
{%- else -%}
{{ "{:%H:%M} - {:%H:%M}".format(row.open, row.close) }}
{%- endif %}

{% endfor %}
```
