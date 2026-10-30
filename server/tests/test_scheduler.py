import asyncio
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from QRServer.config import Config
from QRServer.db.connector import DbConnector
from QRServer.db.models import ScheduledTask, ScheduledTaskStatus
from QRServer.scheduler.scheduler import Scheduler
from QRServer.scheduler.task import Task


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


class RecordingTask(Task):
    name = 'test'

    def __init__(self):
        self.calls: list[ScheduledTask] = []

    async def run(self, task: ScheduledTask) -> None:
        self.calls.append(task)


class DailyTask(RecordingTask):
    """Fires at noon every day"""
    name = 'daily'
    enabled = True

    def next_run(self, after: datetime) -> datetime | None:
        if not self.enabled:
            return None
        noon = after.replace(hour=12, minute=0, second=0, microsecond=0)
        return noon if noon > after else noon + timedelta(days=1)


class SchedulerTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.config = Config()
        self.conn = DbConnector(':memory:', self.config)
        await self.conn.connect()

        self.now = utc(2026, 5, 10, 12, 0, 0)
        self.scheduler = Scheduler(self.conn, self.config, clock=lambda: self.now)
        self.task = RecordingTask()
        self.scheduler.register(self.task)

        # the connector stamps task status changes with its own clock, keep it in step with the scheduler's
        patcher = patch('QRServer.db.connector.datetime', wraps=datetime)
        mock_datetime = patcher.start()
        mock_datetime.now.side_effect = lambda tz=None: self.now
        self.addCleanup(patcher.stop)

    async def asyncTearDown(self):
        await self.conn.close()

    def advance(self, **kwargs):
        self.now += timedelta(**kwargs)

    async def row(self, task_id: str) -> ScheduledTask:
        return next(t for t in await self.conn.get_scheduled_tasks() if t.id == task_id)

    async def test_does_not_run_task_before_it_is_due(self):
        await self.scheduler.schedule('test', self.now + timedelta(minutes=5), task_id='a')

        self.advance(minutes=4, seconds=59)

        self.assertEqual(await self.scheduler.tick(), 0)
        self.assertEqual(self.task.calls, [])

    async def test_runs_task_when_due(self):
        await self.scheduler.schedule('test', self.now + timedelta(minutes=5), task_id='a')

        self.advance(minutes=5)

        self.assertEqual(await self.scheduler.tick(), 1)
        self.assertEqual([t.id for t in self.task.calls], ['a'])

    async def test_does_not_run_task_twice(self):
        await self.scheduler.schedule('test', self.now, task_id='a')

        self.assertEqual(await self.scheduler.tick(), 1)
        self.assertEqual(await self.scheduler.tick(), 0)

        self.assertEqual(len(self.task.calls), 1)

    async def test_passes_payload_to_task(self):
        await self.scheduler.schedule('test', self.now, {'x': 1}, task_id='a')

        await self.scheduler.tick()

        self.assertEqual(self.task.calls[0].payload, {'x': 1})

    async def test_marks_finished_task_done(self):
        await self.scheduler.schedule('test', self.now, task_id='a')

        await self.scheduler.tick()

        task = await self.row('a')
        self.assertEqual(task.status, ScheduledTaskStatus.DONE)
        self.assertIsNotNone(task.finished_at)

    async def test_runs_due_tasks_in_order(self):
        await self.scheduler.schedule('test', self.now + timedelta(minutes=2), task_id='late')
        await self.scheduler.schedule('test', self.now + timedelta(minutes=1), task_id='early')
        self.advance(minutes=3)

        self.assertEqual(await self.scheduler.tick(), 2)

        self.assertEqual([t.id for t in self.task.calls], ['early', 'late'])

    async def test_schedule_with_existing_id_is_ignored(self):
        self.assertTrue(await self.scheduler.schedule('test', self.now + timedelta(minutes=5), task_id='a'))
        self.assertFalse(await self.scheduler.schedule('test', self.now + timedelta(hours=1), task_id='a'))

        self.advance(minutes=5)
        self.assertEqual(await self.scheduler.tick(), 1)

    async def test_schedule_generates_id(self):
        await self.scheduler.schedule('test', self.now)
        await self.scheduler.schedule('test', self.now)

        self.assertEqual(len({t.id for t in await self.conn.get_scheduled_tasks()}), 2)

    async def test_schedule_requires_registered_task(self):
        with self.assertRaises(ValueError):
            await self.scheduler.schedule('nope', self.now)

    async def test_register_rejects_duplicate_name(self):
        with self.assertRaises(ValueError):
            self.scheduler.register(RecordingTask())

    async def test_cancel(self):
        await self.scheduler.schedule('test', self.now, task_id='a')

        self.assertTrue(await self.scheduler.cancel('a'))
        self.assertFalse(await self.scheduler.cancel('a'))

        self.assertEqual(await self.scheduler.tick(), 0)
        self.assertEqual(self.task.calls, [])

    async def test_task_can_cancel_a_later_due_task(self):
        scheduler = self.scheduler

        class Canceller(Task):
            name = 'canceller'

            async def run(self, task: ScheduledTask) -> None:
                await scheduler.cancel('victim')

        scheduler.register(Canceller())
        await scheduler.schedule('canceller', self.now - timedelta(minutes=2), task_id='first')
        await scheduler.schedule('test', self.now - timedelta(minutes=1), task_id='victim')

        await scheduler.tick()

        self.assertEqual(self.task.calls, [])

    def during_next_refresh(self, action) -> list[asyncio.Task]:
        """
        Starts `action()` as a separate task right after the next refresh has read the db, which is
        the moment a `schedule` or `cancel` from elsewhere (a bot command, say) can interleave with it.
        """
        original = self.conn.get_scheduled_tasks
        started: list[asyncio.Task] = []

        async def read_then_interleave():
            snapshot = await original()
            started.append(asyncio.create_task(action()))
            # Give it the chance to finish before the refresh does. It is expected to be held back until
            # then, so this returns on the timeout - unless nothing makes it wait, which is what we check for.
            await asyncio.wait(started, timeout=0.1)
            return snapshot

        patcher = patch.object(self.conn, 'get_scheduled_tasks', read_then_interleave)
        patcher.start()
        self.addCleanup(patcher.stop)
        return started

    async def test_task_cancelled_during_refresh_does_not_run(self):
        await self.scheduler.schedule('test', self.now, task_id='victim')
        started = self.during_next_refresh(lambda: self.scheduler.cancel('victim'))

        self.assertEqual(await self.scheduler.tick(), 0)

        await asyncio.gather(*started)
        self.assertEqual(self.task.calls, [])
        self.assertEqual(await self.conn.get_scheduled_tasks(), [])

    async def test_task_scheduled_during_refresh_is_not_lost(self):
        started = self.during_next_refresh(lambda: self.scheduler.schedule('test', self.now, task_id='new'))

        await self.scheduler.tick()
        await asyncio.gather(*started)

        self.assertEqual(await self.scheduler.tick(), 1)  # without waiting for the next refresh
        self.assertEqual([t.id for t in self.task.calls], ['new'])

    async def test_task_can_schedule_another_task(self):
        scheduler = self.scheduler

        class Chainer(Task):
            name = 'chainer'

            async def run(self, task: ScheduledTask) -> None:
                await scheduler.schedule('test', scheduler.now(), task_id='child')

        scheduler.register(Chainer())
        await scheduler.schedule('chainer', self.now, task_id='parent')

        self.assertEqual(await scheduler.tick(), 1)
        self.assertEqual(await scheduler.tick(), 1)

        self.assertEqual([t.id for t in self.task.calls], ['child'])

    async def test_failed_task_is_not_retried(self):
        class Broken(Task):
            name = 'broken'

            async def run(self, task: ScheduledTask) -> None:
                raise RuntimeError('boom')

        self.scheduler.register(Broken())
        await self.scheduler.schedule('broken', self.now, task_id='a')

        self.assertEqual(await self.scheduler.tick(), 1)
        self.advance(hours=1)
        self.assertEqual(await self.scheduler.tick(), 0)

        task = await self.row('a')
        self.assertEqual(task.status, ScheduledTaskStatus.FAILED)
        self.assertEqual(task.error, 'RuntimeError: boom')

    async def test_unknown_handler_marks_task_failed(self):
        await self.conn.create_scheduled_task('a', 'removed', self.now)

        self.assertEqual(await self.scheduler.tick(), 1)

        task = await self.row('a')
        self.assertEqual(task.status, ScheduledTaskStatus.FAILED)
        self.assertIn('unknown handler', task.error)

    async def test_timeout_marks_task_failed(self):
        class Hangs(Task):
            name = 'hangs'

            async def run(self, task: ScheduledTask) -> None:
                await asyncio.sleep(10)

        self.scheduler.register(Hangs())
        await self.scheduler.schedule('hangs', self.now, task_id='a')

        with patch('QRServer.scheduler.scheduler.HANDLER_TIMEOUT_S', 0.05):
            await self.scheduler.tick()

        task = await self.row('a')
        self.assertEqual(task.status, ScheduledTaskStatus.FAILED)
        self.assertIn('TimeoutError', task.error)

    async def test_picks_up_tasks_added_to_db_on_refresh(self):
        await self.scheduler.tick()  # initial load
        await self.conn.create_scheduled_task('a', 'test', self.now)

        self.assertEqual(await self.scheduler.tick(), 0)  # not reloaded yet

        self.advance(seconds=self.config.scheduler_refresh_interval.get())
        self.assertEqual(await self.scheduler.tick(), 1)

    async def test_loads_pending_tasks_on_first_tick(self):
        await self.conn.create_scheduled_task('a', 'test', self.now - timedelta(days=3))  # due during downtime

        self.assertEqual(await self.scheduler.tick(), 1)

    async def test_interrupted_tasks_are_marked_failed_on_load(self):
        await self.conn.create_scheduled_task('a', 'test', self.now)
        await self.conn.update_scheduled_task_status('a', ScheduledTaskStatus.RUNNING)

        self.assertEqual(await self.scheduler.tick(), 0)

        task = await self.row('a')
        self.assertEqual(task.status, ScheduledTaskStatus.FAILED)
        self.assertEqual(task.error, 'interrupted by shutdown')
        self.assertEqual(self.task.calls, [])

    async def test_purges_old_finished_tasks_on_refresh(self):
        await self.scheduler.schedule('test', self.now, task_id='done')
        await self.scheduler.schedule('test', self.now, task_id='failed')
        await self.conn.create_scheduled_task('pending', 'test', self.now + timedelta(days=100))
        await self.conn.update_scheduled_task_status('failed', ScheduledTaskStatus.FAILED, 'boom')
        await self.scheduler.tick()

        # still within retention
        self.advance(days=29, seconds=self.config.scheduler_refresh_interval.get())
        await self.scheduler.tick()
        self.assertEqual({t.id for t in await self.conn.get_scheduled_tasks()}, {'done', 'failed', 'pending'})

        self.advance(days=2)
        await self.scheduler.tick()
        self.assertEqual([t.id for t in await self.conn.get_scheduled_tasks()], ['pending'])

    async def test_retention_is_configurable(self):
        self.config.set('scheduler.retention_days', 1)
        await self.scheduler.schedule('test', self.now, task_id='a')
        await self.scheduler.tick()

        self.advance(days=2)
        await self.scheduler.tick()

        self.assertEqual(await self.conn.get_scheduled_tasks(), [])


class SchedulerAutoscheduleTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.config = Config()
        self.conn = DbConnector(':memory:', self.config)
        await self.conn.connect()

        self.now = utc(2026, 5, 10, 9, 0, 0)
        self.scheduler = Scheduler(self.conn, self.config, clock=lambda: self.now)
        self.daily = DailyTask()
        self.manual = RecordingTask()
        self.scheduler.register(self.daily)
        self.scheduler.register(self.manual)

    async def asyncTearDown(self):
        await self.conn.close()

    async def rows(self) -> dict[str, ScheduledTask]:
        return {t.id: t for t in await self.conn.get_scheduled_tasks()}

    async def test_schedules_next_occurrence_of_autoscheduled_tasks_only(self):
        await self.scheduler.autoschedule()

        rows = await self.rows()
        self.assertEqual(set(rows), {'daily:2026-05-10'})
        self.assertEqual(rows['daily:2026-05-10'].run_at, utc(2026, 5, 10, 12))
        self.assertEqual(rows['daily:2026-05-10'].status, ScheduledTaskStatus.PENDING)

    async def test_autoschedule_is_idempotent(self):
        await self.scheduler.autoschedule()
        await self.scheduler.autoschedule()
        self.now = utc(2026, 5, 10, 10)
        await self.scheduler.autoschedule()

        self.assertEqual(len(await self.rows()), 1)

    async def test_autoschedule_skips_disabled_task(self):
        self.daily.enabled = False

        await self.scheduler.autoschedule()

        self.assertEqual(await self.rows(), {})

    async def test_run_schedules_next_occurrence(self):
        await self.scheduler.autoschedule()

        self.now = utc(2026, 5, 10, 12, 0, 5)
        self.assertEqual(await self.scheduler.tick(), 1)

        rows = await self.rows()
        self.assertEqual(set(rows), {'daily:2026-05-10', 'daily:2026-05-11'})
        self.assertEqual(rows['daily:2026-05-10'].status, ScheduledTaskStatus.DONE)
        self.assertEqual(rows['daily:2026-05-11'].status, ScheduledTaskStatus.PENDING)
        self.assertEqual(rows['daily:2026-05-11'].run_at, utc(2026, 5, 11, 12))

    async def test_failed_run_still_schedules_next_occurrence(self):
        class BrokenDaily(DailyTask):
            name = 'broken_daily'

            async def run(self, task: ScheduledTask) -> None:
                raise RuntimeError('boom')

        self.scheduler.register(BrokenDaily())
        await self.scheduler.autoschedule()

        self.now = utc(2026, 5, 10, 12, 0, 5)
        await self.scheduler.tick()

        rows = await self.rows()
        self.assertEqual(rows['broken_daily:2026-05-10'].status, ScheduledTaskStatus.FAILED)
        self.assertEqual(rows['broken_daily:2026-05-11'].status, ScheduledTaskStatus.PENDING)
        self.assertEqual(rows['broken_daily:2026-05-11'].run_at, utc(2026, 5, 11, 12))

    async def test_missed_occurrences_collapse_after_downtime(self):
        await self.scheduler.autoschedule()

        self.now = utc(2026, 5, 15, 9)  # the server was down for 5 days
        self.assertEqual(await self.scheduler.tick(), 1)  # the late run
        self.assertEqual(await self.scheduler.tick(), 0)  # nothing to catch up on

        self.assertEqual(len(self.daily.calls), 1)
        self.assertEqual(self.daily.calls[0].run_at, utc(2026, 5, 10, 12))
        rows = await self.rows()
        self.assertEqual(rows['daily:2026-05-15'].status, ScheduledTaskStatus.PENDING)
        self.assertEqual(rows['daily:2026-05-15'].run_at, utc(2026, 5, 15, 12))

    async def test_restart_after_downtime_does_not_duplicate_the_chain(self):
        await self.scheduler.autoschedule()
        restarted = Scheduler(self.conn, self.config, clock=lambda: utc(2026, 5, 15, 9))
        restarted.register(DailyTask())

        await restarted.autoschedule()
        await restarted.tick()

        # the stale occurrence ran once and the chain continues from today, once
        self.assertEqual(set(await self.rows()), {'daily:2026-05-10', 'daily:2026-05-15'})


class SchedulerLoopTest(unittest.IsolatedAsyncioTestCase):
    # The only test on the real clock: it checks that `run` wires autoscheduling and polling together.
    async def test_run_autoschedules_and_runs_due_tasks(self):
        config = Config()
        config.set('scheduler.poll_interval', 1)
        conn = DbConnector(':memory:', config)
        await conn.connect()
        scheduler = Scheduler(conn, config)
        fired = asyncio.Event()

        class Soon(Task):
            name = 'soon'

            async def run(self, task: ScheduledTask) -> None:
                fired.set()

            def next_run(self, after: datetime) -> datetime | None:
                return None if fired.is_set() else after - timedelta(seconds=1)

        scheduler.register(Soon())
        loop_task = asyncio.create_task(scheduler.run())
        try:
            await asyncio.wait_for(fired.wait(), timeout=5)
        finally:
            loop_task.cancel()
            await asyncio.gather(loop_task, return_exceptions=True)
            await conn.close()
