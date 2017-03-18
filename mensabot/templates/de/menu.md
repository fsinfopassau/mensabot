{% import 'de/utils.md' as utils %}
{% for dish in menu %}{# use menu|kennz("V,F") or menu|zusatz_not("G") to filter #}
{% if loop.first %}
Speisekarte für Mittagsmensa {{ utils.date(date, now, locale) }}:

{% endif %}
{{ utils.icon(dish.warengruppe[0]) }} {{ dish.name }}
`>{{ "%7s" |format(dish.kennz.keys()|join(",")) }} {{ "%1.2f€"|format(dish.stud) }} {{ dish.zusatz.keys()|join(",") }}`
{% else %}
Kein Speiseplan für {{ utils.date(date, now, locale) }} verfügbar!
{% endfor %}
{% if menu|ketchup()|list() %}

🍅 Ketchup für {% for dish in menu|ketchup() %}{{ dish.name }}{% if not loop.last %}, {% endif %}{% endfor %} mitnehmen.
{% endif %}
