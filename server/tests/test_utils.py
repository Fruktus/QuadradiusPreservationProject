import unittest
from datetime import datetime as dt
import random as rnd
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


class CalculateNewRatingsTest(unittest.TestCase):
    def test_rating_change(self):
        player_1_rating = 500
        player_2_rating = 500

        player_1_rating, player_2_rating = utils.calculate_new_ratings(
                player_1_rating, player_2_rating)

        self.assertEqual(player_1_rating, 532)
        self.assertEqual(player_2_rating, 468)

    def test_rating_vs_different_players(self):
        # Playing against the same player the same amount of times as someone who plays
        # against different opponents should result in higher score
        player_1_rating = 500
        player_2_rating = 500
        player_3_rating = 500

        for _ in range(10):
            player_1_rating, player_2_rating = utils.calculate_new_ratings(
                player_1_rating, player_2_rating)

        self.assertEqual(player_1_rating, 670)
        self.assertEqual(player_2_rating, 330)

        for _ in range(10):
            player_3_rating, _ = utils.calculate_new_ratings(
                player_3_rating, 500)

        self.assertEqual(player_3_rating, 720)
        self.assertGreater(player_3_rating, player_1_rating)

    def test_rating_ratio(self):
        # The ratio betweem winner/loser should remain roughly the same
        # if the percentage remains the same
        rnd.seed(2222)
        player_1_rating = 500
        player_2_rating = 500

        for _ in range(1000):
            if rnd.randrange(0, 100) > 80:
                player_1_rating, player_2_rating = utils.calculate_new_ratings(
                    player_1_rating, player_2_rating)
            else:
                player_2_rating, player_1_rating = utils.calculate_new_ratings(
                    player_2_rating, player_1_rating)

        rating_ratio_10 = player_1_rating / player_2_rating

        player_1_rating = 500
        player_2_rating = 500

        for _ in range(3000):
            if rnd.randrange(0, 100) > 80:
                player_1_rating, player_2_rating = utils.calculate_new_ratings(
                    player_1_rating, player_2_rating)
            else:
                player_2_rating, player_1_rating = utils.calculate_new_ratings(
                    player_2_rating, player_1_rating)

        rating_ratio_100 = player_1_rating / player_2_rating

        self.assertEqual(round(rating_ratio_10, 2), 0.49)
        self.assertEqual(round(rating_ratio_100, 2), 0.44)
