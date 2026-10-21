import asyncio
import functools
import time
from collections import OrderedDict
from typing import Any, Awaitable, Callable

# Looked up through the module so tests can patch it
_clock = time.monotonic

_UNSET = object()


class _TtlStore:
    """Bounded key -> (expiry, value) store, plus in-flight computations so that
    concurrent misses for the same key share one computation."""

    def __init__(self, maxsize: int):
        self.maxsize = maxsize
        self.entries: OrderedDict[Any, tuple[float, Any]] = OrderedDict()
        self.inflight: dict[Any, asyncio.Future] = {}

    def get(self, key):
        entry = self.entries.get(key)
        if entry is None:
            return _UNSET
        expires_at, value = entry
        if expires_at <= _clock():
            del self.entries[key]
            return _UNSET
        return value

    def put(self, key, value, ttl: float):
        self.entries[key] = (_clock() + ttl, value)
        self.entries.move_to_end(key)
        while len(self.entries) > self.maxsize:
            self.entries.popitem(last=False)  # evict the oldest


def ttl_cache(ttl: float, maxsize: int = 1024):
    """Caches the result of an async *method* for `ttl` seconds, per distinct positional arguments.

    - The cache lives on the instance (not on the class), so separate instances never share entries.
    - Only successful results are cached; exceptions propagate and are not stored.
    - Concurrent calls with the same arguments made while one is already computing wait for that one.
    - At most `maxsize` entries are kept; the oldest are evicted first.
    - Arguments must be hashable. Keyword arguments are not supported, to keep keys unambiguous.
    """
    def decorator(func: Callable[..., Awaitable[Any]]):
        attr = f'_ttl_cache_{func.__name__}'

        @functools.wraps(func)
        async def wrapper(self, *args):
            store: _TtlStore | None = self.__dict__.get(attr)
            if store is None:
                store = self.__dict__.setdefault(attr, _TtlStore(maxsize))

            while True:
                cached = store.get(args)
                if cached is not _UNSET:
                    return cached

                pending = store.inflight.get(args)
                if pending is None:
                    break
                try:
                    return await asyncio.shield(pending)
                except asyncio.CancelledError:
                    if pending.cancelled():
                        continue  # whoever was computing got cancelled, take over
                    raise

            future: asyncio.Future = asyncio.get_running_loop().create_future()
            store.inflight[args] = future
            try:
                value = await func(self, *args)
            except asyncio.CancelledError:
                future.cancel()
                raise
            except BaseException as e:
                future.set_exception(e)
                future.exception()  # mark retrieved, avoids "never retrieved" warnings when nobody waited
                raise
            else:
                store.put(args, value, ttl)
                future.set_result(value)
                return value
            finally:
                del store.inflight[args]

        def cache_clear(self):
            self.__dict__.pop(attr, None)

        wrapper.cache_clear = cache_clear  # type: ignore[attr-defined]
        return wrapper

    return decorator
