import unittest
import uuid
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import patch

from QRServer.achievements.challenges.winter_2026 import WinterCalendar2026, days, power_groups
from QRServer.achievements.challenges.winter_2026.days import DAYS, WinterDay
from QRServer.achievements.challenges.winter_2026.power_groups import ALL_GROUPS, Power, PowerGroup
from QRServer.achievements.conditions.constants import GridSize, SquadronSize
from QRServer.achievements.manager import AchievementsManager
from QRServer.common.messages import GetPowerSquareMessage, Message, RemovePlayerMessage, UsePowerMessage
from QRServer.config import Config
from QRServer.db.connector import DbConnector
from QRServer.db.models import DbMatchReport, DbRecordedMessage
from QRServer.scheduler.tasks.event_embed import EventEmbedTask

EMBED_LIMITS = {'title': 256, 'description': 4096, 'field_value': 1024, 'total': 6000}

# The open progress query compares expires_at with the real clock, so it is frozen to a moment inside of the event
NOW = datetime(2026, 12, 12, 12, tzinfo=timezone.utc)


class FrozenDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        return NOW


@dataclass
class Played:
    """One match of the player. The defaults are a plain win which passes no day."""
    won: bool = True
    grid: str = GridSize.SMALL
    squadron: str = SquadronSize.MEDIUM
    pieces_left: int = 1
    seconds: int = 30 * 60
    messages: list[Message] = field(default_factory=list)


class EventTimeline:
    """Shared by the tests of the challenge, expects `challenge` to be set up"""
    challenge: WinterCalendar2026

    def opens_at(self, day: int) -> datetime:
        return self.challenge.EVENT_START + (day - 1) * self.challenge.DAY_LENGTH


# # # # # # # # # # # # #
# Content of the event  #
# # # # # # # # # # # # #

class PowerGroupsTest(unittest.TestCase):
    def test_unknown_codename_is_rejected(self):
        with self.assertRaises(ValueError):
            Power('NOT_A_POWER', 'Nothing')

    def test_power_twice_in_a_group_is_rejected(self):
        with self.assertRaises(ValueError):
            PowerGroup('Doubled', 'powers', (power_groups.DESTROY, power_groups.DESTROY))

    def test_ranged_power_includes_row_and_column_versions(self):
        for power in (power_groups.DESTROY, power_groups.ACIDIC, power_groups.KAMIKAZE, power_groups.INVERT):
            self.assertEqual(power.codenames, {power.codename, f'{power.codename}_ROW', f'{power.codename}_COL'})
            self.assertTrue(power.ranged)

    def test_single_power_has_only_its_own_codename(self):
        for power in (power_groups.MULTIPLY, power_groups.SNAKE_TUNNELING):
            self.assertEqual(power.codenames, {power.codename})
            self.assertFalse(power.ranged)

    def test_group_counts_every_version_of_its_members(self):
        for group in ALL_GROUPS:
            expected = set().union(*(member.codenames for member in group.members))
            self.assertEqual(group.codenames, expected, group.label)

    def test_group_labels_are_unique(self):
        labels = [group.label for group in ALL_GROUPS]
        self.assertEqual(len(labels), len(set(labels)))

    def test_describe_lists_members_and_mentions_versions_only_when_there_are_any(self):
        destructive = power_groups.DESTRUCTIVE_GROUP.describe()
        self.assertIn('**Destructive**', destructive)
        self.assertIn('Snake Tunneling', destructive)
        self.assertIn('Radial/Row/Column versions count', destructive)

        single = PowerGroup('Single', 'a single power', (power_groups.MULTIPLY,))
        self.assertNotIn('versions', single.describe())

    def test_destructive_and_malfunction_share_no_power(self):
        # day 22 needs both, a use must never count for both
        self.assertEqual(power_groups.DESTRUCTIVE_GROUP.codenames & power_groups.MALFUNCTION_GROUP.codenames, set())


