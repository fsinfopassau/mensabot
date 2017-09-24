import datetime as dtm
import re
from abc import ABC, abstractmethod
from enum import Enum
from pprint import pformat
from typing import Callable, List, NamedTuple, Optional, Tuple, Union

import requests

__all__ = ["Institution", "Semester", "Location", "LocationType"]

Semester = NamedTuple("Semester", [("name", str),
                                   ("is_winter", bool),
                                   ("start", dtm.date), ("end", dtm.date),
                                   ("holidays", List[Tuple[dtm.date, dtm.date]])])


class LocationType(Enum):
    CAFETERIA = 1
    MENSA = 2


CompiledPattern = type(re.compile(''))


# TODO Location <-> Institution connection

class Location(NamedTuple("Location", [("name", str),
                                       ("type", LocationType),
                                       ("url", str),
                                       ("menu_url", str),
                                       ("aliases", List[Union[str, CompiledPattern, Callable]])])
               ):
    def __hash__(self):
        return hash(self.name)


class Institution(ABC):
    def __init__(self, name: str, id: str):
        self._name = name
        self._id = id
        self._location_patterns = {loc: self.parse_aliases(loc.aliases) for loc in self.locations}

    def parse_aliases(self, patterns: List[Union[str, CompiledPattern, Callable]]):
        if patterns is None:
            return []
        if not isinstance(patterns, list):
            patterns = [patterns]

        compile_flags = re.IGNORECASE
        compiled_pattern_list = []
        for idx, p in enumerate(patterns):
            if isinstance(p, str):
                compiled_pattern_list.append(re.compile(p, compile_flags).fullmatch)
            elif isinstance(p, CompiledPattern):
                compiled_pattern_list.append(p.fullmatch)
            elif callable(p):
                compiled_pattern_list.append(p)
            else:
                raise ValueError("Alias #%d: '%s' can't be converted to a string matcher" % (idx, p))
        return compiled_pattern_list

    @property
    def name(self) -> str:
        return self._name

    @property
    def id(self) -> str:
        return self._id

    def _session(self):
        return requests.Session()

    @property
    @abstractmethod
    def default_mensa(self) -> Location:
        ...

    @property
    @abstractmethod
    def default_cafeteria(self) -> Location:
        ...

    @property
    @abstractmethod
    def locations(self) -> List[Location]:
        # FIXME
        """
        A dict with the ids (URL fragments) of all mensas and cafeterias at this institution, i.e. all valid values to
        be used for the location parameter, as keys. Values are possible aliases for the locations.
        """
        ...

    def find_location(self, name: str) -> Optional[Location]:
        """
        Check if the given name matches any of the aliases of the locations at this institution.
        """
        for loc, matchers in self._location_patterns.items():
            if name == loc.name:
                return loc
            for matcher in matchers:
                if matcher(name):
                    return loc
        return None

    @abstractmethod
    def _get_semester_dates(self) -> List[Semester]:
        """
        A list of the start and end dates of semesters coming and past, including the ranges of dates which
        have no lectures according to the website.
        """
        ...

    def __get_semester_dates(self) -> List[Semester]:
        return self._get_semester_dates()

    semester_dates = property(__get_semester_dates)

    def is_holiday(self, dt: dtm.datetime = None) -> bool:
        """
        Check whether a certain date is during the holidays, the so called "vorlesungsfreie Zeit".
        """

        dt = dt.date() or dtm.date.today()
        semester_dates = self.semester_dates
        current_semester = next((sem for sem in reversed(semester_dates) if sem.start <= dt), None)
        assert current_semester, "Could not find semester for date %s, available semesters are:\n%s" \
                                 % (dt, pformat(semester_dates))
        return current_semester.end < dt or any(start <= dt <= end for start, end in current_semester.holidays)
