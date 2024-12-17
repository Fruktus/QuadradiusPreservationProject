import hashlib
from datetime import datetime
import secrets
import string


def is_guest(username: str, password: str):
    return username.endswith(' GUEST') and \
           password == hashlib.md5(b'<NOPASS>').hexdigest()


def make_month_dates(month: int, year: int) -> tuple[datetime, datetime]:
    return \
        datetime(year, month, 1), \
        datetime(year + month // 12, (month % 12) + 1, 1)


def generate_random_password(length: int) -> str:
    return ''.join([secrets.choice(string.ascii_letters + string.digits) for _ in range(length)])


def calculate_new_ratings(rating1: int, rating2: int, score1: int = 1, score2: int = 0, k_factor: int = 32
                          ) -> tuple[int, int]:
    """Calculates new ratings according to ELO equation. The default values are meant for case when
    the first player is a winner of a binary game (victory - score 1, lose - score 0)"""
    expected_score_1 = 1 / (1 + pow(10, (rating2 - rating1) / 400))
    expected_score_2 = 1 / (1 + pow(10, (rating1 - rating2) / 400))

    new_rating_1 = rating1 + k_factor * (score1 - expected_score_1)
    new_rating_2 = rating2 + k_factor * (score2 - expected_score_2)

    return (new_rating_1, new_rating_2)
