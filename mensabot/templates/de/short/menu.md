{% import 'de/utils.md' as utils %}
{% for dish in menu | warengruppe("H") %}{# use menu|kennz("V,F") or menu|zusatz_not("G") to filter #}
    {% if loop.first %}
        Speisekarte für Mittagsmensa {{ utils.date(date, now, locale) }}:

    {% endif %}
    {{ utils.icon_dish(dish.warengruppe[0]) }} *{{ dish.name }}*
    {{ "%1.2f€"|format(dish[price_category]) }} _{{ utils.icons_kennz(dish.kennz) }} {{ dish.zusatz.keys()|join(",") }}_
{% else %}
    Kein Speiseplan für {{ utils.date(date, now, locale) }} verfügbar!
{% endfor %}

{% for dish in menu | warengruppe_not("H") %}
    {% if not "salat" in dish.name.lower() %}
        {{ utils.icon_dish(dish.warengruppe[0]) }} *{{ dish.name }}* {{ utils.icons_kennz(dish.kennz) }}
    {% endif %}
{% endfor %}
{% if menu|ketchup()|list() %}

    🍅 Ketchup mitnehmen.
{% endif %}