class DaysTest(unittest.TestCase):
    def test_all_24_days_are_defined_once(self):
        self.assertEqual(sorted(day.day_number for day in DAYS), list(range(1, 25)))

    def test_every_day_has_prose_and_conditions(self):
        for day in DAYS:
            for text in (day.title, day.story, day.objective):
                self.assertTrue(text.strip(), f'day {day.day_number}')
                self.assertNotIn('{', text, f'day {day.day_number}: unformatted text')
            self.assertTrue(day.conditions(), f'day {day.day_number}')

    def test_conditions_are_not_shared_between_calls(self):
        for day in DAYS:
            self.assertIsNot(day.conditions(), day.conditions())
            for first, second in zip(day.conditions(), day.conditions()):
                self.assertIsNot(first, second, f'day {day.day_number}')

    def test_day_which_defines_groups_explains_them(self):
        for day in DAYS:
            for group in day.groups:
                self.assertIn(group.describe(), day.objective_details, f'day {day.day_number}')

    def test_day_with_no_groups_and_no_notes_has_no_details(self):
        self.assertEqual(days.Day01().objective_details, '')

    def test_day_must_define_its_prose(self):
        with self.assertRaises(TypeError):
            class Incomplete(WinterDay):
                day_number = 99
                title = 'No story'

                def conditions(self):
                    return []

    def test_day_must_define_conditions(self):
        class NoConditions(WinterDay):
            day_number = 99
            title = 'Title'
            story = 'Story'
            objective = 'Objective'

        with self.assertRaises(TypeError):
            NoConditions()  # type: ignore[abstract]


# # # # # # # # # # # # # # # # # # # #
# Posts, schedule and timing (unit)   #
# # # # # # # # # # # # # # # # # # # #

