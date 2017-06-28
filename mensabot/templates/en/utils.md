{% extends "utils.md" %}

{% macro date(dt, now, locale) -%}
{% set delta = (dt|ensure_date - now|ensure_date).days %}
{% set relative_days = false %}
{% if delta == 0 %}
today, {% elif delta == -1 %}
yesterday, {% elif delta == 1 %}
tomorrow, {% else %}
{% set relative_days = true %}
{% endif %}
{{ dt|format_date('full', locale) }}
{%- if relative_days and delta < 0 %} ({{ delta * -1 }} days ago)
{%- elif relative_days and delta > 0 %} (in {{ delta }} days)
{%- endif %}
{%- endmacro %}
