from mensabot.bot.util import ComHandlerFunc
from mensabot.format import get_version


@ComHandlerFunc("version")
def version(update, ctx):
    ctx.bot.sendMessage(chat_id=update.message.chat_id, text=get_version())


def DbgComHandlerFunc(command, **kwargs):
    def func_decorator(func):
        def func_wrapper(update, ctx):
            if update.message.chat_id != 114998496:
                ctx.bot.sendMessage(chat_id=update.message.chat_id, text="You are not allowed to do this!")
            else:
                func(update, ctx)

        return ComHandlerFunc("dbg_" + command, **kwargs)(func_wrapper)

    return func_decorator


@DbgComHandlerFunc("scheduler")
def dump_schedule(update, ctx):
    from mensabot.bot.tasks import SCHED
    ctx.bot.sendMessage(chat_id=update.message.chat_id,
                    text="Scheduler jobs:\n" + "\n\n".join(str(job) for job in SCHED.queue))


@DbgComHandlerFunc("notifications")
def dump_notifications(update, ctx):
    from mensabot.bot.command import mensa
    ctx.bot.sendMessage(chat_id=update.message.chat_id,
                    text="Menu messages for {:%Y-%m-%d}:\n{}".format(
                        mensa.notifications_date,
                        "\n\n".join(
                            str({'message_id': msg.message_id, 'date': msg.date, 'chat': msg.chat.to_dict()})
                            for msg in mensa.notifications)
                    ))


@DbgComHandlerFunc("settrace")
def settrace(update, ctx):
    import pydevd
    ctx.bot.sendMessage(chat_id=update.message.chat_id, text="Calling pydevd.settrace...")
    pydevd.settrace('localhost', port=6548, stdoutToServer=True, stderrToServer=True)
    ctx.bot.sendMessage(chat_id=update.message.chat_id, text="breakpoint completed")


@DbgComHandlerFunc("stoptrace")
def settrace(update, ctx):
    import pydevd
    ctx.bot.sendMessage(chat_id=update.message.chat_id, text="Calling pydevd.stoptrace")
    pydevd.stoptrace()
