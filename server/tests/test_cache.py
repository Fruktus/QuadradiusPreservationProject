import asyncio
import unittest
from unittest.mock import patch

from QRServer.common.utils.cache import ttl_cache


class Slow:
    def __init__(self):
        self.calls = 0
        self.gate: asyncio.Event | None = None
        self.fail = False

    @ttl_cache(ttl=10)
    async def compute(self, key):
        self.calls += 1
        if self.gate is not None:
            await self.gate.wait()
        if self.fail:
            raise ValueError('boom')
        return f'{key}-{self.calls}'


class SmallCache:
    def __init__(self):
        self.calls = 0

    @ttl_cache(ttl=10, maxsize=2)
    async def compute(self, key):
        self.calls += 1
        return key


class TtlCacheTest(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.now = 1000.0
        patcher = patch('QRServer.common.utils.cache._clock', lambda: self.now)
        patcher.start()
        self.addCleanup(patcher.stop)

    async def test_hit_within_ttl_and_miss_after(self):
        obj = Slow()
        self.assertEqual(await obj.compute('a'), 'a-1')
        self.now += 9.9
        self.assertEqual(await obj.compute('a'), 'a-1')
        self.assertEqual(obj.calls, 1)

        self.now += 0.2
        self.assertEqual(await obj.compute('a'), 'a-2')
        self.assertEqual(obj.calls, 2)

    async def test_keys_are_independent(self):
        obj = Slow()
        self.assertEqual(await obj.compute('a'), 'a-1')
        self.assertEqual(await obj.compute('b'), 'b-2')
        self.assertEqual(await obj.compute('a'), 'a-1')
        self.assertEqual(obj.calls, 2)

    async def test_instances_do_not_share_entries(self):
        first, second = Slow(), Slow()
        await first.compute('a')
        await second.compute('a')
        self.assertEqual((first.calls, second.calls), (1, 1))

    async def test_exceptions_are_not_cached(self):
        obj = Slow()
        obj.fail = True
        with self.assertRaises(ValueError):
            await obj.compute('a')
        obj.fail = False
        self.assertEqual(await obj.compute('a'), 'a-2')

    async def test_concurrent_misses_share_one_computation(self):
        obj = Slow()
        obj.gate = asyncio.Event()
        tasks = [asyncio.create_task(obj.compute('a')) for _ in range(5)]
        await asyncio.sleep(0)
        await asyncio.sleep(0)
        obj.gate.set()
        results = await asyncio.gather(*tasks)
        self.assertEqual(results, ['a-1'] * 5)
        self.assertEqual(obj.calls, 1)

    async def test_waiter_takes_over_when_computing_call_is_cancelled(self):
        obj = Slow()
        obj.gate = asyncio.Event()
        leader = asyncio.create_task(obj.compute('a'))
        await asyncio.sleep(0)
        waiter = asyncio.create_task(obj.compute('a'))
        await asyncio.sleep(0)

        leader.cancel()
        await asyncio.sleep(0)
        obj.gate.set()
        self.assertEqual(await waiter, 'a-2')
        with self.assertRaises(asyncio.CancelledError):
            await leader

    async def test_oldest_entries_are_evicted(self):
        obj = SmallCache()
        for key in ('a', 'b', 'c'):
            await obj.compute(key)
        self.assertEqual(obj.calls, 3)

        await obj.compute('c')
        await obj.compute('b')
        self.assertEqual(obj.calls, 3)  # still cached

        await obj.compute('a')  # was evicted
        self.assertEqual(obj.calls, 4)

    async def test_cache_clear(self):
        obj = Slow()
        await obj.compute('a')
        Slow.compute.cache_clear(obj)  # type: ignore[attr-defined]
        await obj.compute('a')
        self.assertEqual(obj.calls, 2)
