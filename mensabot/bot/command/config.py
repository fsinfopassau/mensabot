from contextlib import ExitStack, closing
from datetime import datetime

from mensabot.bot.util import ComHandlerFunc, get_args
from mensabot.db import CHATS, SQL_ENGINE
from mensabot.format import check_legal_template
from mensabot.mensa import PRICES_CATEGORIES
from mensabot.parse import LANG


def check_price_category(x):
    idx = PRICES_CATEGORIES.index(x)
    if idx < 0:
        raise ValueError("Unknown price category '%s'. Try 'stud', 'bed' or 'gast'." % x)
    return idx


def check_locale(x):
    idx = LANG.index(x)
    if idx < 0:
        raise ValueError("Unknown locale '%s'. Try 'de' or 'en'." % x)
    return x


def check_notification_time(x):
    try:
        return datetime.strptime(x, "%H:%M:%S").time()
    except ValueError:
        try:
            return datetime.strptime(x, "%H:%M").time()
        except ValueError as e:
            raise ValueError("Could not parse time '%s', try e.g. '11:15'. (reason was %s)" % (x, e))


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

    try:
        arg = CONFIG_OPTIONS[args[0]](args[1])
    except KeyError:
        bot.sendMessage(chat_id=update.message.chat_id, text="'{}' is not a valid config option. Try {}.".format(
            args[0], ", ".join(CONFIG_OPTIONS.keys())
        ))
        return
    except ValueError as e:
        bot.sendMessage(chat_id=update.message.chat_id, text=str(e))
        return

    with ExitStack() as s:
        val = {args[0]: arg}
        conn = s.enter_context(closing(SQL_ENGINE.connect()))
        res = s.enter_context(closing(conn.execute(
            CHATS.update().values(**val).where(CHATS.c.id == id)
        )))
        if res.rowcount != 1:
            s.enter_context(closing(conn.execute(
                CHATS.insert().values(id=id, **val)
            )))
    bot.sendMessage(chat_id=update.message.chat_id, text="Updated %s to '%s'." % (args[0], args[1]))
