import logging
import os
from datetime import datetime

import sh

from mensabot import mensa
from mensabot.bot.command import init_commands
from mensabot.bot.command.mensa import mensa_notifications, send_menu_update
from mensabot.bot.ext import updater
from mensabot.bot.tasks import run_sched
from mensabot.bot.util import chat_record
from mensabot.config import MENU_STORE
from mensabot.format import get_version
from mensabot.mensa_menu import generate_diff

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.DEBUG)
# logging.getLogger("requests.packages.urllib3.connectionpool").setLevel(logging.INFO)
logging.getLogger("telegram.bot").setLevel(logging.INFO)
logger = logging.getLogger("mensabot.bot")


# TODO move to another location

def commit_diff(week, old, new):
    git = sh.git.bake(_cwd=MENU_STORE)

    if not os.path.isdir(MENU_STORE):
        os.mkdir(MENU_STORE)
        git.init()
        git.remote.add("origin", "git@github.com:N-Coder/mensabot-crawler.git")

    git.add("%s.csv" % week)
    git.commit(m="updates from %s" % datetime.now())
    # git.push()


def notify_diff(week, old, new):
    diff = generate_diff(old, new)
    # print_diff(diff)

    for chat_id in mensa_notifications:
        with chat_record(chat_id) as chat:
            send_menu_update(datetime.now(), diff, chat, chat_id)


mensa.change_listeners.append(notify_diff)
mensa.change_listeners.append(commit_diff)


def main():
    init_commands()
    updater.start_polling()
    logger.info("{} listening...".format(get_version()))
    run_sched()


if __name__ == "__main__":
    main()
