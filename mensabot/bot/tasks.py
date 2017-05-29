import logging
import math
import sched
import time as systime
from contextlib import ExitStack, closing
from datetime import date, datetime, time, timedelta

from sqlalchemy import and_

from mensabot.bot.command.mensa import mensa_notifications, send_menu_message
from mensabot.bot.ext import updater
from mensabot.db import CHATS, SQL_ENGINE
from mensabot.mensa import clear_caches, get_menu_day, get_menu_week

SCHED = sched.scheduler(systime.time, systime.sleep)
SCHED_INTERVAL = 1

logger = logging.getLogger("mensabot.sched")


def run_sched():
    schedule_notification()
    schedule_update_menu()
    schedule_clear_cache()
    schedule_clear_mensa_notifications()

    running = True
    while running:
        try:
            logger.debug("Handing over to scheduler")
            SCHED.run(blocking=True)
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

    if not get_menu_day(now):
        later = (later + timedelta(days=1)).replace(hour=0, minute=0)
        logger.debug("Not sending any notifications at {:%Y-%m-%d %H:%M} as no menu is available".format(now))
    else:
        logger.debug("Scheduling notifications between {:%H:%M} and {:%H:%M}".format(now, later))

    SCHED.enterabs(later.timestamp(), 10, schedule_notification, [later])

    with ExitStack() as s:
        conn = s.enter_context(closing(SQL_ENGINE.connect()))
        res = s.enter_context(closing(conn.execute(
            CHATS.select()
                .where(and_(CHATS.c.notification_time >= now.time(), CHATS.c.notification_time < later.time()))
                .order_by(CHATS.c.notification_time.asc())
        )))
        for row in res:
            notify_time = datetime.combine(now.date(), row.notification_time)
            logger.debug("Scheduling notification to {} for {:%H:%M}".format(row, notify_time))
            SCHED.enterabs(notify_time.timestamp(), 100, send_menu_message, [notify_time, row, row.id])


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
    logger.debug("Resetting mensa notifications")
    now = datetime.now()
    next = datetime.combine((now + timedelta(days=1)).date(), time(0, 30))
    SCHED.enterabs(next.timestamp(), 1000, schedule_clear_mensa_notifications)
    mensa_notifications.clear()
