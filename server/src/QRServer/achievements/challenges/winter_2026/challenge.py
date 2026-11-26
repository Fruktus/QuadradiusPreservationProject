from datetime import datetime, timedelta, timezone

from QRServer.achievements.challenge import Challenge, Outcome
from QRServer.achievements.challenges.winter_2026.days import DAYS, WinterDay
from QRServer.db.models import DbMatchReport, DbRecordedMessage, ScheduledTaskData


class WinterCalendar2026(Challenge):
    """
    Winter Calendar 2026 event - The Great Christmas Mix-Up.

    One task a day, complete them all to get the reward.
    A day which was missed stays missed.
    Every day starts and ends at 12:00 UTC.
    The progress is the sorted list of the completed days.
    The challenge also publishes the post of every day.
    """

    key = 'winter-2026'
    display_name = 'Winter Calendar 2026'
    reward_key = 'winter_2026'

    EVENT_START = datetime(2026, 12, 1, 12, tzinfo=timezone.utc)
    DAY_LENGTH = timedelta(days=1)
    EVENT_END = EVENT_START + 24 * DAY_LENGTH

    GRACE = timedelta(days=7)  # the progress is still shown (and the reward reconciled) after the event
    POST_HANDLER = 'event_embed'  # Scheduled Discord Embed poster task
    POST_COLOR = 0xC0392B  # Christmas red
    SPACER = '\u200b'  # Zero-width space, lets whitespace formatting survive

    expires_at = EVENT_END + GRACE  # Include grace time to allow reconciliation

    # Instance attribute in tests can be overridden to run on a subset of days
    _days: dict[int, WinterDay] = {day.day_number: day for day in DAYS}

    # # # # # # # # # # # # # # # # #
    # Required Challenge functions  #
    # # # # # # # # # # # # # # # # #

    def applies(self, report: DbMatchReport, recording: list[DbRecordedMessage]) -> bool:
        # Cheap preflight check - did match start within event time?
        return self._day_of(report) is not None

    def initial_progress(self) -> str:
        return self.encode_progress([])

    def pretty_print_progress(self, progress: list[int]) -> str:
        days = ', '.join(map(str, progress))
        return f'Days done: {len(progress)}/{len(self._days)}' + (f' ({days})' if days else '')

    def run(self, user_id: str, progress: list[int], report: DbMatchReport,
            recording: list[DbRecordedMessage]) -> Outcome | None:
        # None - no change, Outcome - update needed
        day = self._day_of(report)
        if day is None or day.day_number in progress:
            return None

        if not self.match_conditions_met(user_id, report, recording, day.conditions()):
            return None

        done = sorted({*progress, day.day_number})
        return Outcome(done, completed=len(done) == len(self._days))

    def scheduled_tasks(self, now: datetime) -> list[ScheduledTaskData]:
        """This event is time-dependent, so it needs daily posts with objectives.
        Idempotent before posting, not (re)created if its already past their time"""
        return [
            ScheduledTaskData(self._task_id(day), self.POST_HANDLER, self._opens_at(day), self._embed(day))
            for day in self._days.values()
            if self._closes_at(day) > now
        ]

    # # # # # # # # # # #
    # Dedicated helper  #
    # # # # # # # # # # #

    def _opens_at(self, day: WinterDay) -> datetime:
        return self.EVENT_START + (day.day_number - 1) * self.DAY_LENGTH

    def _closes_at(self, day: WinterDay) -> datetime:
        return self._opens_at(day) + self.DAY_LENGTH

    def _day_of(self, report: DbMatchReport) -> WinterDay | None:
        """The day a match counts for by its start time (None if outside of the event or for an undefined day)."""
        moment = report.started_at
        if not self.EVENT_START <= moment < self.EVENT_END:
            return None
        return self._days.get((moment - self.EVENT_START) // self.DAY_LENGTH + 1)

    def _task_id(self, day: WinterDay) -> str:
        """Since this challenge is using scheduled tasks, its also responsible for generating their ids.
        They need to be stable across restarts and unique in the scheduled_tasks table."""
        return f'{self.key}:day-{day.day_number:02d}'

    def _embed(self, day: WinterDay) -> dict:
        """Build the nicely formatted embed for the scheduled task"""
        opens = int(self._opens_at(day).timestamp())
        closes = int(self._closes_at(day).timestamp())
        fields = [
            {'name': '🕛 Day starts', 'value': f'<t:{opens}:f>', 'inline': True},
            {'name': '⏳ Day ends', 'value': f'<t:{closes}:f> (<t:{closes}:R>)', 'inline': True},
            {'name': '📊 Progress', 'value': f'`/progress {self.key}`', 'inline': True},
        ]
        if day.objective_details:
            fields.insert(0, {
                'name': '📖 Details', 'value': f'{day.objective_details}\n{self.SPACER}', 'inline': False})
        return {
            'title': f'🎄  Day {day.day_number} · {day.title}  🎄',
            'color': self.POST_COLOR,
            'description': f'{day.story}\n\n**Objective:** {day.objective}\n{self.SPACER}',
            'fields': fields,
            'footer': {'text': f'🎁 Complete all {len(self._days)} days for the reward'},
        }
