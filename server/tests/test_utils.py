import unittest
from datetime import datetime as dt

from QRServer.common import utils


class MakeMonthDatesTest(unittest.TestCase):
    def test_make_month_dates(self):
        self.assertEqual(
            utils.make_month_dates(1, 2020),
            (dt(2020, 1, 1), dt(2020, 2, 1))
        )
        self.assertEqual(
            utils.make_month_dates(12, 2020),
            (dt(2020, 12, 1), dt(2021, 1, 1))
        )


class GenerateRandomPasswordTest(unittest.TestCase):
    def test_generate_random_password(self):
        for i in range(0, 100, 10):
            self.assertEqual(len(utils.generate_random_password(i)), i)


class MakeMonthDatesRange(unittest.TestCase):
    def test_month_dates_range_basic(self):
        self.assertEqual(
            utils.make_month_dates_range(
                dt(2020, 1, 1), dt(2020, 1, 31)
            ),
            [
                dt(2020, 1, 1),
            ]
        )

    def test_month_dates_range_random_days_same_month(self):
        self.assertEqual(
            utils.make_month_dates_range(
                dt(2020, 1, 4), dt(2020, 1, 9)
            ),
            [
                dt(2020, 1, 1),
            ]
        )

    def test_month_dates_range_start_after_end(self):
        self.assertEqual(
            utils.make_month_dates_range(
                dt(2020, 2, 4), dt(2020, 1, 9)
            ),
            [
            ]
        )

    def test_month_dates_range_year(self):
        self.assertEqual(
            utils.make_month_dates_range(
                dt(2020, 1, 12), dt(2020, 12, 12)
            ),
            [
                dt(2020, 1, 1),
                dt(2020, 2, 1),
                dt(2020, 3, 1),
                dt(2020, 4, 1),
                dt(2020, 5, 1),
                dt(2020, 6, 1),
                dt(2020, 7, 1),
                dt(2020, 8, 1),
                dt(2020, 9, 1),
                dt(2020, 10, 1),
                dt(2020, 11, 1),
                dt(2020, 12, 1),
            ]
        )

    def test_month_dates_range_across_year(self):
        self.assertEqual(
            utils.make_month_dates_range(
                dt(2020, 11, 12), dt(2021, 2, 15)
            ),
            [
                dt(2020, 11, 1),
                dt(2020, 12, 1),
                dt(2021, 1, 1),
                dt(2021, 2, 1),
            ]
        )
