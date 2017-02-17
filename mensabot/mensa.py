import csv
import re
import warnings
from datetime import datetime, time

import requests
from bs4 import BeautifulSoup

MENU_URL = "http://www.stwno.de/infomax/daten-extern/csv/UNI-P/"
MENU_TYPES = ["S", "H", "B", "N"]
MENU_TYPE_ICONS = {
    "S": "🍵",
    "H": "🍔",
    "B": "🍟",
    "N": "🍨"
}


def get_menu_week(week, icons=MENU_TYPE_ICONS):
    r = requests.get("%s%s.csv" % (MENU_URL, week))
    if not r.ok:
        r = requests.get("%s%02s.csv" % (MENU_URL, week))
    r.raise_for_status()
    for row in csv.DictReader(r.text.splitlines(), delimiter=';'):
        row['datum'] = datetime.strptime(row['datum'], "%d.%m.%Y").date()
        name = re.split("\(", row['name'], 1)
        row['name'] = name[0].strip()
        row['zusatz'] = name[1].rstrip(")").strip() if len(name) > 1 else ""
        row['tags'] = "/".join([row['kennz'], row['zusatz']])
        row['icon'] = icons[row["warengruppe"][0]]
        del row['tag']
        del row['preis']
        yield row


def get_menu_day(dt=datetime.now(), icons=MENU_TYPE_ICONS):
    return sorted([d for d in get_menu_week(dt.date().isocalendar()[1], icons) if d['datum'] == dt.date()],
                  key=lambda d: (MENU_TYPES.index(d["warengruppe"][0]), d["warengruppe"]))


OPENING_URL = "https://stwno.de/de/gastronomie/"
OPENING_DAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
OPENING_TIMEFRAME_HOLIDAY = {"vorlesungszeit": False, "vorlesungsfreie zeit": True}
NOT_OPEN = (time(0, 0),) * 2


def get_opening_times(loc):
    # TODO list possible URLs
    r = requests.get(OPENING_URL + loc)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find("h3", string=re.compile("^Öffnungszeiten")).find_next_sibling("table")

    dates = {(t, d): NOT_OPEN for d in range(7) for t in [True, False]}

    timeframe = None
    for row in table.find_all("tr"):
        cols = row.find_all("td")
        if not len(cols) == 3:
            warnings.warn("Skipping row with unknown format '{}'".format(row))
            continue

        timeframe = cols[0].text.lower().strip().strip(":") or timeframe
        if timeframe not in OPENING_TIMEFRAME_HOLIDAY:
            warnings.warn("Skipping row with unknown timeframe '{}'".format(timeframe))
            continue
        holidays = OPENING_TIMEFRAME_HOLIDAY[timeframe]

        days = cols[1].text.strip()
        days_match = re.match("({days}) ?- ?({days})".format(days="|".join(OPENING_DAYS)), days)
        if days_match:
            first, last = OPENING_DAYS.index(days_match.group(1)), OPENING_DAYS.index(days_match.group(2))
            days = [i for i in range(first, last + 1)]
        elif not days:
            days = list(range(len(OPENING_DAYS)))
        elif days in OPENING_DAYS:
            days = [OPENING_DAYS.index(days)]
        else:
            warnings.warn("Could not parse day range '{}'".format(days))
            continue

        time_str = cols[2].text.strip()
        time_match = re.match("([0-9]{1,2}):([0-9]{1,2}) ?- ?([0-9]{1,2}):([0-9]{1,2}) ?(Uhr)?", time_str)
        if time_match:
            open_h, open_min, close_h, close_min = (int(time_match.group(i)) for i in range(1, 5))
        elif "geschlossen" in time_str:
            open_h, open_min, close_h, close_min = (0,) * 4
        else:
            warnings.warn("Could not parse time range '{}'".format(time_str))
            continue
        open = time(open_h, open_min)
        close = time(close_h, close_min)

        for day in days:
            dates[(holidays, day)] = (open, close)

    return dates


DATES_URL = "http://www.uni-passau.de/studium/waehrend-des-studiums/semesterterminplan/"
DATES_HOLIDAY = {"Vorlesungsbeginn": True, "Vorlesungsende": False}


def is_holiday(dt=datetime.now()):
    # TODO use http://www.uni-passau.de/studium/waehrend-des-studiums/semesterterminplan/vorlesungszeiten/ instead
    r = requests.get(DATES_URL)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    dates = [(elem.text, datetime.strptime(elem.find_previous_sibling("td").text, "%d.%m.%Y").date()) for elem in
             soup.find_all("td", text=re.compile("^Vorlesungs(beginn|ende)"))]
    dates.sort(key=lambda e: e[1])
    next_date = next((t, d) for t, d in dates if d >= dt.date())
    is_holiday = DATES_HOLIDAY[next_date[0]]
    return is_holiday
