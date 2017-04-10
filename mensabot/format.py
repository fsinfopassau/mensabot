from contextlib import closing

from babel.dates import format_date, format_time
from jinja2 import BaseLoader, PackageLoader
from jinja2.sandbox import SandboxedEnvironment

from mensabot.mensa import *
from mensabot.parse import LANG
from mensabot.user import chats, engine, templates

KETCHUP = ["kartoffel", "potato", "pommes", "twister", "kroketten", "rösti", "schnitzel", "cordon"]

LOCATIONS = {
    "audimax": "cafeterien/cafeteria-uni-pa-audimax",
    "mensacafete": "cafeterien/cafeteria-uni-pa-mensagebaeude",
    "nikolakloster": "cafeterien/cafeteria-uni-pa-nikolakloster",
    "wiwi": "cafeterien/cafebar-uni-pa-wiwi",
    "mensaessen": "mensen/mensa-uni-passau"
}


class DBTemplateLoader(BaseLoader):
    def __init__(self, file_loader, default_path):
        self.file_loader = file_loader
        self.default_path = default_path

    def get_source(self, environment, template):
        path = template.split("/")
        if len(path) != 2:
            return self.file_loader.get_source(environment, template)
        user, file = path

        conn = engine.connect()
        # check if user uses a built-in template
        with closing(conn.execute(chats.select(chats.c.id == user))) as res:
            row = res.fetchone()
            if row and row.template_path:
                return self.file_loader.get_source(environment, "{}/{}".format(row.template_path, file))

        # check if user uses a custom template
        q = templates.select(templates.c.user_id == user and templates.c.filename == file)
        with closing(conn.execute(q)) as res:
            row = res.fetchone()
            if row:
                return row.template, "sqlite://templates/{}/{}".format(user, file), lambda: True

        # return default template
        return self.file_loader.get_source(environment, self.default_path + "/" + file)


JINJA2_ENV = SandboxedEnvironment(
    loader=DBTemplateLoader(PackageLoader('mensabot', 'templates'), LANG[0]),
    trim_blocks=True, lstrip_blocks=True, auto_reload=True
)


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


JINJA2_ENV.filters["format_date"] = format_date
JINJA2_ENV.filters["format_time"] = format_time



def get_mensa_formatted(dt, locale=LANG[0]):
    return JINJA2_ENV.get_template(locale + "/menu.md").render(
        {"menu": get_menu_day(dt), "date": dt, "now": datetime.now(), "locale": locale})


schedule = NamedTuple("schedule", [("open", time), ("close", time), ("day", datetime)])


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
