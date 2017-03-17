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
Menu for lunch mensa {{ date }}:
{% for dish in menu %}
{{ icon(dish.warengruppe[0]) }} {{ dish.name }}
`>{{ "%7s" |format(dish.kennz) }} {{ dish.stud }}`
{% else %}
No menu available!
{% endfor %}
