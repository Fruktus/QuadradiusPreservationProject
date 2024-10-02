import hashlib
from datetime import datetime


def is_guest(username: str, password: str):
    return username.endswith(' GUEST') and \
           password == hashlib.md5(b'<NOPASS>').hexdigest()


def make_month_dates(month: int, year: int) -> tuple[datetime, datetime]:
    return \
        datetime(year, month, 1), \
        datetime(year + month // 12, (month % 12) + 1, 1)
