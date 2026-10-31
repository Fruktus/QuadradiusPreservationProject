import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

from QRServer.common.classes import GameResultHistory, MonthlySummary, RankingEntry
from QRServer.config import Config
from QRServer.db.connector import DbConnector
from QRServer.db.models import ScheduledTask, ScheduledTaskStatus
from QRServer.discord.bot import DiscordBot
from QRServer.scheduler.scheduler import Scheduler
from QRServer.scheduler.tasks.monthly_leaderboard import MonthlyLeaderboardTask

build_embed = MonthlyLeaderboardTask.build_embed


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


def entry(username: str, wins: int, games: int) -> RankingEntry:
    return RankingEntry(username=username, user_id=f'id-{username}', wins=wins, games=games)


def match(player_won: str, player_lost: str, duration_s: int, moves: int) -> GameResultHistory:
    start = utc(2026, 10, 5, 12)
    return GameResultHistory(
        player_won=player_won,
        player_lost=player_lost,
        won_score=5,
        lost_score=0,
        start=start,
        finish=start + timedelta(seconds=duration_s),
        moves=moves,
    )


def summary(ranking: list[RankingEntry] | None = None, champion_streak: int = 1,
            longest_match: GameResultHistory | None = None,
            most_moves_match: GameResultHistory | None = None) -> MonthlySummary:
    return MonthlySummary(
        ranking=ranking if ranking is not None else [entry('alice', 12, 15), entry('bob', 8, 15)],
        champion_streak=champion_streak,
        longest_match=longest_match,
        most_moves_match=most_moves_match,
    )


def scheduled(run_at: datetime) -> ScheduledTask:
    return ScheduledTask(
        id='a', handler='monthly_leaderboard', payload={}, run_at=run_at, status=ScheduledTaskStatus.RUNNING,
        error=None, created_at=run_at, started_at=run_at, finished_at=None)


class MonthlyLeaderboardTaskTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.connector = MagicMock(spec=DbConnector)
        self.connector.get_monthly_summary = AsyncMock(return_value=summary())
        self.bot = MagicMock(spec=DiscordBot)
        self.bot.leaderboard_channel_id = '555'
        self.bot.send_embed = AsyncMock()
        self.task = MonthlyLeaderboardTask(self.connector, self.bot)

    def test_next_run_is_the_first_of_next_month(self):
        self.assertEqual(self.task.next_run(utc(2026, 10, 15, 12)), utc(2026, 11, 1))

    def test_next_run_on_the_first_is_the_following_month(self):
        self.assertEqual(self.task.next_run(utc(2026, 11, 1)), utc(2026, 12, 1))

    def test_next_run_is_none_without_leaderboard_channel(self):
        self.bot.leaderboard_channel_id = ''

        self.assertIsNone(self.task.next_run(utc(2026, 10, 15)))

    async def test_run_reports_the_month_before_the_scheduled_time(self):
        await self.task.run(scheduled(utc(2026, 11, 1)))

        self.connector.get_monthly_summary.assert_awaited_once_with(2026, 10)

    async def test_run_in_january_reports_december_of_previous_year(self):
        await self.task.run(scheduled(utc(2027, 1, 1)))

        self.connector.get_monthly_summary.assert_awaited_once_with(2026, 12)

    async def test_run_posts_to_the_leaderboard_channel(self):
        await self.task.run(scheduled(utc(2026, 11, 1)))

        self.bot.send_embed.assert_awaited_once()
        self.assertEqual(self.bot.send_embed.call_args.args[0], '555')

    async def test_run_posts_the_summary_of_the_month(self):
        await self.task.run(scheduled(utc(2026, 11, 1)))

        embed = self.bot.send_embed.call_args.args[1]
        self.assertIn('October 2026', embed['title'])

    async def test_run_does_not_post_when_no_games_were_played(self):
        self.connector.get_monthly_summary.return_value = summary(ranking=[])

        await self.task.run(scheduled(utc(2026, 11, 1)))

        self.bot.send_embed.assert_not_awaited()

    async def test_run_propagates_send_errors(self):
        # so that the scheduler marks the task as failed
        self.bot.send_embed.side_effect = RuntimeError('boom')

        with self.assertRaises(RuntimeError):
            await self.task.run(scheduled(utc(2026, 11, 1)))

    async def test_run_does_nothing_without_leaderboard_channel(self):
        self.bot.leaderboard_channel_id = ''

        await self.task.run(scheduled(utc(2026, 11, 1)))

        self.connector.get_monthly_summary.assert_not_awaited()
        self.bot.send_embed.assert_not_awaited()


class MonthlyLeaderboardSchedulingTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.config = Config()
        self.conn = DbConnector(':memory:', self.config)
        await self.conn.connect()

        connector = MagicMock(spec=DbConnector)
        connector.get_monthly_summary = AsyncMock(return_value=summary())
        self.get_monthly_summary = connector.get_monthly_summary
        self.bot = MagicMock(spec=DiscordBot)
        self.bot.leaderboard_channel_id = '555'
        self.bot.send_embed = AsyncMock()

        self.now = utc(2026, 10, 31, 12)
        self.scheduler = Scheduler(self.conn, self.config, clock=lambda: self.now)
        self.scheduler.register(MonthlyLeaderboardTask(connector, self.bot))

    async def asyncTearDown(self):
        await self.conn.close()

    async def rows(self) -> dict[str, ScheduledTask]:
        return {t.id: t for t in await self.conn.get_scheduled_tasks()}

    async def test_autoschedule_adds_the_first_of_next_month(self):
        await self.scheduler.autoschedule()

        rows = await self.rows()
        self.assertEqual(set(rows), {'monthly_leaderboard:2026-11-01'})
        self.assertEqual(rows['monthly_leaderboard:2026-11-01'].run_at, utc(2026, 11, 1))

    async def test_autoschedule_adds_nothing_without_leaderboard_channel(self):
        self.bot.leaderboard_channel_id = ''

        await self.scheduler.autoschedule()

        self.assertEqual(await self.rows(), {})

    async def test_posts_the_summary_when_the_month_ends(self):
        await self.scheduler.autoschedule()

        self.now = utc(2026, 11, 1, 0, 0, 5)
        self.assertEqual(await self.scheduler.tick(), 1)

        self.get_monthly_summary.assert_awaited_once_with(2026, 10)
        self.bot.send_embed.assert_awaited_once()

    async def test_schedules_the_following_month_after_posting(self):
        await self.scheduler.autoschedule()

        self.now = utc(2026, 11, 1, 0, 0, 5)
        await self.scheduler.tick()

        self.assertIn('monthly_leaderboard:2026-12-01', await self.rows())

    async def test_late_run_reports_the_month_it_was_scheduled_for(self):
        await self.scheduler.autoschedule()

        self.now = utc(2026, 12, 3)  # the server was down over the turn of the month
        await self.scheduler.tick()

        self.get_monthly_summary.assert_awaited_once_with(2026, 10)


class BuildEmbedTest(unittest.TestCase):
    def test_title_names_the_month(self):
        embed = build_embed(summary(), 2026, 10)

        self.assertEqual(embed['title'], '🏆✨  October 2026 champions  ✨🏆')

    def test_podium_lists_the_top_three_with_medals(self):
        ranking = [entry('alice', 12, 15), entry('bob', 8, 15), entry('carol', 5, 10), entry('dave', 1, 10)]

        description = build_embed(summary(ranking=ranking), 2026, 10)['description']

        self.assertIn('🥇  **alice**\n🎯 **12**/15 wins', description)
        self.assertIn('🥈  **bob**\n🎯 **8**/15 wins', description)
        self.assertIn('🥉  **carol**\n🎯 **5**/10 wins', description)

    def test_podium_leaves_out_fourth_place(self):
        ranking = [entry('alice', 12, 15), entry('bob', 8, 15), entry('carol', 5, 10), entry('dave', 1, 10)]

        description = build_embed(summary(ranking=ranking), 2026, 10)['description']

        self.assertNotIn('dave', description)

    def test_podium_with_a_single_player(self):
        description = build_embed(summary(ranking=[entry('alice', 3, 3)]), 2026, 10)['description']

        self.assertNotIn('🥈', description)

    def test_champion_streak_is_shown_from_two_months(self):
        description = build_embed(summary(champion_streak=2), 2026, 10)['description']

        self.assertIn('🥇  **alice**  ·  👑 *reigning, unconquered for 2 months*', description)

    def test_champion_streak_is_not_shown_for_a_first_win(self):
        description = build_embed(summary(champion_streak=1), 2026, 10)['description']

        self.assertNotIn('👑', description)

    def test_champion_streak_is_shown_for_the_champion_only(self):
        description = build_embed(summary(champion_streak=5), 2026, 10)['description']

        self.assertEqual(description.count('👑'), 1)

    def test_names_are_escaped(self):
        special = r'\*_`~|>[]'
        description = build_embed(summary(ranking=[entry(special, 1, 1)]), 2026, 10)['description']

        self.assertIn('**' + ''.join('\\' + char for char in special) + '**', description)

    def test_longest_match_field(self):
        embed = build_embed(summary(longest_match=match('bob', 'alice', 3000, 30)), 2026, 10)

        field = embed['fields'][0]
        self.assertEqual(field['name'], '⏱️ Longest match')
        self.assertEqual(field['value'], '⚔️ **bob** vs **alice**\n50m 00s · 30 moves')

    def test_most_moves_field(self):
        embed = build_embed(summary(most_moves_match=match('alice', 'bob', 900, 120)), 2026, 10)

        field = embed['fields'][0]
        self.assertEqual(field['name'], '♟️ Most moves')
        self.assertEqual(field['value'], '⚔️ **alice** vs **bob**\n120 moves · 15m 00s')

    def test_match_duration_over_an_hour_shows_hours(self):
        embed = build_embed(summary(longest_match=match('bob', 'alice', 3700, 30)), 2026, 10)

        self.assertIn('1h 01m', embed['fields'][0]['value'])

    def test_match_players_are_escaped(self):
        embed = build_embed(summary(longest_match=match('a_b', 'c*d', 600, 30)), 2026, 10)

        self.assertIn('**a\\_b** vs **c\\*d**', embed['fields'][0]['value'])

    def test_match_fields_are_left_out_without_matches(self):
        embed = build_embed(summary(), 2026, 10)

        self.assertEqual([field['name'] for field in embed['fields']], ['\u200b'])
