import logging
import traceback
from datetime import datetime, timedelta

import telegram
from telegram.ext import CommandHandler, Updater

from mensabot.config import TELEGRAM_TOKEN
from mensabot.format import LOCATIONS, get_abbr, get_mensa_formatted, get_open_formatted, \
    parse_loc_date

MARKDOWN = telegram.ParseMode.MARKDOWN

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
# logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.DEBUG)

updater = Updater(token=TELEGRAM_TOKEN)
dispatcher = updater.dispatcher


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
    bot.sendMessage(chat_id=update.message.chat_id, text="MensaBot Passau to your service. "
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
        if loc:
            raise ValueError("Currently, only default location is supported")
    except ValueError as e:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="%s. Try 'today', 'tomorrow', 'Friday' or a date." % e)
        return

    bot.sendMessage(chat_id=update.message.chat_id, text=get_mensa_formatted(dt), parse_mode=MARKDOWN)


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

    bot.sendMessage(chat_id=update.message.chat_id, text=get_open_formatted(loc, dt), parse_mode=MARKDOWN)


@ComHandlerFunc("abbr")
def abbr(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=get_abbr(), parse_mode=MARKDOWN)


updater.start_polling()

print("Listening...")
