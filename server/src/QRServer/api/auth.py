from datetime import datetime, timedelta, timezone
from secrets import token_hex

import jwt


def make_access_token(secret: str, user_id: str, username: str, lifetime_sec: int) -> str:
    payload = {
        'sub': user_id,
        'username': username,
        'type': 'access',
        'exp': datetime.now(timezone.utc) + timedelta(seconds=lifetime_sec),
    }
    return jwt.encode(payload, secret, algorithm='HS256')


def make_refresh_token(secret: str, user_id: str, lifetime_sec: int) -> str:
    payload = {
        'sub': user_id,
        'type': 'refresh',
        'exp': datetime.now(timezone.utc) + timedelta(seconds=lifetime_sec),
        'jti': token_hex(16),
    }
    return jwt.encode(payload, secret, algorithm='HS256')


def decode_token(secret: str, token: str) -> dict:
    return jwt.decode(token, secret, algorithms=['HS256'])
