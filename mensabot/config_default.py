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
    os.makedirs(LOG_PATH, exist_ok=True)
    with open(LOG_CONFIG, "r") as f:
        logging.config.dictConfig(yaml.safe_load(f))

# Defaults for the config
ENABLE_WEBSERVER = False
DATABASE = 'sqlite:///mensabot.sqlite'
LOG_PATH = "./log"
LOG_CONFIG = "./logging.yaml"
#TELEGRAM_TOKEN =  # No sensible default here
MENU_STORE = "./menustore"
ENABLE_WEBSERVER = False

sys.path.insert(0, '.')
from config import *
del sys.path[0]
