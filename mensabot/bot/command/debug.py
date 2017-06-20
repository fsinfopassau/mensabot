from mensabot.bot.util import ComHandlerFunc
from mensabot.format import get_version


@ComHandlerFunc("version")
def version(bot, update):
    bot.sendMessage(chat_id=update.message.chat_id, text=get_version())


def DbgComHandlerFunc(command, **kwargs):
    def func_decorator(func):
        def func_wrapper(bot, update):
            if update.message.chat_id != 114998496:
                bot.sendMessage(chat_id=update.message.chat_id, text="You are not allowed to do this!")
            else:
                func(bot, update)

        return ComHandlerFunc("dbg_" + command, **kwargs)(func_wrapper)

    return func_decorator


@DbgComHandlerFunc("scheduler")
def dump_schedule(bot, update):
    from mensabot.bot.tasks import SCHED
    bot.sendMessage(chat_id=update.message.chat_id, text="\n\n".join(str(job) for job in SCHED.queue))


@DbgComHandlerFunc("notifications")
def dump_notifications(bot, update):
    from mensabot.bot.command.mensa import mensa_notifications
    bot.sendMessage(chat_id=update.message.chat_id, text="\n".join(str(msg) for msg in mensa_notifications))


@DbgComHandlerFunc("settrace")
def settrace(bot, update):
    import pydevd
    bot.sendMessage(chat_id=update.message.chat_id, text="Calling pydevd.settrace...")
    pydevd.settrace('localhost', port=6548, stdoutToServer=True, stderrToServer=True)
    bot.sendMessage(chat_id=update.message.chat_id, text="breakpoint completed")


@DbgComHandlerFunc("stoptrace")
def settrace(bot, update):
    import pydevd
    bot.sendMessage(chat_id=update.message.chat_id, text="Calling pydevd.stoptrace")
    pydevd.stoptrace()
