import functools
import asyncio


class UpdateCollisionError(Exception):
    pass


def retry_on_update_collision(retries=3, delay=0.1):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return await func(*args, **kwargs)
                except UpdateCollisionError:
                    if attempt < retries - 1:
                        asyncio.sleep(delay)
                        continue
                    else:
                        raise
        return wrapper
    return decorator
