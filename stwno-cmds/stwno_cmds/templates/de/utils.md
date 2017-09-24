{% extends "utils.md" %}

{% macro date(dt, now, locale) -%}
{% set delta = (dt|ensure_date - now|ensure_date).days %}
{% set relative_days = false %}
{% if delta == 0 %}
heute, {% elif delta == -1 %}
gestern, {% elif delta == -2 %}
vorgestern, {% elif delta == 1 %}
morgen, {% elif delta == 2 %}
übermorgen, {% else %}
{% set relative_days = true %}
{% endif %}
{{ dt|format_date('full', locale) }}
{%- if relative_days and delta < 0 %} (vor {{ delta * -1 }} Tagen)
{%- elif relative_days and delta > 0 %} (in {{ delta }} Tagen)
{%- endif %}
{%- endmacro %}
