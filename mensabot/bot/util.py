import traceback
from contextlib import ExitStack, closing, contextmanager

from telegram import MessageEntity, ParseMode
from telegram.ext import CommandHandler

from mensabot.bot.ext import dispatcher
from mensabot.db import CHATS, SQL_ENGINE


@contextmanager
def chat_record(id):
    if not isinstance(id, int):  # object is a telegram update
        id = id.message.chat.id
    with ExitStack() as s:
        conn = s.enter_context(closing(SQL_ENGINE.connect()))
        res = s.enter_context(closing(conn.execute(CHATS.select(CHATS.c.id == id))))
        yield res.fetchone()


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
