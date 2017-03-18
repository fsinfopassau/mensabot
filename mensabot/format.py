import humanize
from jinja2 import PackageLoader
from jinja2.sandbox import SandboxedEnvironment

from mensabot.mensa import *

LANG = ['de', 'en']
humanize.i18n.activate(LANG[0])

DATEPARSER_SETTINGS = {'PREFER_DATES_FROM': 'future'}

JINJA2_ENV = SandboxedEnvironment(
    loader=PackageLoader('mensabot', 'templates'),
    trim_blocks=True, lstrip_blocks=True, auto_reload=True
)

KETCHUP = ["kartoffel", "potato", "pommes", "twister", "kroketten", "rösti", "schnitzel", "curry", "cordon"]


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

schedule = NamedTuple("schedule", [("open", time), ("close", time), ("day", datetime)])


def get_mensa_formatted(dt):
    return JINJA2_ENV.get_template("menu.md").render({"menu": get_menu_day(dt), "date": dt})


def get_open_formatted(loc, dt):
    # next open date
    open_info = get_next_open(dt, loc)

    # schedule for the current week
    sched = [schedule(*get_opening_times(loc)[(is_holiday(day), day.isoweekday() - 1)], day=day)
             for day in [dt + timedelta(days=i - dt.weekday()) for i in range(7)]]

    return JINJA2_ENV.get_template("open.md").render(
        {"open_info": open_info, "schedule": sched, "date": dt, "loc": loc, "NOT_OPEN": NOT_OPEN})

def get_abbr():
    return JINJA2_ENV.get_template("abbr.md").render()
