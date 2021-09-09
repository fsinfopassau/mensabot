import logging
import logging.config
import os
import sys

import yaml

ECHO_SQL = False

API_ARGS = {"debug": False, "use_reloader": False}


def configure_api(app):
    app.config["LOGGER_NAME"] = "mensabot.bot.api"


def configure_logging():
    # logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    os.makedirs("log", exist_ok=True)
    with open("logging.yaml", "r") as f:
        logging.config.dictConfig(yaml.load(f))


sys.path.append('.')
from config import *
del sys.path[-1]

IS_DEVELOPMENT = DEPLOY_MODE == "DEVELOPMENT"
TELEGRAM_TOKEN = TOKENS[DEPLOY_MODE]
MENU_STORE = os.path.abspath(MENU_STORE)
