import sys

from mensabot.mensa import get_menu_day, get_opening_times

try:
    get_menu_day()
    get_opening_times("cafeterien/cafeteria-uni-pa-nikolakloster")
except:
    e = sys.exc_info()[0]
    print("Something went wrong")
