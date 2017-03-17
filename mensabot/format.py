from datetime import timedelta

import humanize

from mensabot.mensa import *

LANG = ['de', 'en']
humanize.i18n.activate(LANG[0])

DATEPARSER_SETTINGS = {'PREFER_DATES_FROM': 'future'}

MENU_FORMAT = "{icon} {name}\n`>{kennz:>7} {stud}`"
MENU_HEADER = {
    'de': "Speiseplan für Mittagsmensa {1}({0:%a})",
    'en': "Menu for lunch mensa {}"
}
MENU_TYPE_ICONS = {
    "S": "🍵",
    "H": "🍔",
    "B": "🍟",
    "N": "🍨"
}


def get_mensa_formatted(dt):
    date = MENU_HEADER[LANG[0]].format(dt, humanize.naturalday(dt))
    menu = get_menu_day(dt)
    if menu:
        return date + "\nNo menu available!"
    else:
        return date + "\n" + "\n".join(
        MENU_FORMAT.format(icon=MENU_TYPE_ICONS[dish["warengruppe"][0]], **dish) for dish in menu)


def get_open_formatted(loc, dt):
    is_open = "closed in this timeframe"
    times = get_opening_times(loc)
    days = [(i, dt + timedelta(days=i)) for i in range(6)]
    for open, close, offset, day in (times[(is_holiday(d), d.isoweekday() - 1)] + (i, d) for i, d in days):
        # print("{} {:%a %Y-%m-%d} {:%H:%M} {:%H:%M}".format(offset, day, open, close))
        if offset == 0:
            if open < dt.time() < close:
                is_open = "open until {}".format(close)
                break
            elif dt.time() < open:
                is_open = "closed, but opens at {}".format(open)
                break
            else:
                pass  # closed for today, search for the next open date
        elif open > time(0, 0):
            is_open = "closed, opens in {} days at {}".format(offset, open)
            break
        else:
            pass  # continue searching for the next open date

    weekdays = [dt + timedelta(days=i - dt.weekday()) for i in range(7)]
    schedule = []
    for day in weekdays:
        open = times[(is_holiday(day), day.isoweekday() - 1)]
        schedule.append("{:%a} ".format(day) + ("closed" if open == NOT_OPEN else "{:%H:%M} - {:%H:%M}".format(*open)))

    s = "Cafete {} {}.```\n{}```".format(loc, is_open, "\n".join(schedule))
    print(s)
    return s
