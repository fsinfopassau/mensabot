import inspect
import logging
import os
import subprocess
import traceback
from contextlib import ExitStack, closing, contextmanager
from datetime import datetime, timedelta

import pkg_resources
import telegram
from telegram.ext import CommandHandler, Updater

from mensabot import config
from mensabot.config import TELEGRAM_TOKEN
from mensabot.format import get_abbr, get_mensa_formatted, get_next_menu_date, get_open_formatted
from mensabot.mensa import LOCATIONS, PRICES_CATEGORIES
from mensabot.parse import parse_loc_date
from mensabot.db import CHATS, SQL_ENGINE

MARKDOWN = telegram.ParseMode.MARKDOWN

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
# logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.DEBUG)

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
        bot.sendMessage(
            chat_id=update.message.chat_id,
            text=get_mensa_formatted(
                dt,
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


def main():
    updater.start_polling()
    print("Listening...")


if __name__ == "__main__":
    main()
