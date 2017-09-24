import datetime as dtm
from typing import Union


def ensure_date(dt: Union[dtm.datetime, dtm.date, str]):
    if isinstance(dt, dtm.datetime):
        return dt.date()
    elif isinstance(dt, dtm.date):
        return dt
    else:
        raise ValueError("'%s' can't be converted to a date" % dt)
