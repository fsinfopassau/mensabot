from telegram.ext import Updater

from mensabot.config_default import TELEGRAM_TOKEN

updater = Updater(token=TELEGRAM_TOKEN)
dispatcher = updater.dispatcher
