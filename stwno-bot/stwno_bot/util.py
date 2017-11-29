import logging
import sys

import requests
from telegram import MessageEntity, ParseMode
from telegram.ext import CommandHandler


def get_args(update):
    text = update.message.text
    for ent in update.message.entities:
        if ent.type == MessageEntity.BOT_COMMAND:
            text = text[:ent.offset] + text[ent.offset + ent.length:]
    return text.strip().split(" ")


com_logger = logging.getLogger("mensabot.bot.command")


def ComHandlerFunc(command, **kwargs):
    # TODO use pass_args param
    def func_decorator(func):
        def func_wrapper(bot, update):
            try:
                func(bot, update)
            except:
                com_logger.error("Command /%s failed", command, exc_info=True)
                if sys.exc_info()[0] in [requests.exceptions.ConnectionError, requests.exceptions.Timeout]:
                    bot.sendMessage(
                        chat_id=update.message.chat_id, text="I got network problems, please try again later! 😢",
                        parse_mode=ParseMode.MARKDOWN)
                else:
                    bot.sendMessage(
                        chat_id=update.message.chat_id, text="Master, I failed! 😢", parse_mode=ParseMode.MARKDOWN)
                raise

        handler = CommandHandler(command, func_wrapper, **kwargs)
        dispatcher.add_handler(handler)
        func_wrapper.handler = handler
        return func_wrapper

    return func_decorator
