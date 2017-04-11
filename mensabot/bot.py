import inspect
import logging
import math
import os
import sched
import subprocess
import time as systime
import traceback
from contextlib import ExitStack, closing, contextmanager
from datetime import datetime, time, timedelta

import pkg_resources
import telegram
from sqlalchemy import and_
from telegram.ext import CommandHandler, Updater

from mensabot import config
from mensabot.config import TELEGRAM_TOKEN
from mensabot.db import CHATS, SQL_ENGINE
from mensabot.format import check_legal_template, get_abbr, get_mensa_formatted, get_open_formatted
from mensabot.mensa import LOCATIONS, PRICES_CATEGORIES, clear_caches, get_menu_day, get_next_menu_date
from mensabot.parse import LANG, parse_loc_date

MARKDOWN = telegram.ParseMode.MARKDOWN

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
# logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.INFO)
# logging.getLogger("telegram").setLevel(logging.INFO)
logger = logging.getLogger("mensabot.bot")

updater = Updater(token=TELEGRAM_TOKEN)
dispatcher = updater.dispatcher


@contextmanager
def chat_record(update):
    id = update.message.chat.id
    with ExitStack() as s:
        conn = s.enter_context(closing(SQL_ENGINE.connect()))
        res = s.enter_context(closing(conn.execute(CHATS.select(CHATS.c.id == id))))
        yield res.fetchone()


def ComHandlerFunc(command, **kwargs):
    def func_decorator(func):
        def func_wrapper(bot, update):
            try:
                func(bot, update)
            except:
                traceback.print_exc()
                bot.sendMessage(
                    chat_id=update.message.chat_id, text="Master, I failed! 😢", parse_mode=MARKDOWN)
                raise

        handler = CommandHandler(command, func_wrapper, **kwargs)
        dispatcher.add_handler(handler)
        func_wrapper.handler = handler
        return func_wrapper

    return func_decorator


@ComHandlerFunc("start")
def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text= \
        "MensaBot Passau to your service. "
        "Try /mensa or /cafete and add a time or location if you want.")


@ComHandlerFunc("mensa")
def mensa(bot, update):
    arg = update.message.text.replace("/mensa", "").strip()
    try:
        loc, dt = parse_loc_date(arg)
        if not dt:
            dt = datetime.now()
            if dt.hour > 15:
                dt += timedelta(days=1)
            dt = get_next_menu_date(dt)
        if loc:
            raise ValueError("Currently, only default location is supported")
    except ValueError as e:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="%s. Try 'today', 'tomorrow', 'Friday' or a date." % e)
        return

    with chat_record(update) as chat:
        send_menu_message(dt, chat, update.message.chat_id)


def send_menu_message(time, chat, chat_id):
    updater.bot.sendMessage(
        chat_id=chat_id,
        text=get_mensa_formatted(
            time,
            template=chat.template if chat else None,
            locale=chat.locale if chat else None,
            price_category=PRICES_CATEGORIES[chat.price_category if chat else 0]),
        parse_mode=MARKDOWN)


@ComHandlerFunc("cafete")
def cafete(bot, update):
    arg = update.message.text.replace("/cafete", "").strip()
    try:
        loc, dt = parse_loc_date(arg)
        if not dt:
            dt = datetime.now()
        if not loc:
            loc = "mensacafete"
    except ValueError as e:
        k = list(LOCATIONS.keys())
        s = " or ".join([", ".join(k[:-1]), k[-1]])
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="%s. Try 'today', 'tomorrow', 'Friday', any date or the locations %s." % (e, s))
        return

    with chat_record(update) as chat:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text=get_open_formatted(
                            loc, dt,
                            template=chat.template if chat else None,
                            locale=chat.locale if chat else None),
                        parse_mode=MARKDOWN)


@ComHandlerFunc("abbr")
def abbr(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=get_abbr(), parse_mode=MARKDOWN)


@ComHandlerFunc("version")
def version(bot, update):
    pkg_data = pkg_resources.require("mensabot")[0]
    try:
        git_rev = subprocess.check_output(
            ["git", "describe", "--always"],
            cwd=os.path.dirname(inspect.getfile(inspect.currentframe()))
        ).decode('ascii').strip()
    except NotADirectoryError:
        git_rev = "release"
    bot.sendMessage(chat_id=update.message.chat_id,
                    text="{} {} {} \[{}]".format(
                        pkg_data.project_name.title(), pkg_data.version,
                        git_rev, config.DEPLOY_MODE),
                    parse_mode=MARKDOWN)


def check_price_category(x):
    idx = PRICES_CATEGORIES.index(x)
    if idx < 0:
        raise ValueError("Unknown price category '%s'. Try 'stud', 'bed' or 'gast'." % x)
    return idx


def check_locale(x):
    idx = LANG.index(x)
    if idx < 0:
        raise ValueError("Unknown locale '%s'. Try 'de' or 'en'." % x)
    return x


def check_notification_time(x):
    try:
        return datetime.strptime(x, "%H:%M:%S").time()
    except ValueError:
        try:
            return datetime.strptime(x, "%H:%M").time()
        except ValueError as e:
            raise ValueError("Could not parse time '%s', try e.g. '11:15'. (reason was %s)" % (x, e))


CONFIG_OPTIONS = {
    "template": check_legal_template,
    "price_category": check_price_category,
    "locale": check_locale,
    "notification_time": check_notification_time,
}


@ComHandlerFunc("set")
def set_config(bot, update):
    id = update.message.chat.id
    args = update.message.text.replace("/set", "").strip().split(" ")
    if len(args) != 2:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Could not parse args '%s'. Enter a config option and a new value." % args)
        return

    try:
        arg = CONFIG_OPTIONS[args[0]](args[1])
    except ValueError as e:
        bot.sendMessage(chat_id=update.message.chat_id, text=str(e))
        return

    with ExitStack() as s:
        val = {args[0]: arg}
        conn = s.enter_context(closing(SQL_ENGINE.connect()))
        res = s.enter_context(closing(conn.execute(
            CHATS.update().values(**val).where(CHATS.c.id == id)
        )))
        if res.rowcount != 1:
            s.enter_context(closing(conn.execute(
                CHATS.insert().values(id=id, **val)
            )))
    bot.sendMessage(chat_id=update.message.chat_id, text="Updated %s to '%s'." % (args[0], args[1]))


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


def schedule_clear_cache():
    now = datetime.now()
    SCHED.enterabs(datetime.combine((now + timedelta(days=7 - now.weekday())).date(), time(1, 0)).timestamp(),
                   1000, schedule_clear_cache)
    clear_caches()


SCHED = sched.scheduler(systime.time, systime.sleep)
SCHED_INTERVAL = 1


def main():
    updater.start_polling()
    logger.info("Listening...")
    schedule_notification()
    schedule_clear_cache()
    logger.debug("Handing over to scheduler")
    running = True
    while running:
        try:
            SCHED.run(blocking=True)
        except KeyboardInterrupt:
            running = False
            logger.info("KeyboardInterrupt, shutting down.", exc_info=1)
            updater.stop()
        except:
            logger.error("Exception from scheduler, restarting.", exc_info=1)


if __name__ == "__main__":
    main()
