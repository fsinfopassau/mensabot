import csv
import os

import wget as wget

from mensabot.mensa import MENU_URL, parse_dish
from mensabot.mensa_menu import __parse_name

DIR = "/tmp/mensa/csvs"
DISHES_MATCHED = {}

print(__parse_name(
    "Salatmix IValsamico Dressing (1,5,16)Bunter Gemüsesalatlaukraut-Apfelrohkost (16)Salatsauce Kräuter (C,G)"))
print(__parse_name("Bio Basmatireis"))
print(__parse_name("Puten - Dönerteller * G (5,16,A,G,J,K)"))
print(__parse_name("Brühe mit Tiroler Suppenknödel,S (2,3,A,C,G,I,AA,P)"))
print(__parse_name("Bohnen - Gemüse - Ragout mit Sojasprossen, Erdnüssen (3,F,I)"))
print(__parse_name("Chilli con Soja (VG) mit Baguette(V) (3,A,F,I)"))
print(__parse_name("Pikkoposs (das estnische Kottelett) (3,A,C,I,J)"))

if not os.path.isdir(DIR):
    os.makedirs(DIR, exist_ok=True)
    for i in range(1, 53):
        wget.download("{}/{}.csv".format(MENU_URL, i), out=DIR)

for file in os.listdir(DIR):
    for row in csv.DictReader(open(DIR + "/" + file, 'r', encoding="ISO-8859-1"), delimiter=';'):
        dish, name, matcher = parse_dish(row)
        if matcher not in DISHES_MATCHED:
            DISHES_MATCHED[matcher] = []
        DISHES_MATCHED[matcher].append((matcher, name) + dish)

for i, list in DISHES_MATCHED.items():
    csv.writer(open("{}/../out-{}.csv".format(DIR, i), 'w+')).writerows(list)
