import os
from datetime import datetime

import sh

from mensabot import mensa
from mensabot.bot.command.mensa import mensa_notifications, send_menu_update
from mensabot.bot.util import chat_record
from mensabot.config_default import MENU_STORE
from mensabot.mensa import MENU_TYPES
from mensabot.mensa_menu import Change, generate_diff


def commit_diff(week, old, new):
    git = sh.git.bake(_cwd=MENU_STORE)

    if not os.path.isdir(os.path.join(MENU_STORE, ".git")):
        git.init()
        git.remote.add("origin", "git@github.com:N-Coder/mensabot-crawler.git")

    git.add("%s.csv" % week)
    git.commit(m="updates from %s" % datetime.now())
    # git.push()


def _diff_order_key(diff: Change):
    wg = diff.to_dish.warengruppe if diff.to_dish else diff.from_dish.warengruppe
    return MENU_TYPES.index(wg[0]), wg


def notify_diff(week, old, new):
    diff = generate_diff(old, new)
    diff = sorted(diff, key=_diff_order_key)
    # print_diff(diff)

    for chat_id in mensa_notifications:
        with chat_record(chat_id) as chat:
            send_menu_update(datetime.now(), diff, chat, chat_id)


def install_listener():
    mensa.change_listeners.append(notify_diff)
    mensa.change_listeners.append(commit_diff)
