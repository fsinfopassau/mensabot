import csv
import datetime as dtm
import functools
import logging
import os
import warnings
from collections import OrderedDict
from typing import Dict, List, NamedTuple, Optional, Tuple, Union

import regex as re
import requests
from bs4 import BeautifulSoup

from stwno_api.institution import Location
from stwno_api.menu_parser import Dish, parse_dish
from stwno_api.util import ensure_date

__all__ = ["NOT_OPEN", "OpenInfo", "StwnoApi", "CachedStwnoApi", "StoringStwnoApi"]

NOT_OPEN = (dtm.time(0, 0),) * 2
OpenInfo = NamedTuple("OpenInfo", [("open", dtm.time), ("close", dtm.time), ("day", dtm.datetime), ("offset", int)])


class StwnoApi(object):
    MENU_URL = "http://www.stwno.de/infomax/daten-extern/csv/%s/%s.csv"
    MENU_URL2 = "http://www.stwno.de/infomax/daten-extern/csv/%s/%s.csv"
    MENU_TYPES = ["S", "H", "B", "N"]
    PRICES_CATEGORIES = ["stud", "bed", "gast"]

    OPENING_TIMES_URL = "https://stwno.de/de/gastronomie/%s"
    OPENING_DAYS = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]
    OPENING_TIMEFRAME_HOLIDAY = {"vorlesungszeit": False, "vorlesungsfreie zeit": True}

    def __init__(self, institution):
        self._institution = institution
        institution._session = lambda: self._session()

    @property
    def institution(self):
        return self._institution

    def _session(self):
        return requests.Session()

    # Mensa menu

    def get_menu_of_week(self, week: int, location: Location = None) -> List[Dish]:
        location = location or self.institution.default_mensa
        assert location in self.institution.locations
        r = self._session().get(self.MENU_URL % (location.menu_url, week))
        if not r.ok:
            r = self._session().get(self.MENU_URL2 % (location.menu_url, week))
        r.raise_for_status()
        text = r.text
        # fix ; appearing in Zusatz, e.g. (2,3,8,G,I,A;AA)
        text = re.sub("\([A-Z0-9,; ]+\)", lambda m: m.group().replace(";", ","), text)

        return [parse_dish(row) for row in csv.DictReader(text.splitlines(), delimiter=';')]

    def get_menu_of_day(self, day: Union[dtm.datetime, dtm.date, str] = None, location: Location = None) -> List[Dish]:
        """
        Get all dishes for a certain day from the stwno website, deduplicated and sorted by their type.

        :param day: the date(-time)
        :return: a list of dishes
        """
        day = ensure_date(day or dtm.date.today())
        menu = [d for d in self.get_menu_of_week(day.isocalendar()[1], location) if d.datum == day]
        menu = sorted(menu, key=lambda d: (self.MENU_TYPES.index(d.warengruppe[0]), d.warengruppe))
        menu = reversed(OrderedDict((dish.name, dish) for dish in reversed(menu)).values())
        return list(menu)

    # Opening times

    def get_opening_times(self, location: Location = None) -> Dict[Tuple[bool, int], Tuple[dtm.time, dtm.time]]:
        """
        Return the opening times for a certain location.

        :param location: the location, indicated by it's URL part
        :return: a dict, mapping from the tuple (is during holidays, iso week day) to (opening time, closing time)
        """
        location = location or self.institution.default_cafeteria
        assert location in self.institution.locations
        r = self._session().get(self.OPENING_TIMES_URL % location.url)
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
            if timeframe not in self.OPENING_TIMEFRAME_HOLIDAY:
                warnings.warn("Skipping row with unknown timeframe '{}'".format(timeframe))
                continue
            holidays = self.OPENING_TIMEFRAME_HOLIDAY[timeframe]

            days = cols[1].text.strip()
            days_match = re.match("({days}) ?- ?({days})".format(days="|".join(self.OPENING_DAYS)), days)
            if days_match:
                first, last = self.OPENING_DAYS.index(days_match.group(1)), self.OPENING_DAYS.index(days_match.group(2))
                days = [i for i in range(first, last + 1)]
            elif not days:
                days = list(range(len(self.OPENING_DAYS)))
            elif days in self.OPENING_DAYS:
                days = [self.OPENING_DAYS.index(days)]
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

    def get_next_open(self, location: Location = None, starting_from: dtm.datetime = None) -> Optional[OpenInfo]:
        """
        Check when the given location is open the next time.

        :return: An OpenInfo with offset = 0 if the location is open today, otherwise OpenInfo showing the next open date.
            If the location is not open in the foreseeable future, None is returned.
        """

        location = location or self.institution.default_cafeteria
        times = self.get_opening_times(location)
        starting_from = starting_from or dtm.datetime.now()
        days = [(i, starting_from + dtm.timedelta(days=i)) for i in range(6)]
        for open, close, offset, day in (times[(self.institution.is_holiday(d), d.isoweekday() - 1)] + (i, d)
                                         for i, d in days):
            # print("{} {:%a %Y-%m-%d} {:%H:%M} {:%H:%M}".format(offset, day, open, close))
            if offset == 0:
                if starting_from.time() < close:
                    return OpenInfo(open, close, day, offset)  # still open today
                else:
                    pass  # closed for today, search for the next open date
            elif open > dtm.time(0, 0):
                return OpenInfo(open, close, day, offset)  # found next open day
            else:
                pass  # continue searching for the next open date

        warnings.warn("Location '%s' not open in the foreseeable future after %s" % (location, starting_from))
        return None

    def get_next_mensa_open(self, location: Location = None, starting_from: dtm.datetime = None) \
            -> Optional[Tuple[OpenInfo, List[Dish]]]:
        """
        Check when the given mensa is open and offers dishes the next time.

        :return: An tupel with the first value being and OpenInfo with offset = 0 if the location is open today,
        otherwise an OpenInfo showing the next open date. The second value is the menu for the found day. If the
        location is not open in the foreseeable future, None is returned.
        """

        location = location or self.institution.default_mensa
        starting_from = starting_from or dtm.datetime.now()
        menu = None
        offset = 0
        while menu is None:
            next_open = self.get_next_open(location, starting_from)
            if not next_open:
                return None
            offset += next_open.offset
            if offset > 31:
                warnings.warn("Mensa '%s' has no menu in the foreseeable future after %s" % (location, starting_from))
                return None
            open, close, day, _ = next_open
            menu = self.get_menu_of_day(day)
            starting_from = day + dtm.timedelta(days=1)
        # noinspection PyUnboundLocalVariable
        return OpenInfo(open, close, day, offset), menu


