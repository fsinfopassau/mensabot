import logging
import logging.config
import os

import yaml

ECHO_SQL = False


def configure_logging():
    # logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
    os.makedirs("log", exist_ok=True)
    with open("logging.yaml", "r") as f:
        logging.config.dictConfig(yaml.load(f))


from .config import *

IS_DEVELOPMENT = DEPLOY_MODE == "DEVELOPMENT"
TELEGRAM_TOKEN = TOKENS[DEPLOY_MODE]
MENU_STORE = os.path.abspath(MENU_STORE)
