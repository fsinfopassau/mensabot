{% macro date(dt, now) -%}
{% set delta = (dt.date() - now.date()).days %}
{% set relative_days = false %}
{% if delta == 0 %}
today, {% elif delta == -1 %}
yesterday, {% elif delta == 1 %}
tomorrow, {% else %}
{% set relative_days = true %}
{% endif %}
{{ "{:%A %B %d}".format(dt) }}
{%- if relative_days and delta < 0 %} ({{ delta * -1 }} days ago)
{%- elif relative_days and delta > 0 %} (in {{ delta }} days)
{%- endif %}
{%- endmacro %}

{% macro icon(tag) -%}
{%- if tag == "S" -%}
🍵
{%- elif tag == "H" -%}
🍔
{%- elif tag == "B" -%}
🍟
{%- elif tag == "N" -%}
🍨
{%- else -%}
❓
{%- endif -%}
{%- endmacro %}
