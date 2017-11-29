import datetime as dtm
import io
import sys
import unittest
from contextlib import ExitStack

import more_itertools
import pkg_resources
import requests_mock
from freezegun import freeze_time

from stwno_cmds.main import *


class Capturing(list):
    def __enter__(self):
        self._stdout = sys.stdout
        sys.stdout = self._stringio = io.StringIO()
        return self

    def __exit__(self, *args):
        self.extend(self._stringio.getvalue().splitlines())
        del self._stringio  # free up some memory
        sys.stdout = self._stdout


class TestMensaCmd(unittest.TestCase):
    def call_mensa(self, args, dt):
        with ExitStack() as s:
            output = s.enter_context(Capturing())
            s.enter_context(freeze_time(dt))
            requests = s.enter_context(requests_mock.mock())
            requests.get('http://www.stwno.de/infomax/daten-extern/csv/UNI-P/44.csv',
                         text=pkg_resources.resource_string("test.data", "44.csv").decode("iso8859_3"))
            mensa(args)
        return output

    def test_date_detection(self):
        vorgestern = self.call_mensa(["vorgestern"], "2017-11-01")
        gestern = self.call_mensa(["gestern"], "2017-10-31")
        heute = self.call_mensa([], "2017-10-30")  # TODO add time
        morgen = self.call_mensa(["morgen"], "2017-10-29")
        uebermorgen = self.call_mensa(["uebermorgen"], "2017-10-28")

        self.assertListEqual(heute[1:], vorgestern[1:])
        self.assertListEqual(heute[1:], gestern[1:])
        self.assertListEqual(heute[1:], morgen[1:])
        self.assertListEqual(heute[1:], uebermorgen[1:])
        self.assertListEqual(heute, self.call_mensa(["heute"], "2017-10-30"))
        self.assertListEqual(heute, self.call_mensa(["today"], "2017-10-30"))
        # self.assertListEqual(heute, self.call_mensa(["30.10."], "2017-10-30"))  # FIXME
        self.assertListEqual(heute, self.call_mensa(["30.10.2017"], "2017-10-30"))
        self.assertListEqual(morgen, self.call_mensa(["30.10."], "2017-10-29"))
        self.assertListEqual(morgen, self.call_mensa(["+1d"], "2017-10-29"))
        self.assertListEqual(morgen, self.call_mensa(["tomorrow"], "2017-10-29"))
        self.assertListEqual(uebermorgen, self.call_mensa(["Montag"], "2017-10-28"))
        self.assertListEqual(uebermorgen, self.call_mensa(["monday"], "2017-10-28"))
        self.assertListEqual(uebermorgen, self.call_mensa(["uebermorgen"], "2017-10-28"))
        self.assertListEqual(uebermorgen, self.call_mensa(["übermorgen"], "2017-10-28"))
        self.assertListEqual(uebermorgen, self.call_mensa([u"\u00A8" + "ubermorgen"], "2017-10-28"))
        self.assertListEqual(uebermorgen, self.call_mensa([u"\u0308" + "ubermorgen"], "2017-10-28"))

    def test_template(self):
        pass

    def test_next_open(self):
        with ExitStack() as s:
            # output = s.enter_context(Capturing())
            requests = s.enter_context(requests_mock.mock())
            requests.get('http://www.stwno.de/infomax/daten-extern/csv/UNI-P/43.csv',
                         text=pkg_resources.resource_string("test.data", "43.csv").decode("iso8859_3"))
            requests.get('http://www.stwno.de/infomax/daten-extern/csv/UNI-P/44.csv',
                         text=pkg_resources.resource_string("test.data", "44.csv").decode("iso8859_3"))
            requests.get('http://www.stwno.de/infomax/daten-extern/csv/UNI-P/45.csv',
                         text=pkg_resources.resource_string("test.data", "45.csv").decode("iso8859_3"))
            requests.get('https://stwno.de/de/gastronomie/mensen/mensa-uni-passau',
                         text=pkg_resources.resource_string("test.data", "mensa-uni-passau.html").decode("utf-8"))
            requests.get('http://www.uni-passau.de/studium/waehrend-des-studiums/semesterterminplan/vorlesungszeiten/',
                         text=pkg_resources.resource_string("test.data", "vorlesungszeiten.html").decode("utf-8"))
            s.enter_context(freeze_time("2017-10-27 08:00"))

            api = CachedStwnoApi(Passau)

            def next_open(dt):
                openinfo, menu = api.get_next_mensa_open(Passau.default_mensa, starting_from=dt)
                self.assertTrue(menu, "get_next_mensa_open didn't find a day with a menu")
                return dtm.datetime.combine(openinfo.day, openinfo.close)

            start = dtm.datetime.now()
            close_times = more_itertools.iterate(next_open, start)
            close_times = itertools.takewhile(lambda dt: dt < dtm.datetime(2017, 11, 7), close_times)
            close_times = list(close_times)

            self.assertListEqual(close_times, [
                start,
                dtm.datetime(2017, 10, 27, 14, 15),
                dtm.datetime(2017, 10, 30, 14, 15),
                dtm.datetime(2017, 11, 2, 14, 15),
                dtm.datetime(2017, 11, 3, 14, 15),
                dtm.datetime(2017, 11, 6, 14, 15)
            ])


if __name__ == '__main__':
    unittest.main()
