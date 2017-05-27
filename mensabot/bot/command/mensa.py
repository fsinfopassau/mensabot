from datetime import date, datetime, timedelta

from telegram import ParseMode

from mensabot.bot.ext import updater
from mensabot.bot.util import ComHandlerFunc, chat_record, get_args
from mensabot.format import get_mensa_diff_formatted, get_mensa_formatted
from mensabot.mensa import PRICES_CATEGORIES, get_next_menu_date
from mensabot.parse import parse_loc_date

mensa_notifications = set()

@ComHandlerFunc("mensa")
def mensa(bot, update):
    try:
        loc, dt = parse_loc_date(get_args(update))
        if not dt:
            dt = datetime.now()
            if dt.hour > 15:
                dt += timedelta(days=1)
            dt = get_next_menu_date(dt)
        if loc:
            raise ValueError("Currently, only default location is supported")
    except ValueError as e:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="%s. Try 'today', 'tomorrow', 'Friday' or a date." % e)
        return

    if dt.date() == date.today():
        mensa_notifications.add(update.message.chat_id)

    with chat_record(update) as chat:
        send_menu_message(dt, chat, update.message.chat_id)


def send_menu_message(time, chat, chat_id):
    updater.bot.sendMessage(
        chat_id=chat_id,
        text=get_mensa_formatted(
            time,
            template=chat.template if chat else None,
            locale=chat.locale if chat else None,
            price_category=PRICES_CATEGORIES[chat.price_category if chat else 0]),
        parse_mode=ParseMode.MARKDOWN)


def send_menu_update(date, diff, chat, chat_id):
    updater.bot.sendMessage(
        chat_id=chat_id,
        text=get_mensa_diff_formatted(
            date, diff,
            template=chat.template if chat else None,
            locale=chat.locale if chat else None,
            price_category=PRICES_CATEGORIES[chat.price_category if chat else 0]),
        parse_mode=ParseMode.MARKDOWN)
