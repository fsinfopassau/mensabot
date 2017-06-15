import traceback
from contextlib import contextmanager

from telegram import Message, MessageEntity, ParseMode, Update
from telegram.ext import CommandHandler

from mensabot.bot.ext import dispatcher
from mensabot.db import CHATS, connection


@contextmanager
def chat_record(id):
    if isinstance(id, Message):
        id = id.chat.id
    elif isinstance(id, Update):
        id = id.message.chat.id
    elif not isinstance(id, int):
        raise ValueError("ID '%s' is not an int." % id)
    with connection() as (conn, execute):
        res = execute(CHATS.select(CHATS.c.id == id))
        row = res.fetchone()
        yield row


def get_args(update):
    text = update.message.text
    for ent in update.message.entities:
        if ent.type == MessageEntity.BOT_COMMAND:
            text = text[:ent.offset] + text[ent.offset + ent.length:]
    return text.strip().split(" ")


def ComHandlerFunc(command, **kwargs):
    def func_decorator(func):
        def func_wrapper(bot, update):
            try:
                func(bot, update)
            except:
                traceback.print_exc()
                bot.sendMessage(
                    chat_id=update.message.chat_id, text="Master, I failed! 😢", parse_mode=ParseMode.MARKDOWN)
                raise

        handler = CommandHandler(command, func_wrapper, **kwargs)
        dispatcher.add_handler(handler)
        func_wrapper.handler = handler
        return func_wrapper

    return func_decorator
