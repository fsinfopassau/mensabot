import datetime as dtm

from telegram import ParseMode
from telegram.error import BadRequest

from mensabot.bot.ext import updater
from mensabot.bot.util import ComHandlerFunc, chat_record, ensure_date, get_args
from mensabot.format import get_mensa_diff_formatted, get_mensa_formatted
from mensabot.mensa import PRICES_CATEGORIES, get_next_mensa_open
from mensabot.parse import parse_loc_date

notifications = []
notifications_date = dtm.date.today()


@ComHandlerFunc("mensa")
def mensa(update, ctx):
    try:
        loc, dt = parse_loc_date(get_args(update))
        if not dt:
            (open, close, dt, offset), menu = get_next_mensa_open()
        if loc:
            raise ValueError("Currently, only default location is supported")
    except ValueError as e:
        ctx.bot.sendMessage(chat_id=update.message.chat_id,
                        text="%s. Try 'today', 'tomorrow', 'Friday' or a date." % e)
        return

    with chat_record(update) as chat:
        send_menu_message(dt, chat, update.message.chat_id)


def send_menu_message(dt, chat, chat_id):
    return updater.bot.sendMessage(
        chat_id=chat_id,
        text=get_mensa_formatted(
            dt,
            template=chat.template if chat else None,
            locale=chat.locale if chat else None,
            price_category=PRICES_CATEGORIES[chat.price_category if chat else 0]),
        disable_notification=(not chat.push_sound) if chat else False,
        parse_mode=ParseMode.MARKDOWN,
        callback=notifications.append if ensure_date(dt) == notifications_date else None)


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
        price_category=PRICES_CATEGORIES[chat.price_category if chat else 0],
        now=msg.date)
    if text != msg.text:
        try:
            updater.bot.editMessageText(
                message_id=msg.message_id, chat_id=msg.chat_id,
                text=text, parse_mode=ParseMode.MARKDOWN)
        except BadRequest as e:
            if str(e.message).startswith("Message is not modified"):
                pass
            else:
                raise
