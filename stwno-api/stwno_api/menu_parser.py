import datetime as dtm
import itertools
import re
from collections import Counter
from enum import Enum, auto
from typing import AbstractSet, List, NamedTuple, Optional, Tuple

import fuzzywuzzy.fuzz

__all__ = ["Dish", "Change", "generate_diff_week"]

PATTERN_TAG = "([AH]?[A-Z]|MV|VG|1?[0-9])"
PATTERN_ZUSATZ = PATTERN_TAG + "(" + PATTERN_TAG + "[,/]\s*)*"
PATTERN_KENNZ = "\s*[,*]\s*(" + PATTERN_TAG + "(" + PATTERN_TAG + "[,/]\s*)*)$"

Dish = NamedTuple("Dish", [
    ("datum", dtm.datetime),
    ("name", str),
    ("warengruppe", str),
    ("kennz", Counter),
    ("zusatz", Counter),
    ("stud", float),
    ("bed", float),
    ("gast", float)
])


def parse_dish(row: dict) -> Dish:
    """
    Parse a row from the csv file as Dish, trying to extract further information from the name.
    """

    row['datum'] = dtm.datetime.strptime(row['datum'], "%d.%m.%Y").date()
    row['zusatz'] = Counter()
    row['kennz'] = Counter(row['kennz'].split(",") if row['kennz'] else [])
    row["stud"] = float(row["stud"].replace(",", "."))
    row["bed"] = float(row["bed"].replace(",", "."))
    row["gast"] = float(row["gast"].replace(",", "."))
    del row['tag']
    del row['preis']

    # fix for fucked up Salatmixes
    if row["name"].startswith("Salatmix"):
        row["name"] = re.match("Salatmix( [IV]+)?", row["name"]).group()
    else:
        names, zusatz, kennz = __parse_name(row["name"])
        row["name"] = " ".join(names)
        row['zusatz'] += Counter(zusatz)
        del row['zusatz']['']
        row['kennz'] += Counter(kennz)
        del row['kennz']['']

    return Dish(**row)


def __parse_name(str_in):
    str_in = re.sub("\(+", "(", re.sub("\)+", ")", str_in))

    name = []
    kennz = []
    zusatz = []

    def append_name(token):
        nonlocal kennz
        token = token.strip()
        m = re.search(PATTERN_KENNZ, token)
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
                return str_in, ["??"], ["??"]
            append_name(token)
            token = ""
            brackets = True
        elif c == ")":
            if not brackets:
                return str_in, ["??"], ["??"]
            append_zusatz(token)
            token = ""
            brackets = False
        else:
            token += c

    if token:
        append_name(token)

    return name, zusatz, kennz


########################################################################################################################

class ChangeType(Enum):
    ATTR = auto()
    RENAME = auto()
    REPLACE = auto()
    REMOVE = auto()
    ADD = auto()


class Change(object):
    def __init__(self, type: ChangeType, from_dish: Optional[Dish], to_dish: Optional[Dish], match: int = None):
        assert from_dish != to_dish
        if not isinstance(type, ChangeType):
            type = ChangeType[type]

        self.type = type  # type: ChangeType
        self.from_dish = from_dish  # type: Optional[Dish]
        self.to_dish = to_dish  # type: Optional[Dish]
        self.match = match  # type: int

        if not self.from_dish or not self.to_dish:
            self.diff = {}
        else:
            self.diff = {
                attr: (self.from_dish[idx], self.to_dish[idx])
                for idx, attr in enumerate(Dish._fields)
                if self.from_dish[idx] != self.to_dish[idx]
            }

    def dish(self) -> Dish:
        return self.to_dish if self.to_dish else self.from_dish

    def __eq__(self, other):
        return isinstance(other, Change) and \
               self.type == other.type and \
               self.from_dish == other.from_dish and \
               self.to_dish == other.to_dish

    def __str__(self):
        ret = "%s " % self.dish().datum
        if self.type == ChangeType.ATTR:
            ret += "ATR: %s (%s -> %s)" % (
                self.from_dish.name, self.from_dish.warengruppe, self.to_dish.warengruppe
            )
        elif self.type == ChangeType.RENAME:
            ret += "REN: %s -> %s (%s -> %s)" % (
                self.from_dish.name, self.to_dish.name, self.from_dish.warengruppe, self.to_dish.warengruppe
            )
        elif self.type == ChangeType.REPLACE:
            ret += "REP: %s -> %s (%s -> %s)" % (
                self.from_dish.name, self.to_dish.name, self.from_dish.warengruppe, self.to_dish.warengruppe
            )
        elif self.type == ChangeType.REMOVE:
            ret += "REM: - %s (%s)" % (
                self.from_dish.name, self.from_dish.warengruppe
            )
        elif self.type == ChangeType.ADD:
            ret += "ADD: + %s (%s)" % (
                self.to_dish.name, self.to_dish.warengruppe
            )
        if self.diff:
            ret += ", %s changed attrs" % len(self.diff)
        if self.match:
            ret += ", %d%% match" % self.match
        return ret


