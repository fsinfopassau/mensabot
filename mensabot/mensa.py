import csv
import datetime as dtm
import functools
import logging
import os
import warnings
from collections import OrderedDict
from pprint import pformat
from typing import Dict, List, NamedTuple, Tuple

import regex as re
import requests
from bs4 import BeautifulSoup
from dateutil.easter import easter
from dateutil.relativedelta import TH, TU, relativedelta

from mensabot.bot.util import ensure_date
from mensabot.config_default import MENU_STORE
from mensabot.mensa_menu import dish, parse_dish

logger = logging.getLogger("mensabot.mensa")

MENU_URL = "http://www.stwno.de/infomax/daten-extern/csv/UNI-P/"
MENU_TYPES = ["S", "H", "B", "N"]

LOCATIONS = {
    "audimax": "cafeterien/cafeteria-uni-pa-audimax",
    "mensacafete": "cafeterien/cafeteria-uni-pa-mensagebaeude",
    "nikolakloster": "cafeterien/cafeteria-uni-pa-nikolakloster",
    "wiwi": "cafeterien/cafebar-uni-pa-wiwi",
    "mensaessen": "mensen/mensa-uni-passau"
}
PRICES_CATEGORIES = ["stud", "bed", "gast"]

cache = {}
change_listeners = []


def get_menu_week(week: int, disable_cache=False) -> List[dish]:
    """
    Get all dishes for a certain week from the stwno website.

    :param week: the iso number of the week
    :return: a list of dishes
    """

    if week in cache and not disable_cache:
        dt, list = cache[week]
        if dtm.datetime.now() - dt < dtm.timedelta(minutes=5):  # TODO make this configurable
            return list
    list = fetch_menu_week(week)
    cache[week] = (dtm.datetime.now(), list)
    return list


def fetch_menu_week(week: int) -> List[dish]:
    r = requests.get("%s%s.csv" % (MENU_URL, week))
    if not r.ok:
        r = requests.get("%s%02s.csv" % (MENU_URL, week))
    r.raise_for_status()
    text = r.text
    # fix ; appearing in Zusatz, e.g. (2,3,8,G,I,A;AA)
    text = re.sub("\([A-Z0-9,; ]+\)", lambda m: m.group().replace(";", ","), text)

    # Fix stray newlines. If a line does not start with a valid date, is it
    # probably actually part of the previous line.
    text = re.sub("\n(?![0-9]{2}\.[0-9]{2}\.[0-9]{4};)", " ", text)

    os.makedirs(MENU_STORE, exist_ok=True)
    with open("%s/%s.csv" % (MENU_STORE, week), "a+", encoding="iso8859_3") as f:
        f.seek(0)
        old = [parse_dish(row) for row in csv.DictReader(f.readlines(), delimiter=';') if row['datum'].strip()]
        new = [parse_dish(row) for row in csv.DictReader(text.splitlines(), delimiter=';') if row['datum'].strip()]

        if old == new:
            return old

        f.seek(0)
        f.truncate(0)
        f.writelines(text)

    logger.debug("Menu changed!")
    for l in change_listeners:
        l(week, old, new)
    return new


def get_menu_day(dt: dtm.date = None) -> List[dish]:
    """
    Get all dishes for a certain day from the stwno website, deduplicated and sorted by their type.

    :param dt: the date(-time)
    :return: a list of dishes
    """
    dt = ensure_date(dt or dtm.date.today())
    menu = [d for d in get_menu_week(dt.isocalendar()[1]) if d.datum == dt]
    menu = sorted(menu, key=lambda d: (MENU_TYPES.index(d.warengruppe[0]), d.warengruppe))
    menu = reversed(OrderedDict((dish.name, dish) for dish in reversed(menu)).values())
    return list(menu)


OPENING_URL = "https://stwno.de/de/gastronomie/"
OPENING_DAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
OPENING_TIMEFRAME_HOLIDAY = {"vorlesungszeit": False, "vorlesungsfreie zeit": True}
NOT_OPEN = (dtm.time(0, 0),) * 2


@functools.lru_cache(maxsize=16)
def get_opening_times(loc: str) -> Dict[Tuple[bool, int], Tuple[dtm.time, dtm.time]]:
    """
    Return the opening times for a certain location.

    :param loc: the location, indicated by it's URL part
    :return: a dict, mapping from the tuple (is during holidays, iso week day) to (opening time, closing time)
    """

    # This is a hack to keep the /mensa command working even though the opening times cannot be determined reliably.
    # TODO: Find a new reliable source for mensa opening times.
    if loc == "mensen/mensa-uni-passau":
      dates = {(t, d): NOT_OPEN for d in range(7) for t in [True, False]}
      for d in range(5):
        dates[(True, d)] = dates[(False, d)] = (dtm.time(11, 00), dtm.time(14, 15))
      return dates

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
        open = dtm.time(open_h, open_min)
        close = dtm.time(close_h, close_min)

        for day in days:
            dates[(holidays, day)] = (open, close)

    return dates


open_info = NamedTuple("open_info", [("open", dtm.time), ("close", dtm.time), ("day", dtm.datetime), ("offset", int)])


