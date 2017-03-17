import logging
from datetime import datetime

import dateparser
import telegram
from telegram.ext import CommandHandler, Updater

from mensabot.config import TELEGRAM_TOKEN
from mensabot.format import DATEPARSER_SETTINGS, LANG, LOCATIONS, get_mensa_formatted, get_open_formatted

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
    date = dateparser.parse(arg if arg else ("tomorrow" if datetime.now().hour > 15 else "today"),
                            languages=LANG, settings=DATEPARSER_SETTINGS)
    if not date:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Could not parse date '%s'. Try 'today', 'tomorrow', 'Friday' or a date." % arg)
    else:
        bot.sendMessage(chat_id=update.message.chat_id, text=get_mensa_formatted(date), parse_mode=MARKDOWN)


@ComHandlerFunc("cafete")
def cafete(bot, update):
    args = update.message.text.strip().split(" ")
    date, loc = None, None
    args = ["today", "mensacafete"] + args[1:]
    for arg in args:
        new_date = dateparser.parse(arg, languages=LANG, settings=DATEPARSER_SETTINGS)
        if new_date:
            date = new_date
            continue
        new_loc = LOCATIONS.get(arg, None)
        if new_loc:
            loc = new_loc
            continue

        k = list(LOCATIONS.keys())
        s = " or ".join([", ".join(k[:-1]), k[-1]])
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Could not parse '%s'. "
                             "Try 'today', 'tomorrow', 'Friday', any date or the locations %s." % (arg, s))
        return

    bot.sendMessage(chat_id=update.message.chat_id, text=get_open_formatted(loc, date),
                    parse_mode=MARKDOWN)


updater.start_polling()

print("Listening...")
