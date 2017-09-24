from typing import List

from babel.dates import format_date, format_time
from jinja2 import PackageLoader, TemplateNotFound
from jinja2.sandbox import SandboxedEnvironment

from stwno_api import Dish
from stwno_api.util import ensure_date

JINJA2_ENV = SandboxedEnvironment(
    loader=PackageLoader('stwno_cmds', 'templates'),
    trim_blocks=True, lstrip_blocks=True, auto_reload=True
)
JINJA2_ENV.filters["format_date"] = format_date
JINJA2_ENV.filters["format_time"] = format_time
JINJA2_ENV.filters["ensure_date"] = ensure_date

KETCHUP = ["kartoffel", "potato", "pommes", "twister", "kroketten", "rösti", "schnitzel", "cordon", "burger", "fries"]


def jinja2_filter(filter_name):
    def tags_decorator(func):
        JINJA2_ENV.filters[filter_name] = func
        return func

    return tags_decorator


@jinja2_filter("warengruppe")
def filter_warengruppe(list: List[Dish], warengruppe):
    if isinstance(warengruppe, str):
        warengruppe = warengruppe.split(",")
    return (v for v in list if any(v.warengruppe.startswith(w) for w in warengruppe))


@jinja2_filter("warengruppe_not")
def filter_warengruppe_not(list: List[Dish], warengruppe):
    if isinstance(warengruppe, str):
        warengruppe = warengruppe.split(",")
    return (v for v in list if not any(v.warengruppe.startswith(w) for w in warengruppe))


@jinja2_filter("kennz")
def filter_kennz(list: List[Dish], kennz):
    if isinstance(kennz, str):
        kennz = kennz.split(",")
    return (v for v in list if any(v.kennz[k] for k in kennz))


@jinja2_filter("kennz_not")
def filter_kennz_not(list: List[Dish], kennz):
    if isinstance(kennz, str):
        kennz = kennz.split(",")
    return (v for v in list if not any(v.kennz[k] for k in kennz))


@jinja2_filter("zusatz")
def filter_zusatz(list: List[Dish], zusatz):
    if isinstance(zusatz, str):
        zusatz = zusatz.split(",")
    return (v for v in list if any(v.zusatz[z] for z in zusatz))


@jinja2_filter("zusatz_not")
def filter_zusatz_not(list: List[Dish], zusatz):
    if isinstance(zusatz, str):
        zusatz = zusatz.split(",")
    return (v for v in list if not any(v.zusatz[z] for z in zusatz))


@jinja2_filter("ketchup")
def filter_ketchup(list: List[Dish]):
    return (v for v in list if any(s in v.name.lower() for s in KETCHUP))


def check_legal_template(dir):
    if dir is None:
        return None
    try:
        from stwno_cmds.format import JINJA2_ENV
        JINJA2_ENV.get_template("{}/menu.md".format(dir))
        JINJA2_ENV.get_template("{}/open.md".format(dir))
        JINJA2_ENV.get_template("{}/diff.md".format(dir))
        return dir
    except TemplateNotFound:
        raise ValueError("Unknown template '%s'. Try 'de' or 'en'." % dir)
