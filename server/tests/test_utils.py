import unittest
from datetime import datetime

from QRServer.common import utils


class MakeMonthDatesTest(unittest.TestCase):
    def test_make_month_dates(self):
        self.assertEqual(
            utils.make_month_dates(1, 2020),
            (datetime(2020, 1, 1), datetime(2020, 2, 1))
        )
        self.assertEqual(
            utils.make_month_dates(12, 2020),
            (datetime(2020, 12, 1), datetime(2021, 1, 1))
        )
