import logging

logging.basicConfig(level=logging.ERROR)
logging.captureWarnings(True)

import argparse
import csv
import itertools

import requests

from stwno_api.api import CachedStwnoApi, StwnoApi
from stwno_api.institutions import Passau
from stwno_api.menu_parser import generate_diff_week, parse_dish
from stwno_cmds.format import get_menu_diff_formatted, get_menu_formatted, get_opening_times_formatted
from stwno_cmds.parse import LANG, parse_location, parse_location_date


def _parse_args(parser, args):
    parser.add_argument('--institution', '-i', action='store', default=Passau.name, nargs='?')
    parser.add_argument('--location', '-l', action='store', default=Passau.default_mensa.name, nargs='?')
    parser.add_argument('--locale', '-s', action='store', default=LANG[0], nargs='?')
    parser.add_argument('--template', '-t', action='store', default=LANG[0], nargs='?')
    parser.add_argument('--price_category', '-c', action='store', default=StwnoApi.PRICES_CATEGORIES[0], nargs='?')
    args = parser.parse_args(args).__dict__

    institution = args.pop("institution")
    if institution == Passau.name:
        institution = Passau
    else:
        raise ValueError("Unknown institution '%s'" % institution)

    location = parse_location(institution, args["location"])
    if not location:
        raise ValueError("Unknown location '%s'" % args["location"])
    else:
        args["location"] = location

    return institution, args


def mensa(args=None):
    parser = argparse.ArgumentParser(description='Get the mensa menu.')
    parser.add_argument('day/location', action='store', default=None, nargs='*')
    institution, args = _parse_args(parser, args)
    args["location"], args["day"] = parse_location_date(institution, args["day/location"])
    with requests.Session() as session:
        api = CachedStwnoApi(institution)
        api._session = lambda: session
        print(get_menu_formatted(api, **args))


def cafete(args=None):
    parser = argparse.ArgumentParser(description='Get the cafeteria opening times.')
    parser.add_argument('date/location', action='store', default=None, nargs='*')
    institution, args = _parse_args(parser, args)
    args["location"], args["dt"] = parse_location_date(institution, args["date/location"])
    with requests.Session() as session:
        api = CachedStwnoApi(institution)
        api._session = lambda: session
        print(get_opening_times_formatted(api, **args))


def diff(args=None):
    parser = argparse.ArgumentParser(description='Compare two mensa menus.')
    parser.add_argument('path', action='store', default="", nargs='?')
    parser.add_argument('old_file', action='store')
    parser.add_argument('old_hex', action='store', default="", nargs='?')
    parser.add_argument('old_mode', action='store', default="", nargs='?')
    parser.add_argument('new_file', action='store')
    parser.add_argument('new_hex', action='store', default="", nargs='?')
    parser.add_argument('new_mode', action='store', default="", nargs='?')
    args = parser.parse_args(args)

    with open(args.old_file, "r", encoding="iso8859_3") as f:
        menu1 = [parse_dish(row) for row in csv.DictReader(f.readlines(), delimiter=';')]
    with open(args.new_file, "r", encoding="iso8859_3") as f:
        menu2 = [parse_dish(row) for row in csv.DictReader(f.readlines(), delimiter=';')]

    diff = generate_diff_week(menu1, menu2)
    diff = itertools.groupby(diff, key=lambda d: d.dish().datum)
    for day, day_diff in diff:
        day_diff = sorted(
            day_diff,
            key=lambda d: (StwnoApi.MENU_TYPES.index(d.dish().warengruppe[0]),
                           d.dish().warengruppe))
        print(get_menu_diff_formatted(day_diff, day))
