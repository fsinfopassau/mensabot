{% import 'de/utils.md' as utils %}
{% for dish in menu %}{# use menu|kennz("V,F") or menu|zusatz_not("G") to filter #}
{% if loop.first %}
    Speisekarte für Mittagsmensa {{ utils.date(day, now, locale) }}:

{% endif %}
{{ utils.icon_dish(dish.warengruppe[0]) }} *{{ dish.name }}*
        {{ "%1.2f€"|format(dish[price_category]) }} _{{ utils.icons_kennz(dish.kennz) }} {{ dish.zusatz.keys()|join(",") }}_
{% else %}
    Kein Speiseplan für {{ utils.date(day, now, locale) }} verfügbar!
{% endfor %}
{% if menu|ketchup()|list() %}

🍅 Ketchup für {% for dish in menu|ketchup() %}{{ dish.name }}{% if not loop.last %}, {% endif %}{% endfor %} mitnehmen.
{% endif %}
