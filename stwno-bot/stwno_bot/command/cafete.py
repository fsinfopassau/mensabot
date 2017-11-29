import datetime as dtm

from mensabot.bot.util import ComHandlerFunc, chat_record, get_args
from mensabot.format import get_open_formatted
from mensabot.mensa import LOCATIONS
from mensabot.parse import parse_loc_date
from telegram import ParseMode


@ComHandlerFunc("cafete")
def cafete(bot, update):
    try:
        loc, dt = parse_loc_date(get_args(update))
        if not dt:
            dt = dtm.datetime.now()
        if not loc:
            loc = "mensacafete"
    except ValueError as e:
        k = list(LOCATIONS.keys())
        s = " or ".join([", ".join(k[:-1]), k[-1]])
        bot.sendMessage(chat_id=update.message.chat_id,
                        text="%s. Try 'today', 'tomorrow', 'Friday', any date or the locations %s." % (e, s))
        return

    with chat_record(update) as chat:
        bot.sendMessage(chat_id=update.message.chat_id,
                        text=get_open_formatted(
                            loc, dt,
                            template=chat.template if chat else None,
                            locale=chat.locale if chat else None),
                        parse_mode=ParseMode.MARKDOWN)
