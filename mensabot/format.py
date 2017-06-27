import datetime as dtm
import inspect
import os
import subprocess
from typing import List, NamedTuple

import pkg_resources
from babel.dates import format_date, format_time
from jinja2 import PackageLoader, TemplateNotFound
from jinja2.sandbox import SandboxedEnvironment

from mensabot.config_default import DEPLOY_MODE
from mensabot.mensa import LOCATIONS, NOT_OPEN, dish, get_menu_day, get_next_open, get_opening_times, is_holiday
from mensabot.parse import LANG

KETCHUP = ["kartoffel", "potato", "pommes", "twister", "kroketten", "rösti", "schnitzel", "cordon", "burger", "fries"]

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


@jinja2_filter("warengruppe")
def filter_warengruppe(list: List[dish], warengruppe):
    if isinstance(warengruppe, str):
        warengruppe = warengruppe.split(",")
    return (v for v in list if any(v.warengruppe.startswith(w) for w in warengruppe))


@jinja2_filter("warengruppe_not")
def filter_warengruppe_not(list: List[dish], warengruppe):
    if isinstance(warengruppe, str):
        warengruppe = warengruppe.split(",")
    return (v for v in list if not any(v.warengruppe.startswith(w) for w in warengruppe))


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
    return (v for v in list if any(v.zusatz[z] for z in zusatz))


@jinja2_filter("zusatz_not")
def filter_zusatz_not(list: List[dish], zusatz):
    if isinstance(zusatz, str):
        zusatz = zusatz.split(",")
    return (v for v in list if not any(v.zusatz[z] for z in zusatz))


@jinja2_filter("ketchup")
def filter_ketchup(list: List[dish]):
    return (v for v in list if any(s in v.name.lower() for s in KETCHUP))


def get_mensa_formatted(dt, template=None, locale=None, price_category="stud"):
    locale = locale or LANG[0]
    template = template or locale
    return JINJA2_ENV.get_template("{}/menu.md".format(template)).render(
        {"menu": get_menu_day(dt), "date": dt, "now": dtm.datetime.now(), "locale": locale,
         "price_category": price_category})


def get_mensa_diff_formatted(dt, diff, template=None, locale=None, price_category="stud"):
    locale = locale or LANG[0]
    template = template or locale
    return JINJA2_ENV.get_template("{}/diff.md".format(template)).render(
        {"diff": diff, "date": dt, "now": dtm.datetime.now(), "locale": locale,
         "price_category": price_category})


schedule = NamedTuple("schedule", [("open", dtm.time), ("close", dtm.time), ("day", dtm.datetime)])


def get_open_formatted(loc, dt, template=None, locale=None):
    locale = locale or LANG[0]
    template = template or locale

    # next open date
    open_info = get_next_open(dt, LOCATIONS[loc])

    # schedule for the current week
    sched = [schedule(*get_opening_times(LOCATIONS[loc])[(is_holiday(day), day.isoweekday() - 1)], day=day)
             for day in [dt + dtm.timedelta(days=i - dt.weekday()) for i in range(7)]]

    return JINJA2_ENV.get_template("{}/open.md".format(template)).render(
        {"open_info": open_info, "schedule": sched, "date": dt, "loc": loc, "NOT_OPEN": NOT_OPEN,
         "now": dtm.datetime.now(), "locale": locale})


def get_abbr():
    return JINJA2_ENV.get_template("abbr.md").render()


def check_legal_template(dir):
    if dir is None:
        return None
    try:
        JINJA2_ENV.get_template("{}/menu.md".format(dir))
        JINJA2_ENV.get_template("{}/open.md".format(dir))
        return dir
    except TemplateNotFound:
        raise ValueError("Unknown template '%s'. Try 'de' or 'en'." % dir)


def get_version():
    pkg_data = pkg_resources.require("mensabot")[0]
    try:
        git_rev = subprocess.check_output(
            ["git", "describe", "--always"],
            cwd=os.path.dirname(inspect.getfile(inspect.currentframe()))
        ).decode('ascii').strip()
    except NotADirectoryError:
        git_rev = "release"
    return "{} {} {} [{}]".format(pkg_data.project_name.title(), pkg_data.version, git_rev, DEPLOY_MODE)
