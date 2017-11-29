import logging

from stwno_bot.api import start_app
from stwno_bot.command import init_commands
from stwno_bot.config import configure_logging
from stwno_bot.diff_listener import install_listener
from stwno_bot.ext import updater
from stwno_bot.tasks import run_sched
from stwno_cmds.util import get_version

configure_logging()
logger = logging.getLogger("mensabot.bot")


def main():
    logger.info("Starting web server")
    start_app()
    logger.info("Starting telegram bot")
    init_commands()
    install_listener()
    updater.start_polling()
    logger.info("{} listening...".format(get_version()))
    run_sched()


if __name__ == "__main__":
    main()
