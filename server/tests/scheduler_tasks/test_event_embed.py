import unittest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

from QRServer.config import Config
from QRServer.db.connector import DbConnector
from QRServer.db.models import ScheduledTask, ScheduledTaskStatus
from QRServer.discord.bot import DiscordBot, DiscordException
from QRServer.scheduler.scheduler import Scheduler
from QRServer.scheduler.tasks.event_embed import EventEmbedTask

RUN_AT = datetime(2026, 12, 1, 12, tzinfo=timezone.utc)
EMBED = {
    'title': '🎄✨  Day 1  ✨🎄',
    'color': 0xC0392B,
    'description': '**Win a match.**\n```\n  *\n ***\n```',
    'fields': [{'name': '⏳ Ends', 'value': '<t:1:R>', 'inline': True}],
}


def utc(*args):
    return datetime(*args, tzinfo=timezone.utc)


def scheduled(payload=EMBED) -> ScheduledTask:
    return ScheduledTask(
        id='a', handler='event_embed', payload=payload, run_at=RUN_AT,
        status=ScheduledTaskStatus.RUNNING, error=None, created_at=RUN_AT, started_at=RUN_AT, finished_at=None)


class EventEmbedTaskTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.bot = MagicMock(spec=DiscordBot)
        self.bot.event_channel_id = '555'
        self.bot.send_embed = AsyncMock()
        self.task = EventEmbedTask(self.bot)

    def test_name(self):
        self.assertEqual(self.task.name, 'event_embed')

    def test_is_not_autoscheduled(self):
        self.assertIsNone(self.task.next_run(utc(2026, 11, 20)))

    def test_bot_has_the_event_channel(self):
        config = Config()
        config.set('discord.bot.token', 'test_token')
        config.set('discord.bot.guild_id', '123')

        bot = DiscordBot(config, MagicMock(spec=DbConnector))

        self.assertTrue(hasattr(bot, 'event_channel_id'))

    # posting
    async def test_posts_the_payload_to_the_event_channel(self):
        await self.task.run(scheduled())

        self.bot.send_embed.assert_awaited_once_with('555', EMBED)

    async def test_channel_is_taken_from_the_current_config(self):
        self.bot.event_channel_id = '777'  # changed after the task was saved

        await self.task.run(scheduled())

        self.bot.send_embed.assert_awaited_once_with('777', EMBED)

    async def test_post_is_skipped_while_the_channel_is_not_set(self):
        for unset in ('', None):
            with self.subTest(channel=unset):
                self.bot.event_channel_id = unset

                await self.task.run(scheduled())

                self.bot.send_embed.assert_not_awaited()

    # validation
    async def test_missing_payload_fails(self):
        for payload in ({}, None):
            with self.subTest(payload=payload):
                with self.assertRaises(ValueError):
                    await self.task.run(scheduled(payload))

                self.bot.send_embed.assert_not_awaited()

    async def test_missing_payload_fails_even_when_the_channel_is_not_set(self):
        self.bot.event_channel_id = ''

        with self.assertRaises(ValueError):
            await self.task.run(scheduled({}))

    # errors
    async def test_send_error_is_raised(self):
        self.bot.send_embed.side_effect = DiscordException('no channel')

        with self.assertRaises(DiscordException):
            await self.task.run(scheduled())


class EventEmbedSchedulingTest(unittest.IsolatedAsyncioTestCase):
    """The task run by the real scheduler, from a row stored in the db"""

    async def asyncSetUp(self):
        self.now = utc(2026, 12, 1, 12, 0, 5)
        self.config = Config()
        self.conn = DbConnector(':memory:', self.config)
        await self.conn.connect()

        self.bot = MagicMock(spec=DiscordBot)
        self.bot.event_channel_id = '555'
        self.bot.send_embed = AsyncMock()
        self.scheduler = Scheduler(self.conn, self.config, clock=lambda: self.now)
        self.scheduler.register(EventEmbedTask(self.bot))

    async def asyncTearDown(self):
        await self.conn.close()

    async def add(self, payload):
        await self.conn.create_scheduled_task('a', 'event_embed', RUN_AT, payload)

    async def stored(self) -> ScheduledTask:
        return (await self.conn.get_scheduled_tasks())[0]

    async def test_embed_survives_the_db(self):
        await self.add(EMBED)

        await self.scheduler.tick()

        self.bot.send_embed.assert_awaited_once_with('555', EMBED)

    async def test_posted_embed_is_done(self):
        await self.add(EMBED)

        await self.scheduler.tick()

        self.assertEqual((await self.stored()).status, ScheduledTaskStatus.DONE)

    async def test_embed_is_not_posted_before_it_is_due(self):
        await self.add(EMBED)
        self.now = utc(2026, 12, 1, 11, 59, 59)

        await self.scheduler.tick()

        self.bot.send_embed.assert_not_awaited()

    async def test_embed_is_posted_once(self):
        await self.add(EMBED)

        await self.scheduler.tick()
        await self.scheduler.tick()

        self.bot.send_embed.assert_awaited_once()

    async def test_embed_without_the_channel_is_done(self):
        self.bot.event_channel_id = ''
        await self.add(EMBED)

        await self.scheduler.tick()

        self.bot.send_embed.assert_not_awaited()
        self.assertEqual((await self.stored()).status, ScheduledTaskStatus.DONE)

    async def test_missing_payload_fails_the_task(self):
        await self.add({})

        await self.scheduler.tick()

        task = await self.stored()
        self.assertEqual(task.status, ScheduledTaskStatus.FAILED)
        self.assertIn('ValueError', task.error)
        self.bot.send_embed.assert_not_awaited()

    async def test_send_error_fails_the_task(self):
        self.bot.send_embed.side_effect = DiscordException('no channel')
        await self.add(EMBED)

        await self.scheduler.tick()

        task = await self.stored()
        self.assertEqual(task.status, ScheduledTaskStatus.FAILED)
        self.assertIn('no channel', task.error)
