import datetime as dtm
import importlib
import sys
import warnings
from typing import List, Optional, Tuple, Union

from stwno_api import Institution
from stwno_api.institution import Location

data_module = importlib.import_module("data")
if "STWNO_ENABLED" not in data_module.__dict__:
    sys.modules["data"] = importlib.import_module("stwno_cmds.translations.dateparser")
    warnings.warn("stwno-cmd requires a modified version of dateparse's \"data\" package, so replacing the currently "
                  "loaded data package (from %s) with the stwno-cmd one (from %s)" %
                  (data_module.__file__, sys.modules["data"].__file__))
    assert "STWNO_ENABLED" in sys.modules["data"].__dict__, "stwno-cmd \"data\" package could not be loaded"

LANG = ['de', 'en']
from dateparser import DateDataParser

parser = DateDataParser(languages=LANG)


def parse_location_date(institution: Institution, tokens: List[str]) \
        -> Tuple[Optional[Location], Optional[dtm.datetime]]:
    if len(tokens) == 1 and isinstance(tokens[0], str) and tokens[0].count(" ") > 0:
        tokens = tokens[0].split(" ")

    if not tokens:
        return None, None

    # check whether location is first word
    loc = parse_location(institution, tokens[0])
    if loc:
        return loc, parse_date(tokens[1:])
    # or last word
    if len(tokens) > 1:
        loc = parse_location(institution, tokens[-1])
        if loc:
            return loc, parse_date(tokens[:-1])
    # otherwise, it's probably only a date
    return None, parse_date(tokens)


def parse_location(institution: Institution, s: Union[str, List[str]]) -> Optional[Location]:
    if not s or s == ['']:
        return None
    if not isinstance(s, str):
        s = " ".join(s)
    s = s.lower()
    return institution.find_location(s.lower())


def parse_date(s: Union[str, List[str]]) -> Optional[dtm.datetime]:
    if not s or s == ['']:
        return None
    if not isinstance(s, str):
        s = " ".join(s)
    if s.startswith("+"):
        s = "in " + s[1:]
    if s.startswith("-"):
        s = "vor " + s[1:]

    v = parser.get_date_data(s)
    if not v or not v['date_obj']:
        raise ValueError("Could not parse date '%s'" % s)
    return v['date_obj']
