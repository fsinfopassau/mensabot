{% import 'de/utils.md' as utils %}
Speisekarte {{ utils.date(date, now, locale) }} geändert:
{% for dish in diff %}
{% if "name" in dish.diff %}
- {{ dish.diff["name"][0] }} ➡️ *{{ dish.diff["name"][1] }}*
{% elif not dish.from_dish %}
- 🆕 *{{ dish.to_dish.name }}*
    Preis: {{ "%1.2f€"|format(dish.to_dish[price_category]) }}
{% elif not dish.to_dish %}
- ❎ *{{ dish.from_dish.name }}*
{% elif price_category in dish.diff %}
- {{ dish.from_dish.name }}
{% endif %}
{% if price_category in dish.diff %}
    Preis: {{ "%1.2f€"|format(dish.from_dish[price_category]) }} ➡️ *{{ "%1.2f€"|format(dish.to_dish[price_category]) }}*
{% endif %}
{% endfor %}
