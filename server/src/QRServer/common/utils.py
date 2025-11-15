import hashlib
from datetime import datetime, timezone
import secrets
import string


def is_guest(username: str, password: str):
    return username.endswith(' GUEST') and \
           password == hashlib.md5(b'<NOPASS>').hexdigest()


def make_month_dates(month: int, year: int) -> tuple[datetime, datetime]:
    # Returns tuple consisting of the first day of the given month and year and
    # the first day of the next month (incrementing year if needed)
    return \
        datetime(year, month, 1, tzinfo=timezone.utc), \
        datetime(year + month // 12, (month % 12) + 1, 1, tzinfo=timezone.utc)


def generate_random_password(length: int) -> str:
    return ''.join([secrets.choice(string.ascii_letters + string.digits) for _ in range(length)])


def make_month_dates_range(start_date: datetime, end_date: datetime) -> list[datetime]:
    # Returns a list of datetimes between the start_date and end_date (end inclusive)
    if start_date > end_date:
        return []

    current_month = start_date.month
    current_year = start_date.year

    end_month = end_date.month
    end_year = end_date.year

    res = []

    while True:
        res.append(datetime(year=current_year, month=current_month, day=1, tzinfo=timezone.utc))

        if current_month >= end_month and current_year >= end_year:
            return res
        else:
            current_year += current_month // 12
            current_month = (current_month % 12) + 1


def calculate_new_ratings(winner_rating: int, loser_rating: int, k_factor: int = 64
                          ) -> tuple[int, int]:
    """Calculates new ratings according to ELO equation. The default values are meant for case when
    the first player is a winner of a binary game (victory - score 1, lose - score 0)"""
    expected_score_1 = 1 / (1 + pow(10, (loser_rating - winner_rating) / 400))
    expected_score_2 = 1 / (1 + pow(10, (winner_rating - loser_rating) / 400))

    new_winner_rating = winner_rating + k_factor * (1 - expected_score_1)
    new_loser_rating = loser_rating + k_factor * (0 - expected_score_2)

    return (round(new_winner_rating), round(new_loser_rating))