def get_next_open(dt: dtm.datetime, loc: str) -> open_info:
    """
    Check when the given location is open the next time.

    :return: An open_info with offset = 0 if the location is open today, otherwise open_info showing the next open date.
        If the location is not open in the foreseeable future, None is returned.
    """

    times = get_opening_times(loc)
    days = [(i, dt + dtm.timedelta(days=i)) for i in range(6)]
    for open, close, offset, day in (times[(is_holiday(d), d.isoweekday() - 1)] + (i, d) for i, d in days):
        # print("{} {:%a %Y-%m-%d} {:%H:%M} {:%H:%M}".format(offset, day, open, close))
        if offset == 0:
            if dt.time() < close:
                return open_info(open, close, day, offset)  # still open today
            else:
                pass  # closed for today, search for the next open date
        elif open > dtm.time(0, 0):
            return open_info(open, close, day, offset)  # found next open day
        else:
            pass  # continue searching for the next open date

    # FIXME this might happen in the vorlesungsfreie zeit
    raise AssertionError("Mensa '%s' not open in the foreseeable future after %s" % (loc, dt))


def get_next_mensa_open(dt: dtm.datetime = None, loc: str = "mensen/mensa-uni-passau") \
        -> (open_info, List[dish]):
    dt = dt or dtm.datetime.now()
    menu = None
    offset = 0
    while menu is None:
        next_open = get_next_open(dt, loc)
        offset += next_open.offset
        if offset > 31:
            raise AssertionError("Mensa '%s' has no menu in the foreseeable future after %s" % (loc, dt))
        open, close, day, _ = next_open
        menu = get_menu_day(day)
        dt = day + dtm.timedelta(days=1)
    return open_info(open, close, day, offset), menu


DATES_URL = "https://www.uni-passau.de/termine-fristen/vorlesungszeiten/"
semester = NamedTuple("semester", [("name", str), ("is_winter", bool), ("start", dtm.date), ("end", dtm.date),
                                   ("holidays", List[Tuple[dtm.date, dtm.date]])])


def is_holiday(dt: dtm.datetime = None) -> bool:
    """
    Check whether a certain date is during the holidays, the so called "vorlesungsfreie Zeit".
    """

    dt = dt.date() or dtm.date.today()
    semester_dates = get_semester_dates()
    current_semester = next((sem for sem in reversed(semester_dates) if sem.start <= dt), None)
    assert current_semester, "Could not find semester for date %s, available semesters are:\n%s" \
                             % (dt, pformat(semester_dates))
    return current_semester.end < dt or any(start <= dt <= end for start, end in current_semester.holidays)

def sanitize_semester_dates_table_heads(strings: List[str]) -> List[str]:
    strings = [x.replace('\xad', '').replace('\t', '').split(' ')[0] for x in strings]
    strings = [x for x in strings if x != '']
    return strings[0:4]

@functools.lru_cache(maxsize=1)
def get_semester_dates() -> List[semester]:
    """
    Get a list of the start and end dates of semesters coming and past, including the ranges of dates which
    have no lectures according to the website. So this does not include public holidays or weekends (where the
    university is closed completely).
    """

    r = requests.get(DATES_URL)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, 'html.parser')
    table = soup.find("div", class_="upa_main_content").find("table", class_="contenttable")
    assert sanitize_semester_dates_table_heads(list(table.find("thead").strings)) == ['Semester', 'Beginn', 'Ende',
                                                 'Verfügungstag']

    past_table = soup.find("div", class_="upa_main_content").find("div", class_="collapse").find("table", class_="contenttable")
    assert sanitize_semester_dates_table_heads(list(past_table.find("thead").strings)) == ['Semester', 'Beginn', 'Ende',
                                                      'Verfügungstag']

    semesters = []
    for semester_tr in table.find("tbody").find_all("tr") + past_table.find("tbody").find_all("tr"):
        name, *dates = [s for s in semester_tr.strings if s.strip() != '']
        try:
            dates = [dtm.datetime.strptime(d.replace('*', ''), "%d.%m.%Y").date() for d in dates]
        except ValueError as e:
            print(e)
            continue
        if len(dates) >= 3:
            start, end, bruecke = dates
            holidays = [(bruecke, bruecke)]
        else:
            start, end = dates
            holidays = []
        winter_sem = name.startswith("Winter")
        assert winter_sem == (start.year != end.year)

        if winter_sem:
            # 24. Dezember bis einschließlich 6. Januar
            holidays.append((dtm.date(start.year, 12, 24), dtm.date(end.year, 1, 6)))
        else:
            easter_date = easter(start.year)
            # Gründonnerstag bis einschließlich Dienstag nach Ostern
            holidays.append((easter_date + relativedelta(weekday=TH(-1)), easter_date + relativedelta(weekday=TU(+1))))
            # Dienstag nach Pfingsten
            holidays.append((easter_date + relativedelta(days=50), easter_date + relativedelta(days=51)))

        semesters.append(semester(name, winter_sem, start, end, holidays))

    semesters.sort(key=lambda e: e.start)
    return semesters


def clear_caches():
    logger.debug("Clearing caches...")
    for func in [get_opening_times, get_semester_dates]:
        logger.debug("Statistics for cache of {}: {}".format(func.__name__, func.cache_info()))
        func.cache_clear()
