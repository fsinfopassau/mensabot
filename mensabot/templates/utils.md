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
