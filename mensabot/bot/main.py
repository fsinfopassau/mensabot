import logging

from mensabot.bot.command import init_commands
from mensabot.bot.ext import updater
from mensabot.bot.tasks import run_sched, schedule_clear_cache, schedule_notification
from mensabot.format import get_version

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
# logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.INFO)
logging.getLogger("telegram.bot").setLevel(logging.INFO)
logger = logging.getLogger("mensabot.bot")


def main():
    init_commands()
    updater.start_polling()
    logger.info("{} listening...".format(get_version()))
    schedule_notification()
    schedule_clear_cache()
    logger.debug("Handing over to scheduler")
    run_sched()


if __name__ == "__main__":
    main()
