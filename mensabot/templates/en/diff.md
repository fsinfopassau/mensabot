{% import 'de/utils.md' as utils %}
{% set print_header=True %}
{% for dish in diff %}
{% if dish.diff|length != 1 or "warengruppe" not in dish.diff %}
{% if print_header %}
Menu for lunch mensa {{ utils.date(date, now, locale) }} changed:
{% set print_header=False %}
{% endif %}
{% if "name" in dish.diff %}
- {{ dish.diff["name"][0] }} ➡️ *{{ dish.diff["name"][1] }}*
    Price: {{ "%1.2f€"|format(dish.to_dish[price_category]) }}
    Labels: {{ dish.diff["kennz"][1]|join(",") }}
    Additives: {{ dish.diff["zusatz"][1]|join(",") }}
{% elif not dish.from_dish %}
- 🆕 *{{ dish.to_dish.name }}*
{% elif not dish.to_dish %}
- ❎ *{{ dish.from_dish.name }}*
{% else %}
- {{ dish.from_dish.name }}
{% endif %}
{% if price_category in dish.diff %}
    Price: {{ "%1.2f€"|format(dish.from_dish[price_category]) }} ➡️ *{{ "%1.2f€"|format(dish.to_dish[price_category]) }}*
{% endif %}
{% if "kennz" in dish.diff %}
    Labels: {{ dish.diff["kennz"][0]|join(",") }} ➡️ *{{ dish.diff["kennz"][1]|join(",") }}*
{% endif %}
{% if "zusatz" in dish.diff %}
    Additives: {{ dish.diff["zusatz"][0]|join(",") }} ➡️ *{{ dish.diff["zusatz"][1]|join(",") }}*
{% endif %}
{% endif %}
{% endfor %}