class WinterCalendar2026Test(EventTimeline, unittest.TestCase):
    BEFORE_EVENT = datetime(2026, 11, 25, tzinfo=timezone.utc)

    def setUp(self):
        self.challenge = WinterCalendar2026()

    def tasks(self, now: datetime):
        return self.challenge.scheduled_tasks(now)

    def day_of(self, started_at: datetime) -> int | None:
        day = self.challenge._day_of(SimpleNamespace(started_at=started_at))  # type: ignore[arg-type]
        return day.day_number if day else None

    def test_post_handler_is_the_embed_task(self):
        self.assertEqual(self.challenge.POST_HANDLER, EventEmbedTask.name)

    def test_event_spans_24_days_and_the_progress_outlives_it(self):
        self.assertEqual(self.challenge.EVENT_END - self.challenge.EVENT_START, 24 * self.challenge.DAY_LENGTH)
        self.assertEqual(self.challenge.expires_at, self.challenge.EVENT_END + self.challenge.GRACE)

    def test_day_of_a_match_is_decided_by_its_start(self):
        start = self.challenge.EVENT_START
        one_second = timedelta(seconds=1)
        self.assertIsNone(self.day_of(start - one_second))
        self.assertEqual(self.day_of(start), 1)
        self.assertEqual(self.day_of(self.opens_at(2) - one_second), 1)
        self.assertEqual(self.day_of(self.opens_at(2)), 2)
        self.assertEqual(self.day_of(self.opens_at(24)), 24)
        self.assertIsNone(self.day_of(self.challenge.EVENT_END))

    def test_progress_starts_empty_and_lists_the_days_done(self):
        self.assertEqual(self.challenge.decode_progress(self.challenge.initial_progress()), [])
        self.assertEqual(self.challenge.pretty_print_progress([]), 'Days done: 0/24')
        self.assertEqual(self.challenge.pretty_print_progress([1, 2, 5]), 'Days done: 3/24 (1, 2, 5)')

    def test_every_day_is_scheduled_before_the_event(self):
        tasks = self.tasks(self.BEFORE_EVENT)

        self.assertEqual([task.id for task in tasks], [f'winter-2026:day-{day:02d}' for day in range(1, 25)])
        for day, task in enumerate(tasks, start=1):
            self.assertEqual(task.handler, 'event_embed')
            self.assertEqual(task.run_at, self.opens_at(day))

    def test_finished_days_are_not_scheduled_again(self):
        # a restart in the middle of day 10: the day which is in progress is still posted (its run_at is in the past)
        tasks = self.tasks(self.opens_at(10) + timedelta(hours=3))

        self.assertEqual([task.id for task in tasks], [f'winter-2026:day-{day:02d}' for day in range(10, 25)])
        self.assertLess(tasks[0].run_at, self.opens_at(10) + timedelta(hours=3))

    def test_nothing_is_scheduled_after_the_event(self):
        self.assertEqual(self.tasks(self.challenge.EVENT_END), [])

    def test_scheduling_is_repeatable(self):
        self.assertEqual(self.tasks(self.BEFORE_EVENT), self.tasks(self.BEFORE_EVENT))

    def test_posts_fit_in_discord_limits(self):
        for task in self.tasks(self.BEFORE_EVENT):
            embed = task.payload
            values = [field['value'] for field in embed['fields']]
            total = (len(embed['title']) + len(embed['description']) + len(embed['footer']['text'])
                     + sum(len(field['name']) + len(field['value']) for field in embed['fields']))
            self.assertLessEqual(len(embed['title']), EMBED_LIMITS['title'], task.id)
            self.assertLessEqual(len(embed['description']), EMBED_LIMITS['description'], task.id)
            self.assertLessEqual(max(map(len, values)), EMBED_LIMITS['field_value'], task.id)
            self.assertLessEqual(total, EMBED_LIMITS['total'], task.id)

    def test_post_describes_the_day(self):
        for day, task in zip(DAYS, self.tasks(self.BEFORE_EVENT)):
            embed = task.payload
            self.assertIn(f'Day {day.day_number} ', embed['title'])
            self.assertIn(day.title, embed['title'])
            self.assertIn(day.story, embed['description'])
            self.assertIn(day.objective, embed['description'])
            self.assertTrue(embed['description'].endswith(self.challenge.SPACER))

            names = [field['name'] for field in embed['fields']]
            self.assertEqual('📖 Details' in names, bool(day.objective_details), f'day {day.day_number}')
            progress = next(field for field in embed['fields'] if 'Progress' in field['name'])
            self.assertIn(f'/progress {self.challenge.key}', progress['value'])

    def test_post_times_are_the_days_boundaries(self):
        embed = self.tasks(self.BEFORE_EVENT)[1].payload  # day 2
        opens, closes = int(self.opens_at(2).timestamp()), int(self.opens_at(3).timestamp())
        values = ' '.join(field['value'] for field in embed['fields'])
        self.assertIn(f'<t:{opens}:f>', values)
        self.assertIn(f'<t:{closes}:f>', values)

    def test_event_runs_from_december_1st_noon_to_december_25th_noon_utc(self):
        self.assertEqual(self.challenge.EVENT_START, datetime(2026, 12, 1, 12, tzinfo=timezone.utc))
        self.assertEqual(self.challenge.EVENT_END, datetime(2026, 12, 25, 12, tzinfo=timezone.utc))


# # # # # # # # # # # # # # # # # # # # # # #
# The whole event, with the db (integration) #
# # # # # # # # # # # # # # # # # # # # # # #

