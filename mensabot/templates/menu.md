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

{% for dish in menu %}{# use menu|kennz("V,F") or menu|zusatz_not("G") to filter #}
{{ icon(dish.warengruppe[0]) }} {{ dish.name }}
`>{{ "%7s" |format(dish.kennz.keys()|join(",")) }} {{ "%1.2f€"|format(dish.stud) }} {{ dish.zusatz.keys()|join(",") }}`
{% else %}
No menu available!
{% endfor %}
{% if menu|ketchup()|list() %}

🍅 Take ketchup for {% for dish in menu|ketchup() %}{{ dish.name }}{% if not loop.last %}, {% endif %}{% endfor %}.
{% endif %}
