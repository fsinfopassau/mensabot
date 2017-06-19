from datetime import date, datetime, timedelta

from telegram import ParseMode
from telegram.error import BadRequest

from mensabot.bot.ext import updater
from mensabot.bot.util import ComHandlerFunc, chat_record, get_args
from mensabot.format import get_mensa_diff_formatted, get_mensa_formatted
from mensabot.mensa import PRICES_CATEGORIES, get_next_menu_date
from mensabot.parse import parse_loc_date

mensa_notifications = []


@ComHandlerFunc("mensa")
def mensa(bot, update):
    try:
        loc, dt = parse_loc_date(get_args(update))
        if not dt:
            dt = default_menu_date()
        if loc:
            raise ValueError("Currently, only default location is supported")
    except ValueError as e:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="%s. Try 'today', 'tomorrow', 'Friday' or a date." % e)
        return

    with chat_record(update) as chat:
        send_menu_message(dt, chat, update.message.chat_id)


def default_menu_date():
    dt = datetime.now()
    if dt.hour > 15:
        dt += timedelta(days=1)
    dt = get_next_menu_date(dt)
    return dt


def send_menu_message(dt, chat, chat_id):
    msg = updater.bot.sendMessage(
        chat_id=chat_id,
        text=get_mensa_formatted(
            dt,
            template=chat.template if chat else None,
            locale=chat.locale if chat else None,
            price_category=PRICES_CATEGORIES[chat.price_category if chat else 0]),
        disable_notification=(not chat.push_sound) if chat else False,
        parse_mode=ParseMode.MARKDOWN,
        callback=mensa_notifications.append if dt.date() == date.today() else None)


def send_menu_update(dt, diff, chat):
    text = get_mensa_diff_formatted(
        dt, diff,
        template=chat.template if chat else None,
        locale=chat.locale if chat else None,
        price_category=PRICES_CATEGORIES[chat.price_category if chat else 0])
    if text.strip():
        updater.bot.sendMessage(chat_id=chat.id, text=text, parse_mode=ParseMode.MARKDOWN,
                                disable_notification=(not chat.notify_change_sound) if chat else False)


def edit_menu_message(dt, msg, menu, chat):
    text = get_mensa_formatted(
        dt,
        template=chat.template if chat else None,
        locale=chat.locale if chat else None,
        price_category=PRICES_CATEGORIES[chat.price_category if chat else 0])
    if text != msg.text:
        try:
            updater.bot.editMessageText(
                message_id=msg.message_id, chat_id=chat.id,
                text=text, parse_mode=ParseMode.MARKDOWN)
        except BadRequest as e:
            if e.message == "Message is not modified":
                pass
            else:
                raise
