import csv
import functools
import re
import warnings
from collections import Counter
from datetime import date, datetime, time, timedelta
from typing import Dict, List, NamedTuple, Tuple

import requests
from bs4 import BeautifulSoup

MENU_URL = "http://www.stwno.de/infomax/daten-extern/csv/UNI-P/"
MENU_TYPES = ["S", "H", "B", "N"]

dish = NamedTuple("dish", [
    ("datum", datetime),
    ("name", str),
    ("warengruppe", str),
    ("kennz", Counter),
    ("zusatz", Counter),
    ("stud", float),
    ("bed", float),
    ("gast", float)
])


@functools.lru_cache()
def get_menu_week(week: int) -> List[dish]:
    """
    Get all dishes for a certain week from the stwno website.

    :param week: the iso number of the week
    :return: a list of dishes
    """

    r = requests.get("%s%s.csv" % (MENU_URL, week))
    if not r.ok:
        r = requests.get("%s%02s.csv" % (MENU_URL, week))
    r.raise_for_status()
    dishes = []
    for row in csv.DictReader(r.text.splitlines(), delimiter=';'):
        row['datum'] = datetime.strptime(row['datum'], "%d.%m.%Y").date()
        name = re.split("\(", row['name'], 1)
        row['name'] = name[0].strip()
        row['kennz'] = Counter(row['kennz'].split(","))
        row['zusatz'] = Counter((name[1].rstrip(")").strip() if len(name) > 1 else "").split(","))
        # row['tags'] = "/".join([row['kennz'], row['zusatz']])
        row["stud"] = float(row["stud"].replace(",", "."))
        row["bed"] = float(row["bed"].replace(",", "."))
        row["gast"] = float(row["gast"].replace(",", "."))
        del row['tag']
        del row['preis']
        dishes.append(dish(**row))

    return dishes


def get_menu_day(dt: datetime = datetime.now()) -> List[dish]:
    """
    Get all dishes for a certain day from the stwno website, sorted by their type.

    :param dt: the date(-time)
    :return: a list of dishes
    """

    return sorted([d for d in get_menu_week(dt.date().isocalendar()[1]) if d.datum == dt.date()],
                  key=lambda d: (MENU_TYPES.index(d.warengruppe[0]), d.warengruppe))


OPENING_URL = "https://stwno.de/de/gastronomie/"
OPENING_DAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
OPENING_TIMEFRAME_HOLIDAY = {"vorlesungszeit": False, "vorlesungsfreie zeit": True}
LOCATIONS = {
    "audimax": "cafeterien/cafeteria-uni-pa-audimax",
    "mensacafete": "cafeterien/cafeteria-uni-pa-mensagebaeude",
    "nikolakloster": "cafeterien/cafeteria-uni-pa-nikolakloster",
    "wiwi": "cafeterien/cafebar-uni-pa-wiwi",
    "mensaessen": "mensen/mensa-uni-passau"
}
NOT_OPEN = (time(0, 0),) * 2


@functools.lru_cache(maxsize=16)
def get_opening_times(loc: str) -> Dict[Tuple[bool, int], Tuple[time, time]]:
    """
    Return the opening times for a certain location.

    :param loc: the location, indicated by it's URL part
    :return: a dict, mapping from the tuple (is during holidays, iso week day) to (opening time, closing time)
    """

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


open_info = NamedTuple("open_info", [("open", time), ("close", time), ("day", datetime), ("offset", int)])


def get_next_open(dt: datetime, loc: str) -> open_info:
    """
    Check when the given location is open the next time.

    :return: An open_info with offset = 0 if the location is open today, otherwise open_info showing the next open date.
        If the location is not open in the foreseeable future, None is returned.
    """

    times = get_opening_times(loc)
    days = [(i, dt + timedelta(days=i)) for i in range(6)]
    for open, close, offset, day in (times[(is_holiday(d), d.isoweekday() - 1)] + (i, d) for i, d in days):
        # print("{} {:%a %Y-%m-%d} {:%H:%M} {:%H:%M}".format(offset, day, open, close))
        if offset == 0:
            if dt.time() < close:
                return open_info(open, close, day, offset)  # still open today
            else:
                pass  # closed for today, search for the next open date
        elif open > time(0, 0):
            return open_info(open, close, day, offset)  # found next open day
        else:
            pass  # continue searching for the next open date

    return None  # not open in the foreseeable future


DATES_URL = "http://www.uni-passau.de/studium/waehrend-des-studiums/semesterterminplan/"
DATES_HOLIDAY = {"Vorlesungsbeginn": True, "Vorlesungsende": False}


def is_holiday(dt: datetime = datetime.now()) -> bool:
    """
    Check whether a certain date is during the holidays, the so called "vorlesungsfreie Zeit".
    """

    next_date = next((t, d) for t, d in get_semester_dates() if d >= dt.date())
    is_holiday = DATES_HOLIDAY[next_date[0]]
    return is_holiday


@functools.lru_cache(maxsize=1)
def get_semester_dates() -> List[Tuple[str, date]]:
    """
    Get a list of the dates of start and end of lecture as a list of Tuples with either
    "Vorlesungsbeginn" or "Vorlesungsende" and the respective date.
    """

    r = requests.get(DATES_URL)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    dates = [(elem.text, datetime.strptime(elem.find_previous_sibling("td").text, "%d.%m.%Y").date()) for elem in
             soup.find_all("td", text=re.compile("^Vorlesungs(beginn|ende)"))]
    dates.sort(key=lambda e: e[1])
    return dates
