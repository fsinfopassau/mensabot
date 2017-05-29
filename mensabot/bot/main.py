import logging

from mensabot.bot.command import init_commands
from mensabot.bot.diff_listener import install_listener
from mensabot.bot.ext import updater
from mensabot.bot.tasks import run_sched
from mensabot.format import get_version

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
# logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.INFO)
logging.getLogger("telegram.bot").setLevel(logging.INFO)
logging.getLogger("sh").setLevel(logging.INFO)
logger = logging.getLogger("mensabot.bot")


def main():
    init_commands()
    install_listener()
    updater.start_polling()
    logger.info("{} listening...".format(get_version()))
    run_sched()


if __name__ == "__main__":
    main()