class CachedStwnoApi(StwnoApi):
    logger = logging.getLogger("stwno_api.CachedStwnoApi")

    def __init__(self, institution):
        institution._get_semester_dates = functools.lru_cache()(institution._get_semester_dates)
        super().__init__(institution)
        self._caches = [self._session, self.get_opening_times, self.get_menu_of_week,
                        self._session]

    @functools.lru_cache()
    def _session(self):
        return super()._session()

    @functools.lru_cache()
    def get_opening_times(self, location: Location = None) -> Dict[Tuple[bool, int], Tuple[dtm.time, dtm.time]]:
        return super().get_opening_times(location)

    @functools.lru_cache(maxsize=16)
    def get_menu_of_week(self, week: int, location: Location = None) -> List[Dish]:
        return super().get_menu_of_week(week, location)

    # TODO implement TTL in lru_cache
    # self.cache = {}
    # self.cache_ttl = cache_ttl
    #
    # def get_menu_of_week(self, week: int, location: Location = None, disable_cache: bool = False):
    #     if week in self.cache and not disable_cache:
    #         dt, list = self.cache[week]
    #         if dtm.datetime.now() - dt < dtm.timedelta(minutes=self.cache_ttl):  # TODO make this configurable
    #             return list
    #     list = super().get_menu_of_week(week, location)
    #     self.cache[week] = (dtm.datetime.now(), list)
    #     return list

    # noinspection PyUnresolvedReferences
    def clear_cache(self):
        for func in self._caches:
            self.logger.debug("Statistics for cache of {}: {}".format(func.__name__, func.cache_info()))
            func.cache_clear()


class StoringStwnoApi(StwnoApi):
    logger = logging.getLogger("stwno_api.StoringStwnoApi")

    def __init__(self, institution, store_dir):
        self.store_dir = store_dir
        self.change_listeners = []
        super().__init__(institution)

    def get_menu_of_week(self, week: int, location: Location = None) -> List[Dish]:
        new = super().get_menu_of_week(week, location)

        os.makedirs(self.store_dir, exist_ok=True)
        with open("%s/%s.csv" % (self.store_dir, week), "a+", encoding="iso8859_3") as f:
            f.seek(0)

            old = [parse_dish(row) for row in csv.DictReader(f.readlines(), delimiter=';')]
            if old == new:
                return old

            f.seek(0)
            f.truncate(0)
            f.writelines(new)

        self.logger.debug("Menu changed!")
        for l in self.change_listeners:
            l(week, old, new)
        return new
