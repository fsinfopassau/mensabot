import logging
from threading import Thread

from mensabot.bot.api import app
from mensabot.bot.command import init_commands
from mensabot.bot.diff_listener import install_listener
from mensabot.bot.ext import updater
from mensabot.bot.tasks import run_sched
from mensabot.config_default import configure_logging
from mensabot.format import get_version

configure_logging()
logger = logging.getLogger("mensabot.bot")


def main():
    logger.info("Starting web server")
    Thread(target=app.run, name="flask", daemon=True, kwargs={"debug": True, "use_reloader": False}).start()
    logger.info("Starting telegram bot")
    init_commands()
    install_listener()
    updater.start_polling()
    logger.info("{} listening...".format(get_version()))
    run_sched()


if __name__ == "__main__":
    main()
