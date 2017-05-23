import csv
import os
import subprocess

from more_itertools import pairwise

from mensabot.mensa_menu import parse_dish, generate_diff


def get_file_at_commit(commit, file):
    cmd = "git archive %s %s | tar -xOf /dev/stdin"
    return subprocess.run(
        ["bash", "-c", cmd % (commit, file)], check=True, stdout=subprocess.PIPE) \
        .stdout.decode("iso8859_3")


def parse_file(text):
    return [parse_dish(row) for row in csv.DictReader(text.split("\n"), delimiter=';')]


os.chdir("/home/niko/Sync/Uni/Fachschaft/Code/mensabot/crawler/store")
for file in os.listdir("."):
    if file.endswith(".csv"):
        commits = subprocess.run(
            ["git", "log", "--format=%H", "--", file], check=True, stdout=subprocess.PIPE) \
            .stdout.decode("utf-8").split("\n")
        for a, b in pairwise(c for c in commits if c):
            print(a, b)
            diff = generate_diff(parse_file(get_file_at_commit(a, file)), parse_file(get_file_at_commit(b, file)))
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

                if any(s in x.diff for s in ["stud", "bed", "gast"]):
                    print("\t\tPreis: (%s/%s/%s) ➡️ (%s/%s/%s)" %
                          (x.from_dish.stud, x.from_dish.bed, x.from_dish.gast,
                           x.to_dish.stud, x.to_dish.bed, x.to_dish.gast))
                if "kennz" in x.diff:
                    print("\t\tKennz: %s ➡️ %s" % tuple(",".join(c.keys()) for c in x.diff["kennz"]))
                if "zusatz" in x.diff:
                    print("\t\tZusatz: %s ➡️ %s" % tuple(",".join(c.keys()) for c in x.diff["zusatz"]))

                    # print("\t" + str(x))
                    # print("\t\t" + str(x.diff))
