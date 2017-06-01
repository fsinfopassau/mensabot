{% import 'de/utils.md' as utils -%}

{%- set list %}
{% for dish in diff %}{% if dish.diff|length != 1 or "warengruppe" not in dish.diff %}
{% if "name" in dish.diff %}
{{ utils.icon_dish(dish.from_dish.warengruppe[0]) }} {{ dish.diff["name"][0] }}
➡️ *{{ dish.diff["name"][1] }}*
{% elif not dish.from_dish %}
{{ utils.icon_dish(dish.to_dish.warengruppe[0]) }}🆕 *{{ dish.to_dish.name }}*
    Preis: {{ "%1.2f€"|format(dish.to_dish[price_category]) }}
    Kennz: {{ utils.icons_kennz(dish.diff["kennz"][1]) }}
    Zusatz: {{ dish.diff["zusatz"][1]|join(",") }}
{% elif not dish.to_dish %}
{{ utils.icon_dish(dish.from_dish.warengruppe[0]) }}❎ *{{ dish.from_dish.name }}*
{% else %}
{{ utils.icon_dish(dish.from_dish.warengruppe[0]) }} {{ dish.from_dish.name }}
{% endif -%}

{%- if price_category in dish.diff %}
    Preis: {{ "%1.2f€"|format(dish.from_dish[price_category]) }} ➡️ *{{ "%1.2f€"|format(dish.to_dish[price_category]) }}*
{% endif %}
{% if "kennz" in dish.diff %}
    Kennz: {{ utils.icons_kennz(dish.diff["kennz"][0]) }} ➡️ {{ utils.icons_kennz(dish.diff["kennz"][1]) }}
{% endif %}
{% if "zusatz" in dish.diff %}
    Zusatz: {{ dish.diff["zusatz"][0]|join(",") }} ➡️ *{{ dish.diff["zusatz"][1]|join(",") }}*
{% endif %}
{% endif %}{% endfor %}
{% endset -%}

{%- if list %}
Speisekarte für Mittagsmensa {{ utils.date(date, now, locale) }} wurde geändert:
{{ list }}
{% endif %}
