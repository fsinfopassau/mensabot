from contextlib import ExitStack, closing
from datetime import datetime

from mensabot.bot.util import ComHandlerFunc, get_args
from mensabot.db import CHATS, SQL_ENGINE
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
        return LANG[0]
    idx = LANG.index(x)
    if idx < 0:
        raise ValueError("Unknown locale '%s'. Try 'de' or 'en'." % x)
    return x


def check_notification_time(x):
    if x is None:
        return None
    try:
        return datetime.strptime(x, "%H:%M:%S").time()
    except ValueError:
        try:
            return datetime.strptime(x, "%H:%M").time()
        except ValueError as e:
            raise ValueError("Could not parse time '%s', try e.g. '11:15'. (reason was %s)" % (x, e))


CONFIG_RESET = ["none", "null", "default", "reset", "-"]

CONFIG_OPTIONS = {
    "template": check_legal_template,
    "price_category": check_price_category,
    "locale": check_locale,
    "notification_time": check_notification_time,
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
            arg = None
        arg = CONFIG_OPTIONS[fun](arg)
    except KeyError:
        bot.sendMessage(chat_id=update.message.chat_id, text="'{}' is not a valid config option. Try {}.".format(
            fun, ", ".join(CONFIG_OPTIONS.keys())
        ))
        return
    except ValueError as e:
        bot.sendMessage(chat_id=update.message.chat_id, text=str(e))
        return

    with ExitStack() as s:
        val = {fun: arg}
        conn = s.enter_context(closing(SQL_ENGINE.connect()))
        res = s.enter_context(closing(conn.execute(
            CHATS.update().values(**val).where(CHATS.c.id == id)
        )))
        if res.rowcount != 1:
            s.enter_context(closing(conn.execute(
                CHATS.insert().values(id=id, **val)
            )))
    bot.sendMessage(chat_id=update.message.chat_id, text="Updated %s to '%s'." % (fun, arg))
