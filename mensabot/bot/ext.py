import logging

from telegram.error import *
from telegram.ext import Updater

from mensabot.config_default import TELEGRAM_TOKEN
from mensabot.db import CHATS, connection

logger = logging.getLogger("mensabot.ext")

updater = Updater(token=TELEGRAM_TOKEN)
dispatcher = updater.dispatcher

old_sm = updater.bot.sendMessage


def __sendMessage(*args, **kwargs):  # FIXME dirty implementation of callback
    from mensabot.bot.tasks import SCHED

    # convert args to kwargs
    kwargs.update(dict(zip(old_sm.__code__.co_varnames, args)))

    retries = kwargs.pop("__sendMessage_retries", 0)

    try:
        msg = old_sm(**kwargs)
        cb = kwargs.pop("callback", None)
        if cb:
            cb(msg)
        return msg

    except (InvalidToken, BadRequest) as e:
        cb = kwargs.pop("callback", None)
        if cb:
            cb(e)
        raise

    except RetryAfter as e:  # schedule retry after e.retry_after
        kwargs["__sendMessage_retries"] = retries + 1
        logger.warning("Message rate limit exceeded, retrying later.", exc_info=e)
        SCHED.enter(e.retry_after, 120, updater.bot.sendMessage, kwargs=kwargs)
        return e

    except (TimedOut, NetworkError) as e:  # handle slow connection problems and handle other connection problems
        if retries <= 8:
            kwargs["__sendMessage_retries"] = retries + 1
            delay = 2 ** retries
            logger.warning("Network problems, retrying in %d seconds." % delay, exc_info=e)
            SCHED.enter(delay, 120, updater.bot.sendMessage, kwargs=kwargs)
            return e
        else:
            cb = kwargs.pop("callback", None)
            if cb:
                cb(e)
            raise

    except ChatMigrated as e:  # the chat_id of a group has changed, use e.new_chat_id instead
        logger.warning("Chat migrated, updating database and retrying.", exc_info=e)
        with connection() as (conn, execute):
            execute(
                CHATS.update().where(CHATS.c.id == kwargs["chat_id"]).values(id=e.new_chat_id)
            )
        kwargs["chat_id"] = e.new_chat_id
        SCHED.enter(1, 120, updater.bot.sendMessage, kwargs=kwargs)
        return e

    except Unauthorized as e:  # remove update.message.chat_id from conversation list
        logger.warning("User stopped bot, removing from database.", exc_info=e)
        with connection() as (conn, execute):
            execute(
                CHATS.delete().where(CHATS.c.id == kwargs["chat_id"])
            )
        cb = kwargs.pop("callback", None)
        if cb:
            cb(e)
        raise


updater.bot.sendMessage = __sendMessage
updater.bot.send_message = __sendMessage
