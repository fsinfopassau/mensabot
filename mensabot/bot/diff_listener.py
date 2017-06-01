import os
from datetime import datetime

import sh

from mensabot import mensa
from mensabot.bot.command.mensa import mensa_notifications, send_menu_update
from mensabot.bot.util import chat_record
from mensabot.config_default import MENU_STORE
from mensabot.mensa import MENU_TYPES
from mensabot.mensa_menu import generate_diff


def commit_diff(week, old, new):
    git = sh.git.bake(_cwd=MENU_STORE)

    if not os.path.isdir(os.path.join(MENU_STORE, ".git")):
        git.init()
        git.remote.add("origin", "git@github.com:N-Coder/mensabot-crawler.git")

    git.add("%s.csv" % week)
    git.commit(m="updates from %s" % datetime.now())
    # git.push()


def notify_diff(week, old, new):
    now = datetime.now()
    today = now.date()

    diff = generate_diff(old, new)
    diff = [d for d in diff if d.dish().datum == today]
    diff = sorted(diff, key=lambda d: (MENU_TYPES.index(d.dish().warengruppe[0]), d.dish().warengruppe))

    for chat_id in mensa_notifications:
        with chat_record(chat_id) as chat:
            send_menu_update(now, diff, chat, chat_id)


def install_listener():
    mensa.change_listeners.append(notify_diff)
    mensa.change_listeners.append(commit_diff)
