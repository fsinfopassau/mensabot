import datetime as dtm
import logging

from telegram import Bot, Message
from telegram.error import InvalidToken, RetryAfter, TimedOut, Unauthorized
from telegram.ext import Updater
from telegram.utils.request import Request

from mensabot.config_default import TELEGRAM_TOKEN
from mensabot.db import CHATS, connection

access_logger = logging.getLogger("mensabot.access")


class MensaBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_update = dtm.datetime.fromtimestamp(0)

    def get_updates(self, *args, **kwargs):
        try:
            updates = super().get_updates(*args, **kwargs)
            self.last_update = dtm.datetime.now()
        except TimedOut:
            self.last_update = dtm.datetime.now()
            raise

        for update in updates:
            access_logger.info("Received update: %s" % update.to_json())
        return updates

    def send_message(self, *args, **kwargs):
        from mensabot.bot.tasks import SCHED

        # TODO use telegram-bot MessageQueue for rate limiting
        # https://github.com/python-telegram-bot/python-telegram-bot/wiki/Avoiding-spam-limits
        retries = kwargs.pop("__sendMessage_retries", 0)
        cb = kwargs.pop("callback", None)
        if not cb:
            cb = lambda x: None

        try:
            access_logger.debug("Sending message (%s, %s)" % (args, kwargs))
            msg = super().send_message(*args, **kwargs)
            access_logger.info("Message sent: %s" % (msg.to_json() if isinstance(msg, Message) else msg))
            cb(msg)
            return msg

        except (InvalidToken, BadRequest) as e:
            cb(e)
            raise

        except RetryAfter as e:  # schedule retry after e.retry_after
            kwargs["__sendMessage_retries"] = retries + 1
            logger.warning("Message rate limit exceeded, retrying later.", exc_info=e)
            id = SCHED.enter(e.retry_after, 120, updater.bot.sendMessage, kwargs=kwargs)
            return e, id

        except (TimedOut, NetworkError) as e:  # handle slow connection problems and handle other connection problems
            if retries <= 8:
                kwargs["__sendMessage_retries"] = retries + 1
                delay = 2 ** retries
                logger.warning("Network problems, retrying in %d seconds." % delay, exc_info=e)
                id = SCHED.enter(delay, 120, updater.bot.sendMessage, kwargs=kwargs)
                return e, id
            else:
                cb(e)
                raise

        except ChatMigrated as e:  # the chat_id of a group has changed, use e.new_chat_id instead
            logger.info("Chat migrated, updating database and retrying.", exc_info=e)
            with connection() as (conn, execute):
                execute(
                    CHATS.update().where(CHATS.c.id == kwargs["chat_id"]).values(id=e.new_chat_id)
                )
            kwargs["chat_id"] = e.new_chat_id
            id = SCHED.enter(1, 120, updater.bot.sendMessage, kwargs=kwargs)
            return e, id

        except Unauthorized as e:  # remove update.message.chat_id from conversation list
            logger.info("User stopped bot, removing from database.", exc_info=e)
            with connection() as (conn, execute):
                execute(
                    CHATS.delete().where(CHATS.c.id == kwargs["chat_id"])
                )
            cb(e)
            raise

    def edit_message_text(self, *args, **kwargs):
        access_logger.debug("Editing message text (%s, %s)" % (args, kwargs))
        msg = super().edit_message_text(*args, **kwargs)
        access_logger.info("Message text edited: %s" % (msg.to_json() if isinstance(msg, Message) else msg))
        return msg

    getUpdates = get_updates
    sendMessage = send_message
    editMessageText = edit_message_text


logger = logging.getLogger("mensabot.ext")
request = Request(con_pool_size=8)
bot = MensaBot(token=TELEGRAM_TOKEN, request=request)
updater = Updater(bot=bot)
dispatcher = updater.dispatcher

# TODO add error handler
# https://github.com/python-telegram-bot/python-telegram-bot/wiki/Exception-Handling
