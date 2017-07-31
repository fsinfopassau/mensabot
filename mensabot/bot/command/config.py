import datetime as dtm

from mensabot.bot.util import ComHandlerFunc, get_args, chat_record
from mensabot.db import CHATS, connection
from mensabot.format import check_legal_template
from mensabot.mensa import PRICES_CATEGORIES
from mensabot.parse import LANG


def check_price_category(x):
    if x is None:
        return 0
    idx = PRICES_CATEGORIES.index(x)
    if idx < 0:
        raise ValueError("Unknown price category '%s'. Try 'stud', 'bed' or 'gast'." % x)
    return idx


def check_locale(x):
    if x is None:
        return None
    idx = LANG.index(x)
    if idx < 0:
        raise ValueError("Unknown locale '%s'. Try 'de' or 'en'." % x)
    return x


def check_notification_time(x):
    if x is None:
        return None
    try:
        return dtm.datetime.strptime(x, "%H:%M:%S").time()
    except ValueError:
        try:
            return dtm.datetime.strptime(x, "%H:%M").time()
        except ValueError as e:
            raise ValueError("Could not parse time '%s', try e.g. '11:15'. (reason was %s)" % (x, e))


def check_boolean(x):
    if x is None:
        return None
    x = str(x).lower()
    if x in ['true', '1', 't', 'y', 'yes', 'j', 'ja']:
        return True
    elif x in ['false', '0', 'f', 'n', 'no', 'nein']:
        return False
    else:
        raise ValueError("Could not parse boolean '%s'" % x)


CONFIG_RESET = ["none", "null", "default", "reset", "-", "/"]

CONFIG_OPTIONS = {
    "template": check_legal_template,
    "price_category": check_price_category,
    "locale": check_locale,
    "push_time": check_notification_time,  # time for pushing the menu notifications
    "push_sound": check_boolean,  # muted menu notifications
    "notify_change": check_boolean,  # change notifications
    "notify_change_sound": check_boolean,  # muted change notifications
    "update_menu": check_boolean,  # menu editing
}


@ComHandlerFunc("set")
def set_config(bot, update):
    id = update.message.chat.id
    args = get_args(update)
    if len(args) != 2:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Could not parse args '%s'. Enter a config option and a new value." % " ".join(args))
        return
    fun, arg = args

    try:
        if arg.lower() in CONFIG_RESET:
            arg = CHATS.columns.get(fun).server_default.arg
        else:
            arg = CONFIG_OPTIONS[fun](arg)
    except KeyError:
        bot.sendMessage(chat_id=update.message.chat_id, text="'{}' is not a valid config option. Try {}.".format(
            fun, ", ".join(CONFIG_OPTIONS.keys())
        ))
        return
    except ValueError as e:
        bot.sendMessage(chat_id=update.message.chat_id, text=str(e))
        return

    with connection() as (conn, execute):
        val = {fun: arg}
        res = execute(
            CHATS.update().values(**val).where(CHATS.c.id == id)
        )
        if res.rowcount != 1:
            execute(
                CHATS.insert().values(id=id, **val)
            )
    bot.sendMessage(chat_id=update.message.chat_id, text="Updated %s to '%s'." % (fun, arg))


@ComHandlerFunc("get")
def get_config(bot, update):
    id = update.message.chat.id
    args = get_args(update)
    if len(args) > 1:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="Could not parse args '%s'. Enter the name of a config option." % " ".join(args))
        return

    with chat_record(id) as res:
        if len(args) == 1 and args[0]:
            fun, = args
            if fun not in CONFIG_OPTIONS.keys():
                bot.sendMessage(chat_id=update.message.chat_id,
                                text="'{}' is not a valid config option. Try {}.".format(
                                    fun, ", ".join(CONFIG_OPTIONS.keys())
                                ))
            else:
                bot.sendMessage(chat_id=update.message.chat_id, text="%s: %s" % (fun, res[fun]))
        else:
            bot.sendMessage(chat_id=update.message.chat_id,
                            text="\n".join("%s: %s" % (fun, res[fun]) for fun in CONFIG_OPTIONS.keys()))
