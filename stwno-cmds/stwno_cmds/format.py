import datetime as dtm
from typing import List, NamedTuple, Union

from stwno_api import Change, NOT_OPEN, StwnoApi
from stwno_api.institution import Location
from stwno_api.util import ensure_date
from stwno_cmds.parse import LANG
from stwno_cmds.template import JINJA2_ENV

Schedule = NamedTuple("Schedule", [("open", dtm.time), ("close", dtm.time), ("day", dtm.datetime)])


# noinspection PyUnusedLocal
def user_config_defaults(**kwargs):
    locale = kwargs.setdefault("locale", LANG[0])
    template = kwargs.setdefault("template", locale)
    price_category = kwargs.setdefault("price_category", StwnoApi.PRICES_CATEGORIES[0])
    now = kwargs.setdefault("now", dtm.datetime.now())
    return kwargs


def get_menu_formatted(api: StwnoApi, day: Union[dtm.datetime, dtm.date, str] = None, location: Location = None,
                       **kwargs) -> str:
    day = ensure_date(day or dtm.date.today())
    location = location or api.institution.default_mensa
    kwargs = user_config_defaults(**kwargs)

    return JINJA2_ENV.get_template("{}/menu.md".format(kwargs["template"])).render(
        {"menu": api.get_menu_of_day(day, location), "day": day, "location": location, **kwargs})


def get_menu_diff_formatted(diff: List[Change], day: Union[dtm.datetime, dtm.date, str], **kwargs) -> str:
    day = ensure_date(day or dtm.date.today())
    kwargs = user_config_defaults(**kwargs)

    return JINJA2_ENV.get_template("{}/diff.md".format(kwargs["template"])).render(
        {"diff": diff, "day": day, **kwargs})


def get_opening_times_formatted(api: StwnoApi, dt: dtm.datetime = None, location: Location = None, **kwargs) -> str:
    dt = dt or dtm.datetime.now()
    location = location or api.institution.default_cafeteria
    kwargs = user_config_defaults(**kwargs)

    # next open date
    open_info = api.get_next_open(location, dt)

    # schedule for the current week
    sched = [
        Schedule(*api.get_opening_times(location)[(api.institution.is_holiday(day), day.isoweekday() - 1)], day=day)
        for day in [dt + dtm.timedelta(days=i - dt.weekday()) for i in range(7)]]

    return JINJA2_ENV.get_template("{}/open.md".format(kwargs["template"])).render(
        {"open_info": open_info, "schedule": sched, "datetime": dt, "location": location, "NOT_OPEN": NOT_OPEN,
         **kwargs})


def get_abbr(**kwargs) -> str:
    kwargs = user_config_defaults(**kwargs)
    # TODO translate?
    return JINJA2_ENV.get_template("abbr.md").render(kwargs)
