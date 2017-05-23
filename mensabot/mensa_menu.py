import re
from collections import Counter
from datetime import datetime
from typing import NamedTuple

import regex as re

PATTERN_TAG = "([AH]?[A-Z]|MV|VG|1?[0-9])"
PATTERN_ZUSATZ = PATTERN_TAG + "(" + PATTERN_TAG + "[,/]\s*)*"
PATTERN_KENNZ = "\s*[,*]\s*(" + PATTERN_TAG + "(" + PATTERN_TAG + "[,/]\s*)*)$"

dish = NamedTuple("dish", [
    ("datum", datetime),
    ("name", str),
    ("warengruppe", str),
    ("kennz", Counter),
    ("zusatz", Counter),
    ("stud", float),
    ("bed", float),
    ("gast", float)
])


def parse_dish(row: dict) -> dish:
    """
    Parse a row from the csv file as dish, trying to extract further information from the name.
    """

    row['datum'] = datetime.strptime(row['datum'], "%d.%m.%Y").date()
    row['zusatz'] = Counter()
    row['kennz'] = Counter(row['kennz'].split(",") if row['kennz'] else [])
    row["stud"] = float(row["stud"].replace(",", "."))
    row["bed"] = float(row["bed"].replace(",", "."))
    row["gast"] = float(row["gast"].replace(",", "."))
    del row['tag']
    del row['preis']

    names, zusatz, kennz = __parse_name(row["name"])
    row["name"] = " ".join(names)
    row['zusatz'] += Counter(zusatz)
    row['kennz'] += Counter(kennz)

    # fix for fucked up Salatmixes
    if row["name"].startswith("Salatmix"):
        row["name"] = re.match("Salatmix( [IV]+)?", row["name"]).group()

    return dish(**row)


def __parse_name(str_in):
    name = []
    kennz = []
    zusatz = []

    def append_name(token):
        nonlocal kennz
        token = token.strip()
        m = re.search(PATTERN_KENNZ, token)  # TODO also at end of string
        if m:
            kennz += (s.strip() for s in m.group(1).split(","))
            token = re.sub(PATTERN_KENNZ, "", token)
        name.append(token)

    def append_zusatz(token):
        nonlocal zusatz
        token = token.strip()
        if re.match(PATTERN_ZUSATZ, token):
            zusatz += (s.strip() for s in token.split(","))
        else:
            name.append("(" + token + ")")

    brackets = False
    token = ""
    for c in str_in:
        if c == "(":
            if brackets:
                return "??", ["??"], ["??"]
            append_name(token)
            token = ""
            brackets = True
        elif c == ")":
            if not brackets:
                return "??", ["??"], ["??"]
            append_zusatz(token)
            token = ""
            brackets = False
        else:
            token += c

    if token:
        append_name(token)

    return name, zusatz, kennz