class WinterCalendar2026EventTest(EventTimeline, unittest.IsolatedAsyncioTestCase):
    KEY = WinterCalendar2026.key
    REPORT_ONLY_DAYS = {3, 5, 17, 23, 24}  # days with no recording condition

    # Messages of a match

    @staticmethod
    def uses(codenames, count: int) -> list[Message]:
        """`count` power uses cycling through the codenames, so the Row and Column versions are used too"""
        names = sorted(codenames)
        return [UsePowerMessage.new(names[i % len(names)], 0) for i in range(count)]

    @staticmethod
    def distinct_uses(count: int) -> list[Message]:
        names = sorted(set().union(*(group.codenames for group in power_groups.ALL_GROUPS)))
        return [UsePowerMessage.new(name, 0) for name in names[:count]]

    @staticmethod
    def orbs(count: int) -> list[Message]:
        return [GetPowerSquareMessage.new(0, 0) for _ in range(count)]

    @staticmethod
    def removals(count: int) -> list[Message]:
        """Removals in a row, which is what one area power does"""
        return [RemovePlayerMessage.new(piece) for piece in range(count)]

    @classmethod
    def scattered_removals(cls, count: int) -> list[Message]:
        """The same number of removals, with another action between each of them"""
        return [message for piece in range(count)
                for message in (RemovePlayerMessage.new(piece), *cls.uses(['MULTIPLY'], 1))]

    @classmethod
    def scenarios(cls) -> dict[int, tuple[Played, Played]]:
        """What the player has to do on each day: (passes the day, nearly passes it). The numbers are read from the
        days themselves, so retuning a threshold does not break the test. The failing match is the closest miss of
        the day."""
        d = days
        pg = power_groups
        uses, distinct_uses, orbs = cls.uses, cls.distinct_uses, cls.orbs
        removals, scattered_removals = cls.removals, cls.scattered_removals
        return {
            1: (Played(messages=orbs(d.Day01.ORBS)), Played(messages=orbs(d.Day01.ORBS - 1))),
            2: (Played(messages=uses(pg.MULTIPLY.codenames, 1)), Played(messages=uses(['DESTROY'], 5))),
            3: (Played(grid=GridSize.MAXIMUM), Played(grid=GridSize.SMALL)),
            4: (Played(messages=uses(pg.ENHANCEMENT_GROUP.codenames, d.Day04.ENHANCEMENT_USES)),
                Played(messages=uses(pg.ENHANCEMENT_GROUP.codenames, d.Day04.ENHANCEMENT_USES - 1)
                       + uses(['DESTROY'], 10))),
            5: (Played(pieces_left=d.Day05.PIECES_LEFT), Played(pieces_left=d.Day05.PIECES_LEFT - 1)),
            6: (Played(messages=uses(['DESTROY'], d.Day06.POWER_USES)),
                Played(messages=uses(['DESTROY'], d.Day06.POWER_USES - 1))),
            7: (Played(messages=uses(pg.MOVEMENT_GROUP.codenames, d.Day07.MOVEMENT_USES)),
                Played(messages=uses(pg.MOVEMENT_GROUP.codenames, d.Day07.MOVEMENT_USES - 1)
                       + uses(['DESTROY'], 10))),
            8: (Played(messages=uses(pg.SNAKE_TUNNELING.codenames, 1)), Played(messages=uses(['DESTROY'], 5))),
            9: (Played(messages=uses(pg.DESTRUCTIVE_GROUP.codenames, d.Day09.DESTRUCTIVE_USES)),
                Played(messages=uses(pg.DESTRUCTIVE_GROUP.codenames, d.Day09.DESTRUCTIVE_USES - 1)
                       + uses(['MULTIPLY'], 10))),
            10: (Played(messages=removals(d.Day10.COMBO_DESTROYED_PIECES)),
                 Played(messages=scattered_removals(d.Day10.COMBO_DESTROYED_PIECES + 5))),
            11: (Played(messages=orbs(d.Day11.ORBS) + removals(d.Day11.PIECES_DESTROYED)),
                 Played(messages=orbs(d.Day11.ORBS) + removals(d.Day11.PIECES_DESTROYED - 1))),
            12: (Played(messages=uses(pg.TERRAFORM_GROUP.codenames, d.Day12.TERRAFORM_USES)),
                 Played(won=False, messages=uses(pg.TERRAFORM_GROUP.codenames, 5))),
            13: (Played(messages=uses(pg.ORB_SPY.codenames, d.Day13.ORB_SPY_USES)),
                 Played(messages=uses(['DESTROY'], 10))),
            14: (Played(messages=uses(pg.RELOCATE.codenames, 1)), Played(messages=uses(['DESTROY'], 5))),
            15: (Played(messages=uses(pg.INVENTORY_GROUP.codenames, d.Day15.INVENTORY_USES)),
                 Played(messages=uses(pg.INVENTORY_GROUP.codenames, d.Day15.INVENTORY_USES - 1)
                        + uses(['DESTROY'], 10))),
            16: (Played(messages=distinct_uses(d.Day16.DISTINCT_POWERS)),
                 Played(messages=distinct_uses(d.Day16.DISTINCT_POWERS - 1) + distinct_uses(1) * 20)),
            17: (Played(grid=GridSize.NINEXNINE), Played(won=False, grid=GridSize.NINEXNINE)),
            18: (Played(messages=orbs(d.Day18.ORBS) + uses(['DESTROY'], d.Day18.POWER_USES)),
                 Played(messages=orbs(d.Day18.ORBS - 1) + uses(['DESTROY'], d.Day18.POWER_USES))),
            19: (Played(messages=orbs(d.Day19.ORBS)), Played(messages=orbs(d.Day19.ORBS - 1))),
            20: (Played(messages=orbs(d.Day20.ORBS)), Played(won=False, messages=orbs(d.Day20.ORBS))),
            21: (Played(messages=scattered_removals(d.Day21.PIECES_DESTROYED)),
                 Played(messages=scattered_removals(d.Day21.PIECES_DESTROYED - 1))),
            22: (Played(messages=uses(pg.DESTRUCTIVE_GROUP.codenames, d.Day22.DESTRUCTIVE_USES)
                        + uses(pg.MALFUNCTION_GROUP.codenames, d.Day22.MALFUNCTION_USES)),
                 Played(messages=uses(pg.DESTRUCTIVE_GROUP.codenames, d.Day22.DESTRUCTIVE_USES))),
            23: (Played(seconds=d.Day23.MINUTES * 60), Played(seconds=d.Day23.MINUTES * 60 + 1)),
            24: (Played(grid=GridSize.LARGE, squadron=SquadronSize.LARGE),
                 Played(grid=GridSize.LARGE, squadron=SquadronSize.MEDIUM)),
        }

    # Set up

    async def asyncSetUp(self):
        self.config = Config()
        self.conn = DbConnector(':memory:', self.config)
        await self.conn.connect()
        self.challenge = WinterCalendar2026()
        self.manager = AchievementsManager(self.config, self.conn, [self.challenge])
        self.player = await self.conn.create_member('player', b'password', '11111111111')
        self.rival = await self.conn.create_member('rival', b'password', '22222222222')
        self.scenarios_by_day = self.scenarios()

        created_at = int(datetime(2026, 11, 7, tzinfo=timezone.utc).timestamp())
        async with self.conn._transaction('w') as c:
            # the reward exists in the db once the achievements migration is merged, then this is a no-op
            await c.execute(
                "insert or ignore into achievements (key, name, description, created_at) values (?, ?, ?, ?)",
                (self.challenge.reward_key, self.challenge.display_name, 'Test achievement.', created_at))

        patcher = patch('QRServer.db.connector.datetime', FrozenDatetime)
        patcher.start()
        self.addCleanup(patcher.stop)

    async def asyncTearDown(self):
        await self.conn.close()

    # Playing and checking

    async def play(self, played: Played, started_at: datetime, user: str | None = None) -> None:
        """Dispatch a match of the user (the player by default) against the rival, as the game server would"""
        user = user or self.player
        winner, loser = (user, self.rival) if played.won else (self.rival, user)
        report = DbMatchReport(
            match_id=str(uuid.uuid4()),
            winner_id=winner,
            loser_id=loser,
            winner_pieces_left=played.pieces_left if played.won else 1,
            loser_pieces_left=1 if played.won else played.pieces_left,
            move_counter=20,
            grid_size=played.grid,
            squadron_size=played.squadron,
            started_at=started_at,
            finished_at=started_at + timedelta(seconds=played.seconds),
            is_ranked=True,
            is_void=False,
        )
        recording = [
            DbRecordedMessage(
                timestamp=started_at,
                sender_id=user,
                receiver_id=self.rival,
                message_type=message.message_type_id,
                message=message.to_data()[:-1],
            )
            for message in played.messages
        ]
        await self.manager.dispatch(report, recording)

    async def done_days(self, user: str | None = None) -> list[int]:
        row = await self.conn.get_challenge_progress(user or self.player, self.KEY)
        return self.challenge.decode_progress(row.progress) if row else []

    async def awarded(self, user: str | None = None) -> list[str]:
        return [a.achievement_key for a in await self.conn.get_user_achievements(user or self.player)]

    # Tests

    async def test_every_day_of_the_event_in_one_pass(self):
        for day in range(1, 25):
            passes, nearly = self.scenarios_by_day[day]
            opens = self.opens_at(day)
            before = list(range(1, day))

            await self.play(nearly, opens + timedelta(hours=1))
            self.assertEqual(await self.done_days(), before, f'day {day}: the closest miss counted')

            await self.play(passes, opens + timedelta(hours=2))
            self.assertEqual(await self.done_days(), before + [day], f'day {day}: the passing match did not count')

            await self.play(passes, opens + timedelta(hours=3))
            self.assertEqual(await self.done_days(), before + [day], f'day {day}: a repeat changed the progress')

            if day < 24:
                self.assertEqual(await self.awarded(), [], f'day {day}: rewarded too early')

        progress = await self.conn.get_challenge_progress(self.player, self.KEY)
        self.assertEqual(progress.completed_at, self.opens_at(24) + timedelta(hours=2, seconds=passes.seconds))
        self.assertEqual(await self.awarded(), [self.challenge.reward_key])

    async def test_opponent_only_gets_the_days_which_do_not_need_a_recording(self):
        for day in range(1, 25):
            await self.play(self.scenarios_by_day[day][0], self.opens_at(day) + timedelta(hours=2))

        rival_days = set(await self.done_days(self.rival))
        self.assertTrue({3, 24} <= rival_days, rival_days)
        self.assertTrue(rival_days <= self.REPORT_ONLY_DAYS, rival_days)
        self.assertEqual(await self.awarded(self.rival), [])

    async def test_a_missed_day_stays_missed(self):
        for day in [1, *range(3, 25)]:
            await self.play(self.scenarios_by_day[day][0], self.opens_at(day) + timedelta(hours=2))
        # day 2 is done on day 3, which has its own task
        await self.play(self.scenarios_by_day[2][0], self.opens_at(3) + timedelta(hours=5))

        self.assertEqual(await self.done_days(), [1, *range(3, 25)])
        self.assertEqual(await self.awarded(), [])
        progress = await self.conn.get_challenge_progress(self.player, self.KEY)
        self.assertIsNone(progress.completed_at)

    async def test_days_are_decided_by_the_start_of_the_match(self):
        day_end = self.opens_at(2)
        await self.play(self.scenarios_by_day[1][0], day_end - timedelta(seconds=1))
        await self.play(self.scenarios_by_day[2][0], day_end)
        self.assertEqual(await self.done_days(), [1, 2])

        # a match of day 3 which started at the very end of it and finishes after it
        late = replace(self.scenarios_by_day[3][0], seconds=60 * 60)
        await self.play(late, self.opens_at(4) - timedelta(minutes=5))
        self.assertEqual(await self.done_days(), [1, 2, 3])

    async def test_matches_outside_of_the_event_count_for_nothing(self):
        start = self.challenge.EVENT_START
        await self.play(self.scenarios_by_day[1][0], start - timedelta(seconds=1))
        await self.play(self.scenarios_by_day[1][0], self.challenge.EVENT_END)
        await self.play(self.scenarios_by_day[1][0], self.challenge.EVENT_END + timedelta(days=3))

        self.assertEqual(await self.done_days(), [])
        self.assertIsNone(await self.conn.get_challenge_progress(self.player, self.KEY))

    async def test_the_posts_of_every_day_are_scheduled(self):
        with patch('QRServer.achievements.manager.datetime', FrozenDatetime):
            await self.manager.schedule_tasks()
            await self.manager.schedule_tasks()  # a restart does not duplicate anything

        tasks = {task.id: task for task in await self.conn.get_scheduled_tasks()}
        # NOW is during day 12, the finished days are not created
        self.assertEqual(sorted(tasks), [f'{self.KEY}:day-{day:02d}' for day in range(12, 25)])
        for day in range(12, 25):
            task = tasks[f'{self.KEY}:day-{day:02d}']
            self.assertEqual(task.run_at, self.opens_at(day))
            self.assertIn(f'Day {day} ', task.payload['title'])
