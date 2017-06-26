import logging
import math
import sched
import time as systime
from datetime import date, datetime, time, timedelta

from sqlalchemy import and_

from mensabot.bot.command import mensa
from mensabot.bot.command.mensa import default_menu_date, send_menu_message
from mensabot.bot.ext import updater
from mensabot.db import CHATS, connection
from mensabot.mensa import clear_caches, get_menu_week, get_next_open

SCHED = sched.scheduler(systime.time, systime.sleep)
SCHED_INTERVAL = 1

logger = logging.getLogger("mensabot.sched")


def run_sched():
    schedule_notification()
    schedule_update_menu()
    schedule_clear_cache()
    schedule_clear_mensa_notifications()

    running = True
    logger.debug("Handing over to scheduler")
    while running:
        try:
            delay = SCHED.run(blocking=False)
            systime.sleep(min(delay, 1))
        except KeyboardInterrupt:
            running = False
            logger.info("KeyboardInterrupt, shutting down.", exc_info=1)
            updater.stop()
        except:
            logger.error("Exception from scheduler, restarting.", exc_info=1)


def schedule_notification(now=None):
    if not now:
        now = datetime.now()
        now = now.replace(minute=math.floor(now.minute / SCHED_INTERVAL) * SCHED_INTERVAL,
                          second=0, microsecond=0)
    later = now + timedelta(minutes=SCHED_INTERVAL)

    mensa_date = default_menu_date()
    next_close = next_mensa_close_dt(mensa_date)
    if next_close - now > timedelta(days=1):
        later = next_close - timedelta(days=1)
        logger.debug("Not sending any notifications at {:%H:%M} as no menu is available "
                     "(next notifications start at {:%Y-%m-%d %H:%M} as next menu is available for {:%Y-%m-%d})"
                     .format(now, later, mensa_date))
    else:
        logger.debug("Scheduling notifications between {:%H:%M} and {:%H:%M}".format(now, later))

    SCHED.enterabs(later.timestamp(), 10, schedule_notification, [later])

    with connection() as (conn, execute):
        res = execute(
            CHATS.select()
                .where(and_(CHATS.c.push_time >= now.time(), CHATS.c.push_time < later.time()))
                .order_by(CHATS.c.push_time.asc())
        )
        for row in res:
            notify_time = datetime.combine(now.date(), row.push_time)
            logger.debug("Scheduling notification to {} for {:%H:%M}".format(row, notify_time))
            SCHED.enterabs(notify_time.timestamp(), 100,
                           lambda row=row: send_menu_message(mensa_date, row, row.id))
            # `row` needs to be captured explicitly in a new scope, otherwise it would always have the last used value
            # after the loop terminated. See here: https://stackoverflow.com/a/2295372/805569


def schedule_update_menu():
    logger.debug("Fetching new menu")
    SCHED.enter(5 * 60, 11, schedule_update_menu)
    get_menu_week(date.today().isocalendar()[1], disable_cache=True)


def schedule_clear_cache():
    now = datetime.now()
    next = datetime.combine((now + timedelta(days=1)).date(), time(2, 0))
    SCHED.enterabs(next.timestamp(), 1000, schedule_clear_cache)
    clear_caches()


def schedule_clear_mensa_notifications():
    next_close = next_mensa_close_dt()
    SCHED.enterabs(next_close.timestamp(), 1000, schedule_clear_mensa_notifications)

    today = default_menu_date().date()
    if mensa.mensa_notification_date != today:
        logger.debug("Dropping mensa notifications from {:%Y-%m-%d}, because new mensa date is {:%Y-%m-%d}"
                     " (next reset at {:%Y-%m-%d %H:%M})".format(mensa.mensa_notification_date, today, next_close))
        mensa.mensa_notifications.clear()
        mensa.mensa_notification_date = today


def next_mensa_close_dt(now=datetime.now()) -> datetime:
    open_info = get_next_open(now, "mensen/mensa-uni-passau")
    if open_info:
        return datetime.combine(open_info.day.date(), open_info.close) + timedelta(minutes=1)
    else:
        return datetime.combine((now + timedelta(days=1)).date(), time(15, 1))