def generate_diff_week(menu1, menu2) -> List[Change]:
    if menu1 == menu2:
        return []

    dates = {dish.datum for dish in menu1}
    map1 = {datum: {dish.warengruppe: dish for dish in menu1 if dish.datum == datum} for datum in dates}
    map2 = {datum: {dish.warengruppe: dish for dish in menu2 if dish.datum == datum} for datum in dates}

    for date in dates:
        if map1[date] == map2[date]:
            continue

        # find all warengruppen that contain changes
        changed = {
            re.sub("[0-9]", "", wg) for wg
            in itertools.chain(map1[date].keys(), map2[date].keys())
            if map1[date].get(wg, None) != map2[date].get(wg, None)
        }

        for wg in changed:
            # compare all items in the concerned warengruppe
            changed_wg1 = [dish for dish in map1[date].values() if dish.warengruppe.startswith(wg)]
            changed_wg2 = [dish for dish in map2[date].values() if dish.warengruppe.startswith(wg)]
            yield from generate_diff_group(changed_wg1, changed_wg2)


def generate_diff_group(dishes1: List[Dish], dishes2: List[Dish], ratio=None, cutoff=60):
    names1 = {d.name: d for d in dishes1}
    names2 = {d.name: d for d in dishes2}
    matches = fuzzy_set_match(names1.keys(), names2.keys(), ratio=ratio)

    for str1, str2, r in matches:
        if str1:
            dish1 = names1[str1]
            if not str2:
                yield Change(ChangeType.REMOVE, dish1, None, r)
                continue
        if str2:
            dish2 = names2[str2]
            if not str1:
                yield Change(ChangeType.ADD, None, dish2, r)
                continue

        assert str1 and str2 and dish1 and dish2

        if dish1 == dish2:
            continue  # not changed
        elif dish1.name == dish2.name:
            yield Change(ChangeType.ATTR, dish1, dish2, r)
        elif r >= cutoff:
            yield Change(ChangeType.RENAME, dish1, dish2, r)
        else:
            yield Change(ChangeType.REPLACE, dish1, dish2, r)


# http://chairnerd.seatgeek.com/fuzzywuzzy-fuzzy-string-matching-in-python/
# https://streamhacker.com/2011/10/31/fuzzy-string-matching-python/
# https://stackoverflow.com/questions/10879247/how-does-the-python-difflib-get-close-matches-function-work
def fuzzy_set_match(set1: AbstractSet[str], set2: AbstractSet[str], ratio=None) \
        -> List[Tuple[str, str, int]]:
    if set1 == set2:
        return ((100, str1, str1) for str1 in set1)
    if not ratio:
        ratio = fuzzywuzzy.fuzz.ratio

    set1 = set(set1)
    set2 = set(set2)
    ratios = sorted(((ratio(str1, str2), str1, str2) for str1 in set1 for str2 in set2), reverse=True)
    for r, str1, str2 in ratios:
        if not (set1 and set2):
            break
        if str1 in set1 and str2 in set2:
            set1.remove(str1)
            set2.remove(str2)
            yield str1, str2, r
    for str1 in set1:
        yield str1, None, 0
    for str2 in set2:
        yield None, str2, 0
