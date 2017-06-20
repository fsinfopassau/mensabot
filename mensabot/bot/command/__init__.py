import importlib

from telegram import ParseMode

from mensabot.bot.util import ComHandlerFunc, get_args
from mensabot.format import get_abbr, get_version

__all__ = ["cafete", "config", "mensa"]


def init_commands():
    # commands are automatically added when their decorator is parsed,
    # so just make sure the modules are loaded
    for mod in __all__:
        importlib.import_module("." + mod, __name__)


@ComHandlerFunc("start")
def start(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text= \
        "MensaBot Passau to your service. "
        "Try /mensa or /cafete and add a time or location if you want.")


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


@ComHandlerFunc("version")
def version(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=get_version())


@ComHandlerFunc("scheduler")
def dump_schedule(bot, update):
    if update.message.chat_id != 114998496:
        bot.sendMessage(chat_id=update.message.chat_id, text="You are not allowed to do this!")
    from mensabot.bot.tasks import SCHED
    bot.sendMessage(chat_id=update.message.chat_id, text="\n".join(str(job) for job in SCHED.queue))


@ComHandlerFunc("settrace")
def settrace(bot, update):
    if update.message.chat_id != 114998496:
        bot.sendMessage(chat_id=update.message.chat_id, text="You are not allowed to do this!")
    import pydevd
    pydevd.settrace('localhost', port=6548, stdoutToServer=True, stderrToServer=True)


@ComHandlerFunc("stoptrace")
def settrace(bot, update):
    if update.message.chat_id != 114998496:
        bot.sendMessage(chat_id=update.message.chat_id, text="You are not allowed to do this!")
    import pydevd
    pydevd.stoptrace()
