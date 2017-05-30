{% import 'de/utils.md' as utils %}
{% set print_header=True %}
{% for dish in diff %}
{% if dish.diff|length != 1 or "warengruppe" not in dish.diff %}
{% if print_header %}
Speisekarte für Mittagsmensa {{ utils.date(date, now, locale) }} wurde geändert:
{% set print_header=False %}
{% endif %}
{% if "name" in dish.diff %}
- {{ dish.diff["name"][0] }} ➡️ *{{ dish.diff["name"][1] }}*
{% elif not dish.from_dish %}
- 🆕 *{{ dish.to_dish.name }}*
    Preis: {{ "%1.2f€"|format(dish.to_dish[price_category]) }}
    Kennz: {{ dish.diff["kennz"][1]|join(",") }}
    Zusatz: {{ dish.diff["zusatz"][1]|join(",") }}
{% elif not dish.to_dish %}
- ❎ *{{ dish.from_dish.name }}*
{% else %}
- {{ dish.from_dish.name }}
{% endif %}
{% if price_category in dish.diff %}
    Preis: {{ "%1.2f€"|format(dish.from_dish[price_category]) }} ➡️ *{{ "%1.2f€"|format(dish.to_dish[price_category]) }}*
{% endif %}
{% if "kennz" in dish.diff %}
    Kennz: {{ dish.diff["kennz"][0]|join(",") }} ➡️ *{{ dish.diff["kennz"][1]|join(",") }}*
{% endif %}
{% if "zusatz" in dish.diff %}
    Zusatz: {{ dish.diff["zusatz"][0]|join(",") }} ➡️ *{{ dish.diff["zusatz"][1]|join(",") }}*
{% endif %}
{% endif %}
{% endfor %}
