import csv
import os

import wget as wget

from mensabot.mensa import MENU_URL, parse_dish

DIR = "/tmp/mensa/csvs"
DISHES_MATCHED = {}

if not os.path.isdir(DIR):
    os.makedirs(DIR,exist_ok=True)
    for i in range(1, 53):
        wget.download("{}/{}.csv".format(MENU_URL, i), out=DIR)

for file in os.listdir(DIR):
    for row in csv.DictReader(open(DIR + "/" + file, 'r', encoding="ISO-8859-1"), delimiter=';'):
        dish, name, matcher = parse_dish(row,debug=True)
        if matcher not in DISHES_MATCHED:
            DISHES_MATCHED[matcher] = []
        DISHES_MATCHED[matcher].append((matcher, name) + dish)

for i, list in DISHES_MATCHED.items():
    csv.writer(open("{}/../out-{}.csv".format(DIR, i), 'w+')).writerows(list)
