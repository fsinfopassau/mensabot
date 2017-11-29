import datetime as dtm
import os

import sh
from mensabot import mensa as mensa_api
from mensabot.bot.command import mensa as mensa_cmd
from mensabot.bot.command.mensa import edit_menu_message, send_menu_update
from mensabot.bot.tasks import SCHED
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
    git.commit(m="updates from %s" % dtm.datetime.now())
    # git.push()


def notify_diff(week, old, new):
    dedup = set()

    diff = generate_diff(old, new)
    diff = [d for d in diff if d.dish().datum == mensa_cmd.notifications_date]
    diff = sorted(diff, key=lambda d: (MENU_TYPES.index(d.dish().warengruppe[0]), d.dish().warengruppe))

    for msg in mensa_cmd.notifications:
        with chat_record(msg) as chat:
            if not chat:
                continue
            if chat.notify_change and chat.id not in dedup:
                dedup.add(chat.id)
                send_menu_update(mensa_cmd.notifications_date, diff, chat)
            if chat.update_menu:
                edit_menu_message(mensa_cmd.notifications_date, msg, new, chat)


def install_listener():
    mensa_api.change_listeners.append(lambda *args, **kwargs: SCHED.enter(0, 150, notify_diff, args, kwargs))
    mensa_api.change_listeners.append(lambda *args, **kwargs: SCHED.enter(0, 150, commit_diff, args, kwargs))
