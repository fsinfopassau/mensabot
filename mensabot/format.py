from babel.dates import format_date, format_time
from jinja2 import PackageLoader
from jinja2.sandbox import SandboxedEnvironment

from mensabot.mensa import *
from mensabot.mensa import LOCATIONS
from mensabot.parse import LANG

KETCHUP = ["kartoffel", "potato", "pommes", "twister", "kroketten", "rösti", "schnitzel", "cordon"]

JINJA2_ENV = SandboxedEnvironment(
    loader=PackageLoader('mensabot', 'templates'),
    trim_blocks=True, lstrip_blocks=True, auto_reload=True
)
JINJA2_ENV.filters["format_date"] = format_date
JINJA2_ENV.filters["format_time"] = format_time


def jinja2_filter(filter_name):
    def tags_decorator(func):
        JINJA2_ENV.filters[filter_name] = func
        return func

    return tags_decorator


@jinja2_filter("kennz")
def filter_kennz(list: List[dish], kennz):
    if isinstance(kennz, str):
        kennz = kennz.split(",")
    return (v for v in list if any(v.kennz[k] for k in kennz))


@jinja2_filter("kennz_not")
def filter_kennz_not(list: List[dish], kennz):
    if isinstance(kennz, str):
        kennz = kennz.split(",")
    return (v for v in list if not any(v.kennz[k] for k in kennz))


@jinja2_filter("zusatz")
def filter_zusatz(list: List[dish], zusatz):
    if isinstance(zusatz, str):
        zusatz = zusatz.split(",")
    return (v for v in list if any(v.zusatz[k] for k in zusatz))


@jinja2_filter("zusatz_not")
def filter_zusatz_not(list: List[dish], zusatz):
    if isinstance(zusatz, str):
        zusatz = zusatz.split(",")
    return (v for v in list if not any(v.zusatz[k] for k in zusatz))


@jinja2_filter("ketchup")
def filter_ketchup(list: List[dish]):
    return (v for v in list if any(s in v.name.lower() for s in KETCHUP))


def get_mensa_formatted(dt, template=None, price_cat="stud", locale=LANG[0]):
    if not template:
        template = locale
    return JINJA2_ENV.get_template("{}/menu.md".format(template)).render(
        {"menu": get_menu_day(dt), "date": dt, "now": datetime.now(), "locale": locale, "price_cat": price_cat})


schedule = NamedTuple("schedule", [("open", time), ("close", time), ("day", datetime)])


def get_open_formatted(loc, dt, template=None, locale=LANG[0]):
    if not template:
        template = locale

    # next open date
    open_info = get_next_open(dt, LOCATIONS[loc])

    # schedule for the current week
    sched = [schedule(*get_opening_times(LOCATIONS[loc])[(is_holiday(day), day.isoweekday() - 1)], day=day)
             for day in [dt + timedelta(days=i - dt.weekday()) for i in range(7)]]

    return JINJA2_ENV.get_template("{}/open.md".format(template)).render(
        {"open_info": open_info, "schedule": sched, "date": dt, "loc": loc, "NOT_OPEN": NOT_OPEN,
         "now": datetime.now(), "locale": locale})


def get_abbr():
    return JINJA2_ENV.get_template("abbr.md").render()
