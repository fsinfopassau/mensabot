from telegram.ext import Updater

from mensabot.config import TELEGRAM_TOKEN

updater = Updater(token=TELEGRAM_TOKEN)
dispatcher = updater.dispatcher
