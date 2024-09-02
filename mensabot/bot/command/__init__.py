import importlib

from telegram import ParseMode
from telegram.ext import Filters, MessageHandler

from mensabot.bot.ext import dispatcher
from mensabot.bot.util import ComHandlerFunc, get_args
from mensabot.format import get_abbr

__all__ = ["cafete", "config", "mensa", "debug"]


def init_commands():
    # commands are automatically added when their decorator is parsed,
    # so just make sure the modules are loaded
    for mod in __all__:
        importlib.import_module("." + mod, __name__)

    def unknown(update, ctx):
        ctx.bot.send_message(chat_id=update.message.chat_id, text="Sorry, I didn't understand that command.")

    unknown_handler = MessageHandler(Filters.command, unknown)
    dispatcher.add_handler(unknown_handler)


@ComHandlerFunc("start")
def start(update, ctx):
    ctx.bot.sendMessage(chat_id=update.message.chat_id, text= \
        "MensaBot Passau to your service. "
        "Try /mensa or /cafete and add a time or location if you want.")


@ComHandlerFunc("help")
def help(update, ctx):
    ctx.bot.sendMessage(chat_id=update.message.chat_id, text= \
        "MensaBot Passau to your service. "
        "Try /mensa or /cafete and add a time or location if you want. "
        "Examples:\n"
        "/mensa tomorrow\n"
        "/cafete audimax\n"
        "/cafete nk 26.09.\n"
        "/abbr MV\n\n"
        "For configuration use /get and /set.")


@ComHandlerFunc("abbr")
def abbr(update, ctx):
    args = get_args(update)
    abbrs = get_abbr()
    if not args or not args[0]:
        ctx.bot.sendMessage(chat_id=update.message.chat_id, text=abbrs, parse_mode=ParseMode.MARKDOWN)
        return
    found = [abbr for abbr in abbrs.split("\n") if abbr.startswith("`" + args[0])]
    if not found:
        ctx.bot.sendMessage(chat_id=update.message.chat_id, text="Abbreviation '{}' not found.".format(args[0]))
    else:
        ctx.bot.sendMessage(chat_id=update.message.chat_id, text="\n".join(found), parse_mode=ParseMode.MARKDOWN)
