import sys
from pkgutil import get_data

import dateparser
from dateparser import DateDataParser

LANG = ['de', 'en']
DATEPARSER_SETTINGS = {'PREFER_DATES_FROM': 'future'}


def __inject_alt_langs():
    """
    Make the lookup function for dateparser language definition files also look in mensabot.languages  
    """

    def get_data2(package, resource):
        if package == "data":
            try:
                data = get_data("mensabot", "languages/{}".format(resource))
                if data:
                    return data
            except:
                pass
        return get_data(package, resource)

    DateDataParser.language_loader = None
    sys.modules['dateparser.languages.loader'].get_data = get_data2
    sys.modules['dateparser.utils'].get_data = get_data2


__inject_alt_langs()


def parse_loc_date(s):
    tokens = s.split(" ")
    # check whether location is first word
    loc = parse_loc(tokens[0])
    if loc:
        return loc, parse_date(tokens[1:])
    # or last word
    loc = parse_loc(tokens[-1])
    if loc:
        return loc, parse_date(tokens[:-1])
    # otherwise, it's probably only a date
    return None, parse_date(tokens)


def parse_loc(s):
    if not s or s == ['']:
        return None
    if not isinstance(s, str):
        s = " ".join(s)
    s = s.lower()

    if s == "am" or s.startswith("audi"):
        return "audimax"
    elif s in ["m", "mc", "mensa"] or s.startswith("mensac"):
        return "mensacafete"
    elif s in ["nk", "kk", "kc", "kuca", "kuka"] or s.startswith("niko") or s.startswith("kul"):
        return "nikolakloster"
    elif s in ["w", "wi", "ww", "wiwi"]:
        return "wiwi"
    elif s == "essen" or s.startswith("mensae"):
        return "mensaessen"

    return None


def parse_date(s):
    if not s or s == ['']:
        return None
    if not isinstance(s, str):
        s = " ".join(s)
    if s.startswith("+"):
        s = "in " + s[1:]
    if s.startswith("-"):
        s = "vor " + s[1:]

    v = dateparser.parse(s, languages=LANG, settings=DATEPARSER_SETTINGS)
    if not v:
        raise ValueError("Could not parse date '%s'" % s)
    return v
