import importlib

from mensabot.bot.ext import dispatcher
from mensabot.bot.util import ComHandlerFunc, get_args
from mensabot.format import get_abbr
from telegram import ParseMode
from telegram.ext import Filters, MessageHandler

__all__ = ["cafete", "config", "mensa", "debug"]


def init_commands():
    # commands are automatically added when their decorator is parsed,
    # so just make sure the modules are loaded
    for mod in __all__:
        importlib.import_module("." + mod, __name__)

    def unknown(bot, update):
        bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")

    unknown_handler = MessageHandler(Filters.command, unknown)
    dispatcher.add_handler(unknown_handler)


@ComHandlerFunc("start")
def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text= \
        "MensaBot Passau to your service. "
        "Try /mensa or /cafete and add a time or location if you want.")


@ComHandlerFunc("help")
def help(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text= \
        "MensaBot Passau to your service. "
        "Try /mensa or /cafete and add a time or location if you want. "
        "Examples:\n"
        "/mensa tomorrow\n"
        "/cafete audimax\n"
        "/cafete nk 26.09.\n"
        "/abbr MV\n\n"
        "For configuration use /get and /set.")


@ComHandlerFunc("status")
def status(bot, update):
    from mensabot.bot.api import health

    bot.sendMessage(chat_id=update.message.chat_id, text= \
        ("Everything is fine! 😊\n" if health.check(request=False)[1] == health.success_status else
         "Uhoh. There seem to be some problems! 😕\n") +
        "You can also check my uptime status online:\n"
        "http://status.mensabot.niko.voidptr.de")


@ComHandlerFunc("abbr")
def abbr(bot, update):
    args = get_args(update)
    abbrs = get_abbr()
    if not args or not args[0]:
        bot.sendMessage(chat_id=update.message.chat_id, text=abbrs, parse_mode=ParseMode.MARKDOWN)
        return
    found = [abbr for abbr in abbrs.split("\n") if abbr.startswith("`" + args[0])]
    if not found:
        bot.sendMessage(chat_id=update.message.chat_id, text="Abbreviation '{}' not found.".format(args[0]))
    else:
        bot.sendMessage(chat_id=update.message.chat_id, text="\n".join(found), parse_mode=ParseMode.MARKDOWN)
