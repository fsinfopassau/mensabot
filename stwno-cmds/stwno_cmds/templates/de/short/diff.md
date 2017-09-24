{% import 'de/utils.md' as utils %}
{% for dish in diff %}
{% if "name" in dish.diff %}
{{ utils.icon_dish(dish.from_dish.warengruppe[0]) }} {{ dish.diff["name"][0] }}
➡️ *{{ dish.diff["name"][1] }}*
{% elif not dish.from_dish %}
{{ utils.icon_dish(dish.to_dish.warengruppe[0]) }}🆕 *{{ dish.to_dish.name }}*
    Preis: {{ "%1.2f€"|format(dish.to_dish[price_category]) }}
{% elif not dish.to_dish %}
{{ utils.icon_dish(dish.from_dish.warengruppe[0]) }}❎ *{{ dish.from_dish.name }}*
{% elif price_category in dish.diff %}
{{ utils.icon_dish(dish.from_dish.warengruppe[0]) }} {{ dish.from_dish.name }}
{% endif %}
{% if price_category in dish.diff %}
    Preis: {{ "%1.2f€"|format(dish.from_dish[price_category]) }} ➡️ *{{ "%1.2f€"|format(dish.to_dish[price_category]) }}*
{% endif %}
{% endfor %}
