import csv
import os
import subprocess

from more_itertools import pairwise

from mensabot.mensa import PRICES_CATEGORIES
from mensabot.mensa_menu import generate_diff, parse_dish


def get_file_at_commit(commit, file):
    cmd = "git archive %s %s | tar -xOf /dev/stdin"
    return subprocess.run(
        ["bash", "-c", cmd % (commit, file)], check=True, stdout=subprocess.PIPE) \
        .stdout.decode("iso8859_3")


def parse_file(text):
    return [parse_dish(row) for row in csv.DictReader(text.split("\n"), delimiter=';')]


def print_diff(diff):
    for x in diff:
        if list(x.diff.keys()) == ["warengruppe"]:
            continue

        if "name" in x.diff:
            print("\t%s ➡️ %s" % x.diff["name"])
        elif not x.from_dish:
            print("\t🆕 " + x.to_dish.name)
        elif not x.to_dish:
            print("\t❎ " + x.from_dish.name)
        else:
            print("\t" + x.from_dish.name)

        if any(s in x.diff for s in PRICES_CATEGORIES):
            print("\t\tPreis: (%s/%s/%s) ➡️ (%s/%s/%s)" %
                  (x.from_dish.stud, x.from_dish.bed, x.from_dish.gast,
                   x.to_dish.stud, x.to_dish.bed, x.to_dish.gast))
        if "kennz" in x.diff:
            print("\t\tKennz: %s ➡️ %s" % tuple(",".join(c.keys()) for c in x.diff["kennz"]))
        if "zusatz" in x.diff:
            print("\t\tZusatz: %s ➡️ %s" % tuple(",".join(c.keys()) for c in x.diff["zusatz"]))

            # print("\t" + str(x))
            # print("\t\t" + str(x.diff))


def main():
    for file in os.listdir("."):
        if file.endswith(".csv"):
            commits = subprocess.run(
                ["git", "log", "--format=%H", "--", file], check=True, stdout=subprocess.PIPE) \
                .stdout.decode("utf-8").split("\n")
            for a, b in pairwise(c for c in commits if c):
                print(a, b)
                diff = generate_diff(parse_file(get_file_at_commit(a, file)), parse_file(get_file_at_commit(b, file)))
                print_diff(diff)


if __name__ == "__main__":
    os.chdir("/home/niko/Sync/Uni/Fachschaft/Code/mensabot/crawler/store")
    main()



# if __name__ == "__main__":
#     git.reset("577313819c501f8aa72336370c3e5466eec00ea3")
#     git.checkout("--", "21.*")
#     # git.reset("origin/master")
#     # git.checkout("5aa368301ad5c97935e243a5f182e3c324d02638", "--", "21.csv")
#
#     fetch_week(21)
#
#     while not SCHED.empty():
#         SCHED.run()
