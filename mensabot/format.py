import random

import dateparser
from babel.dates import format_date, format_time
from jinja2 import PackageLoader
from jinja2.sandbox import SandboxedEnvironment

from mensabot.mensa import *

LANG = ['de', 'en']
DATEPARSER_SETTINGS = {'PREFER_DATES_FROM': 'future'}

JINJA2_ENV = SandboxedEnvironment(
    loader=PackageLoader('mensabot', 'templates'),
    trim_blocks=True, lstrip_blocks=True, auto_reload=True
)

KETCHUP = ["kartoffel", "potato", "pommes", "twister", "kroketten", "rösti", "schnitzel", "cordon"]

LOCATIONS = {
    "audimax": "cafeterien/cafeteria-uni-pa-audimax",
    "mensacafete": "cafeterien/cafeteria-uni-pa-mensagebaeude",
    "nikolakloster": "cafeterien/cafeteria-uni-pa-nikolakloster",
    "wiwi": "cafeterien/cafebar-uni-pa-wiwi",
    "mensaessen": "mensen/mensa-uni-passau"
}


def filter_kennz(list: List[dish], kennz):
    if isinstance(kennz, str):
        kennz = kennz.split(",")
    return (v for v in list if any(v.kennz[k] for k in kennz))


def filter_kennz_not(list: List[dish], kennz):
    if isinstance(kennz, str):
        kennz = kennz.split(",")
    return (v for v in list if not any(v.kennz[k] for k in kennz))


def filter_zusatz(list: List[dish], zusatz):
    if isinstance(zusatz, str):
        zusatz = zusatz.split(",")
    return (v for v in list if any(v.zusatz[k] for k in zusatz))


def filter_zusatz_not(list: List[dish], zusatz):
    if isinstance(zusatz, str):
        zusatz = zusatz.split(",")
    return (v for v in list if not any(v.zusatz[k] for k in zusatz))


def filter_ketchup(list: List[dish]):
    return (v for v in list if any(s in v.name.lower() for s in KETCHUP))


JINJA2_ENV.filters["kennz"] = filter_kennz
JINJA2_ENV.filters["kennz_not"] = filter_kennz_not
JINJA2_ENV.filters["zusatz"] = filter_zusatz
JINJA2_ENV.filters["zusatz_not"] = filter_zusatz_not
JINJA2_ENV.filters["ketchup"] = filter_ketchup
JINJA2_ENV.filters["format_date"] = format_date
JINJA2_ENV.filters["format_time"] = format_time

schedule = NamedTuple("schedule", [("open", time), ("close", time), ("day", datetime)])


def get_mensa_formatted(dt, locale=LANG[0]):
    return JINJA2_ENV.get_template(locale + "/menu.md").render(
        {"menu": get_menu_day(dt), "date": dt, "now": datetime.now(), "locale": locale})


def get_open_formatted(loc, dt, locale=LANG[0]):
    # next open date
    open_info = get_next_open(dt, LOCATIONS[loc])

    # schedule for the current week
    sched = [schedule(*get_opening_times(LOCATIONS[loc])[(is_holiday(day), day.isoweekday() - 1)], day=day)
             for day in [dt + timedelta(days=i - dt.weekday()) for i in range(7)]]

    return JINJA2_ENV.get_template(locale + "/open.md").render(
        {"open_info": open_info, "schedule": sched, "date": dt, "loc": loc, "NOT_OPEN": NOT_OPEN,
         "now": datetime.now(), "locale": locale})


def get_abbr():
    return JINJA2_ENV.get_template("abbr.md").render()


def parse_loc_date(s):
    tokens = s.split(" ")
    # check whether location is first word
    loc = parse_loc(tokens[0])
    if loc:
        return loc, parse_date(tokens[1:])
    # or last word
    loc = parse_loc(tokens[-1])
    if loc:
        return loc, parse_date(tokens[:-1])
    # otherwise, it's probably only a date
    return None, parse_date(tokens)


def parse_loc(s):
    if not s or s == ['']:
        return None
    if not isinstance(s, str):
        s = " ".join(s)
    s = s.lower()

    if s == "am" or s.startswith("audi"):
        return "audimax"
    elif s in ["m", "mc", "mensa"] or s.startswith("mensac"):
        return "mensacafete"
    elif s in ["nk", "kk", "kc", "kuca", "kuka"] or s.startswith("niko") or s.startswith("kul"):
        return "nikolakloster"
    elif s in ["w", "wi", "ww", "wiwi"]:
        return "wiwi"
    elif s == "essen" or s.startswith("mensae"):
        return "mensaessen"

    return None


def parse_date(s):
    if not s or s == ['']:
        return None
    if not isinstance(s, str):
        s = " ".join(s)

    v = dateparser.parse(s, languages=LANG, settings=DATEPARSER_SETTINGS)
    if not v:
        raise ValueError("Could not parse date '%s'" % s)
    return v
