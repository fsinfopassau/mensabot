import datetime as dtm
import logging
import math
import sched
import time as systime

import requests
from sqlalchemy import and_

from mensabot.bot.command import mensa
from mensabot.bot.command.mensa import send_menu_message
from mensabot.bot.ext import updater
from mensabot.db import CHATS, connection
from mensabot.mensa import clear_caches, get_menu_week, get_next_mensa_open

# TODO use telegram task queue
# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Extensions-%E2%80%93-JobQueue
SCHED = sched.scheduler(systime.time, systime.sleep)
SCHED_INTERVAL = 1
SCHED_TASK_COUNT = 4

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
            if len(SCHED.queue) < SCHED_TASK_COUNT:
                logger.error("Only %d running tasks left: %s" %
                             (len(SCHED.queue), [task_name(task) for task in SCHED.queue]))


def task_name(task):
    return getattr(task.action, '__name__', repr(task.action))


def schedule_notification(now=None):
    if not now:
        now = dtm.datetime.now()
        now = now.replace(minute=math.floor(now.minute / SCHED_INTERVAL) * SCHED_INTERVAL,
                          second=0, microsecond=0)
    later = now + dtm.timedelta(minutes=SCHED_INTERVAL)

    try:
        (open, close, day, offset), menu = get_next_mensa_open(now)
        next_close = dtm.datetime.combine(day.date(), close)
        if next_close - now > dtm.timedelta(days=1):
            later = next_close - dtm.timedelta(days=1)
            logger.debug("Not sending any notifications at {:%H:%M} as no menu is available "
                         "(next notifications start at {:%Y-%m-%d %H:%M} as next menu is available for {:%Y-%m-%d})"
                         .format(now, later, day))
        else:
            logger.debug("Scheduling notifications between {:%H:%M} and {:%H:%M}".format(now, later))
    except requests.exceptions.RequestException:
        logger.warning("Could not get next opening time of mensa, trying again in 1 minute", exc_info=True)

    SCHED.enterabs(later.timestamp(), 10, schedule_notification, [later])

    with connection() as (conn, execute):
        res = execute(
            CHATS.select()
                .where(and_(CHATS.c.push_time >= now.time(), CHATS.c.push_time < later.time()))
                .order_by(CHATS.c.push_time.asc())
        )
        for row in res:
            notify_time = dtm.datetime.combine(now.date(), row.push_time)
            logger.debug("Scheduling notification to {} for {:%H:%M}".format(row, notify_time))
            SCHED.enterabs(notify_time.timestamp(), 100,
                           lambda row=row: send_menu_message(day, row, row.id))
            # `row` needs to be captured explicitly in a new scope, otherwise it would always have the last used value
            # after the loop terminated. See here: https://stackoverflow.com/a/2295372/805569
            # this also needs to use `day` instead of `notify_time`, because we could be requesting the menu for
            # tomorrow on the evening before


def schedule_update_menu():
    logger.debug("Fetching new menu")
    SCHED.enter(5 * 60, 11, schedule_update_menu)
    try:
        get_menu_week(dtm.date.today().isocalendar()[1], disable_cache=True)
    except requests.exceptions.RequestException:
        logger.warning("Could not fetch new menu, trying again later", exc_info=True)


def schedule_clear_cache():
    now = dtm.datetime.now()
    next = dtm.datetime.combine((now + dtm.timedelta(days=1)).date(), dtm.time(2, 0))
    SCHED.enterabs(next.timestamp(), 1000, schedule_clear_cache)
    clear_caches()


def schedule_clear_mensa_notifications():
    try:
        (open, close, day, offset), menu = get_next_mensa_open()
        next_close = dtm.datetime.combine(day.date(), close)
        SCHED.enterabs((next_close + dtm.timedelta(minutes=1)).timestamp(), 1000, schedule_clear_mensa_notifications)

        if mensa.notifications_date != day.date():
            logger.debug("Dropping mensa notifications from {:%Y-%m-%d}, because new mensa date is {:%Y-%m-%d}"
                         " (next reset on that day at {:%H:%M})"
                         .format(mensa.notifications_date, day.date(), next_close))
            mensa.notifications.clear()
            mensa.notifications_date = day.date()
        else:
            logger.debug("Not dropping mensa notifications from {:%Y-%m-%d}, because it is still the next mensa date "
                         " (next reset on that day at {:%H:%M})"
                         .format(mensa.notifications_date, next_close))
    except requests.exceptions.RequestException:
        logger.warning("Could not get next opening time of mensa, trying again in 1 minute", exc_info=True)
        SCHED.enterabs((dtm.datetime.now() + dtm.timedelta(minutes=1)).timestamp(), 1000,
                       schedule_clear_mensa_notifications)
