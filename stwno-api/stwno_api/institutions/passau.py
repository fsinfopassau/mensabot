import datetime as dtm
from typing import List

from bs4 import BeautifulSoup
from cached_property import cached_property
from dateutil.easter import easter
from dateutil.relativedelta import TH, TU, relativedelta

from stwno_api.institution import Institution, Location, LocationType, Semester

__all__ = ["Passau"]

CAFETE = LocationType.CAFETERIA
MENSA = LocationType.MENSA


class Passau(Institution):
    DATES_URL = "http://www.uni-passau.de/studium/waehrend-des-studiums/semesterterminplan/vorlesungszeiten/"

    def __init__(self):
        super().__init__("Passau", "pa")

    @cached_property
    def locations(self) -> List[Location]:
        return [
            Location("uni-pa-am", CAFETE, "cafeterien/cafeteria-uni-pa-audimax", None,
                     ["am", lambda s: s.startswith("audi")]),
            Location("uni-pa-nk", CAFETE, "cafeterien/cafeteria-uni-pa-nikolakloster", "Cafeteria-Nikolakloster",
                     ["nk", "kk", "kc", "kuca", "kuka",
                      lambda s: s.startswith("niko") or s.startswith("kul")]),
            Location("uni-pa-wiwi", CAFETE, "cafeterien/cafebar-uni-pa-wiwi", None,
                     ["wiwi", "w", "wi", "ww"]),
            self.default_mensa,
            self.default_cafeteria,
        ]

    @cached_property
    def default_mensa(self):
        return Location("uni-pa-mensa", MENSA, "mensen/mensa-uni-passau", "UNI-P",
                        ["mensa", "m"])

    @cached_property
    def default_cafeteria(self):
        return Location("uni-pa-mensacafete", CAFETE, "cafeterien/cafeteria-uni-pa-mensagebaeude", None,
                        [lambda s: s.startswith("mensacaf"), "mc"])

    def _get_semester_dates(self) -> List[Semester]:
        r = self._session().get(self.DATES_URL)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        table = soup.find(id="up-content").next_sibling.find("table")
        assert list(table.find("thead").strings) == ['Semester', 'Beginn', 'Ende',
                                                     'Verfügungstag der Universität Passau (vorlesungsfrei)']
        assert table.next_sibling.string == \
               "Die Vorlesungszeit wird unterbrochen vom 24. Dezember bis einschließlich 6. Januar, vom " \
               "Gründonnerstag bis einschließlich Dienstag nach Ostern sowie am Dienstag nach Pfingsten!"
        semesters = []
        for semester_tr in table.find("tbody").find_all("tr"):
            name, *dates = semester_tr.strings
            try:
                dates = [dtm.datetime.strptime(d, "%d.%m.%Y").date() for d in dates]
            except ValueError:
                continue
            start, end, bruecke = dates
            lecture_free = [(bruecke, bruecke)]
            holidays = []
            winter_sem = name.startswith("Winter")
            assert winter_sem == (start.year != end.year)

            if winter_sem:
                # 24. Dezember bis einschließlich 6. Januar
                lecture_free.append((dtm.date(start.year, 12, 24), (dtm.date(end.year, 1, 6))))
                holidays.append((dtm.date(start.year, 12, 24), dtm.date(end.year, 1, 1)))
                holidays.append(((dtm.date(end.year, 1, 6)), (dtm.date(end.year, 1, 6))))
            else:
                easter_date = easter(start.year)
                # Gründonnerstag bis einschließlich Dienstag nach Ostern
                holidays.append((easter_date + relativedelta(weekday=TH(-1)),
                                 easter_date + relativedelta(weekday=TU(+1))))
                # Dienstag nach Pfingsten
                holidays.append((easter_date + relativedelta(days=50),
                                 easter_date + relativedelta(days=51)))

            lecture_free += holidays
            semesters.append(Semester(name, winter_sem, start, end, lecture_free, holidays))

        semesters.sort(key=lambda e: e.start)
        return semesters
