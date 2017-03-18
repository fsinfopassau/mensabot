{% import 'en/utils.md' as utils %}
{% for dish in menu %}{# use menu|kennz("V,F") or menu|zusatz_not("G") to filter #}
{% if loop.first %}
Menu for lunch mensa {{ utils.date(date, now, locale) }}:

{% endif %}
{{ utils.icon(dish.warengruppe[0]) }} {{ dish.name }}
`>{{ "%7s" |format(dish.kennz.keys()|join(",")) }} {{ "%1.2f€"|format(dish.stud) }} {{ dish.zusatz.keys()|join(",") }}`
{% else %}
No menu for {{ utils.date(date, now, locale) }} available!
{% endfor %}
{% if menu|ketchup()|list() %}

🍅 Take ketchup for {% for dish in menu|ketchup() %}{{ dish.name }}{% if not loop.last %}, {% endif %}{% endfor %}.
{% endif %}
