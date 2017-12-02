{% import 'en/utils.md' as utils -%}

{%- set list %}
{% for dish in diff %}{% if dish.diff|length != 1 or "warengruppe" not in dish.diff %}
{% if "name" in dish.diff %}
{{ utils.icon_dish(dish.from_dish.warengruppe[0]) }} {{ dish.diff["name"][0] }}
➡️ *{{ dish.diff["name"][1] }}*
{% elif not dish.from_dish %}
{{ utils.icon_dish(dish.to_dish.warengruppe[0]) }}🆕 *{{ dish.to_dish.name }}*
    Price: {{ "%1.2f€"|format(dish.to_dish[price_category]) }}
    Labels: {{ utils.icons_kennz(dish.to_dish.kennz) }}
    Additives: {{ dish.to_dish.zusatz|join(",") }}
{% elif not dish.to_dish %}
{{ utils.icon_dish(dish.from_dish.warengruppe[0]) }}❎ *{{ dish.from_dish.name }}*
{% else %}
{{ utils.icon_dish(dish.from_dish.warengruppe[0]) }} {{ dish.from_dish.name }}
{% endif -%}

{%- if price_category in dish.diff %}
    Price: {{ "%1.2f€"|format(dish.from_dish[price_category]) }} ➡️ *{{ "%1.2f€"|format(dish.to_dish[price_category]) }}*
{% endif %}
{% if "kennz" in dish.diff %}
    Labels: {{ utils.icons_kennz(dish.diff["kennz"][0]) }} ➡️ {{ utils.icons_kennz(dish.diff["kennz"][1]) }}
{% endif %}
{% if "zusatz" in dish.diff %}
    Additives: {{ dish.diff["zusatz"][0]|join(",") }} ➡️ *{{ dish.diff["zusatz"][1]|join(",") }}*
{% endif %}
{% endif %}{% endfor %}
{% endset -%}

{%- if list %}
    Menu for lunch mensa {{ utils.date(day, now, locale) }} changed:
{{ list }}
{% endif %}
