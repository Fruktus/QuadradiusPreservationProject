import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import Callable

from QRServer.config import Config
from QRServer.db.connector import DbConnector
from QRServer.db.models import ScheduledTask, ScheduledTaskStatus
from QRServer.scheduler.task import Task

log = logging.getLogger('qr.scheduler')

HANDLER_TIMEOUT_S = 300  # single task timeout


class Scheduler:
    """
    Runs registered tasks at the configured target datetime.
    Tasks are backed by db, so they can be retrieved on server restart.
    The tasks are executed as soon as possible after their due date.
    If server was down at that time and task is still pending, it will run immediately on next start.

    Tasks are one-off.
    If they are meant to repeat, then they need to implement `Task.next_run` - if there is no
    task already scheduled, then scheduler will add it to db.

    Pending tasks are kept in memory and checked every `scheduler.poll_interval` seconds.

    Task handlers run outside of the lock, so they are free to schedule or cancel other tasks.
    `schedule`, `cancel`, the reload and claiming a due task are guarded with a lock,
    so a task which was cancelled while the list is being reloaded (for example due to bot command)
    doesn't run anyway.

    The list is reloaded from the db every `scheduler.refresh_interval` seconds,
    which also removes finished tasks older than `scheduler.retention_days`.

    There are no retries: a task which raises (or times out) is marked as failed.
    A task which was running when the server went down is marked as failed as well,
    as there is no telling how far it got.
    """

    def __init__(self, connector: DbConnector, config: Config,
                 clock: Callable[[], datetime] | None = None):
        self.connector = connector
        self.config = config
        self._clock = clock or (lambda: datetime.now(timezone.utc))
        self._tasks: dict[str, Task] = {}
        self._pending: dict[str, ScheduledTask] = {}
        self._last_refresh: datetime | None = None
        self._lock = asyncio.Lock()

    def now(self) -> datetime:
        return self._clock()

    def register(self, task: Task) -> None:
        if task.name in self._tasks:
            raise ValueError(f'A task named "{task.name}" is already registered')
        self._tasks[task.name] = task

    async def schedule(self, handler: str, run_at: datetime, payload: dict | None = None,
                       task_id: str | None = None) -> bool:
        """
        Schedules a one-off task.

        Args:
            task_id: Makes scheduling idempotent: a task with an already existing id is left untouched.
                Random uuid if omitted.

        Returns:
            bool: False if a task with the given id already exists, True otherwise
        """
        async with self._lock:
            return await self._schedule(handler, run_at, payload, task_id)

    async def _schedule(self, handler: str, run_at: datetime, payload: dict | None, task_id: str | None) -> bool:
        # Caller holds the lock
        if handler not in self._tasks:
            raise ValueError(f'No task registered under the name "{handler}"')

        task_id = task_id or str(uuid.uuid4())
        run_at = run_at.astimezone(timezone.utc)
        if not await self.connector.create_scheduled_task(task_id, handler, run_at, payload):
            return False

        self._pending[task_id] = ScheduledTask(
            id=task_id, handler=handler, payload=payload or {}, run_at=run_at, status=ScheduledTaskStatus.PENDING,
            error=None, created_at=self._clock(), started_at=None, finished_at=None)
        return True

    async def cancel(self, task_id: str) -> bool:
        async with self._lock:
            self._pending.pop(task_id, None)
            return await self.connector.delete_scheduled_task(task_id)

    async def autoschedule(self) -> None:
        """
        Ensure that registered repeating tasks are scheduled and in db.
        """
        async with self._lock:
            for task in self._tasks.values():
                await self._schedule_next(task)

    async def _schedule_next(self, task: Task) -> None:
        # the caller holds the lock
        run_at = task.next_run(self._clock())  # Get the next run due date from task
        if run_at is not None:
            await self._schedule(task.name, run_at, None, task.task_id(run_at))

    async def run(self) -> None:
        try:
            await self.autoschedule()
        except Exception:
            log.exception('Autoscheduling failed')

        log.info(f'Scheduled {len(self._pending)} task{"" if len(self._pending) == 1 else "s"}')

        while True:
            try:
                num_tasks_ran = await self.tick()
                if num_tasks_ran > 0:
                    log.info(f'Ran {num_tasks_ran} task{"" if num_tasks_ran == 1 else "s"}')
            except Exception:
                log.exception('Scheduler iteration failed')
            await asyncio.sleep(self.config.scheduler_poll_interval.get())

    async def tick(self) -> int:
        """
        Reloads the task list if it is time to, then runs the tasks which are due, earliest first.

        Returns:
            int: Number of tasks run (those which were cancelled after they became due are not counted)
        """
        now = self._clock()
        if (self._last_refresh is None
                or now - self._last_refresh >= timedelta(seconds=self.config.scheduler_refresh_interval.get())):
            async with self._lock:
                await self._refresh(now)

        due = sorted((t for t in self._pending.values() if t.run_at <= now), key=lambda t: (t.run_at, t.created_at))
        num_ran = 0
        for task in due:
            if await self._execute(task):
                num_ran += 1
        return num_ran

    async def _refresh(self, now: datetime) -> None:
        retention = timedelta(days=self.config.scheduler_retention_days.get())
        pending: dict[str, ScheduledTask] = {}

        for task in await self.connector.get_scheduled_tasks():
            if task.status == ScheduledTaskStatus.PENDING:
                pending[task.id] = task
            elif task.status == ScheduledTaskStatus.RUNNING:
                # tasks are only run by this loop, so nothing can legitimately be running while it refreshes
                log.warning(f'Task {task.id} was interrupted by a shutdown, marking as failed')
                await self.connector.update_scheduled_task_status(
                    task.id, ScheduledTaskStatus.FAILED, 'interrupted by shutdown')
            elif task.finished_at is not None and now - task.finished_at >= retention:
                await self.connector.delete_scheduled_task(task.id)

        self._pending = pending
        self._last_refresh = now

    async def _execute(self, scheduled: ScheduledTask) -> bool:
        """
        Returns:
            bool: False if the task was cancelled (or dropped by a reload) before it could be executed
        """
        # Once the scheduler enters this block the task run cannot be cancelled anymore
        # Handlers themselves don't need the lock - they don't directly modify
        # the scheduler's internal state and they may run for long time, so we don't
        # want to block the scheduler for all that time
        async with self._lock:
            if self._pending.pop(scheduled.id, None) is None:
                return False

            task = self._tasks.get(scheduled.handler)
            if task is None:
                log.error(f'Task {scheduled.id} refers to unknown handler "{scheduled.handler}", marking as failed')
                await self.connector.update_scheduled_task_status(
                    scheduled.id, ScheduledTaskStatus.FAILED, f'unknown handler: {scheduled.handler}')
                return True

            # If task repeats, schedule it as soon as possible so in case of errors it'd be in db
            try:
                await self._schedule_next(task)
            except Exception:
                log.exception(f'Could not schedule the next occurrence of task "{task.name}"')

            await self.connector.update_scheduled_task_status(scheduled.id, ScheduledTaskStatus.RUNNING)

        log.debug(f'Running task {scheduled.id}, scheduled for {scheduled.run_at}')
        try:
            async with asyncio.timeout(HANDLER_TIMEOUT_S):
                await task.run(scheduled)
        except Exception as e:
            log.exception(f'Task {scheduled.id} failed')
            await self.connector.update_scheduled_task_status(
                scheduled.id, ScheduledTaskStatus.FAILED, f'{type(e).__name__}: {e}')
        else:
            await self.connector.update_scheduled_task_status(scheduled.id, ScheduledTaskStatus.DONE)
        return True
