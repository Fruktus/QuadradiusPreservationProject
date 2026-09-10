from aiohttp import web
from datetime import datetime, timedelta, timezone
import functools
import jwt
from secrets import token_hex


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


def authenticated(handler):
    @functools.wraps(handler)
    async def wrapper(self, request: web.Request, *args, **kwargs):
        auth_header = request.headers.get('Authorization', '')

        if not auth_header.startswith('Bearer '):
            return web.json_response(
                {'error': 'authentication required'},
                status=401,
            )

        token = auth_header.removeprefix('Bearer ')

        try:
            claims = decode_token(self.api_token_secret, token)

            if claims.get('type') != 'access':
                return web.json_response(
                    {'error': 'authentication required'},
                    status=401,
                )

            user = await self.connector.get_user(claims['sub'])

            if user is None:
                return web.json_response(
                    {'error': 'authentication required'},
                    status=401,
                )

        except jwt.PyJWTError:
            return web.json_response(
                {'error': 'authentication required'},
                status=401,
            )

        return await handler(self, request, user, *args, **kwargs)

    return wrapper
