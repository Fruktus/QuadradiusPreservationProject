from abc import ABC, abstractmethod
from datetime import datetime
from typing import ClassVar

from QRServer.db.models import ScheduledTask


class Task(ABC):
    """
    A Task for Scheduler - includes handler and logic for run.
    Corresponds to ScheduledTask in DB.

    Register it in Scheduler, which will run it at the configured time.
    If the task is meant to be repeated, implement `next_run`.
    """
    name: ClassVar[str]

    @abstractmethod
    async def run(self, task: ScheduledTask) -> None:
        # actual task logic goes here
        pass

    def next_run(self, after: datetime) -> datetime | None:
        """
        If you want the task to be executed multiple times, set the next due date calculation here.

        For example, if `after` is 2026-10-29 and you want the task to run next month
        your code should return 2026-11-01

        Returns:
            datetime: The first occurrence strictly after `after`.
                None if the task is not autoscheduled (it is only scheduled explicitly) or is currently disabled.
        """
        return None

    def task_id(self, run_at: datetime) -> str:
        """
        The id of the db row for the occurrence at `run_at`.
        Being derived from the time is what makes autoscheduling idempotent:
        an occurrence which is already in the db is not added again.

        By default time is omitted, but if needed it can be overriden.
        """
        return f'{self.name}:{run_at:%Y-%m-%d}'
