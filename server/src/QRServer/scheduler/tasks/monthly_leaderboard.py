import calendar
import logging
import re
from datetime import datetime, timezone

from QRServer.common.classes import GameResultHistory, MonthlySummary
from QRServer.common.utils import utils
from QRServer.db.connector import DbConnector
from QRServer.db.models import ScheduledTask
from QRServer.discord.bot import DiscordBot
from QRServer.scheduler.task import Task

log = logging.getLogger('qr.scheduler.monthly_leaderboard')


class MonthlyLeaderboardTask(Task):
    """
    Posts the summary of the month which just ended to the leaderboard channel on the 1st of every month.
    Disabled (never scheduled) while the channel is not configured.
    """
    name = 'monthly_leaderboard'

    MEDALS = ['🥇', '🥈', '🥉']
    SPACER = '\u200b'  # zero-width space, survives Discord's whitespace trimming

    def __init__(self, connector: DbConnector, bot: DiscordBot):
        self.connector = connector
        self.bot = bot

    @staticmethod
    def _escape_markdown(text: str) -> str:
        """Escape Discord markdown in user-provided names."""
        return re.sub(r'([\\*_`~|>\[\]])', r'\\\1', text)

    @staticmethod
    def _format_duration(seconds: int) -> str:
        hours, rest = divmod(seconds, 3600)
        minutes, seconds = divmod(rest, 60)
        return f'{hours}h {minutes:02d}m' if hours else f'{minutes}m {seconds:02d}s'

    @classmethod
    def _format_match(cls, match: GameResultHistory, duration_first: bool) -> str:
        duration = cls._format_duration(int((match.finish - match.start).total_seconds()))
        moves = f'{match.moves} moves'
        stats = f'{duration} · {moves}' if duration_first else f'{moves} · {duration}'
        return \
            f'⚔️ **{cls._escape_markdown(match.player_won)}** vs **{cls._escape_markdown(match.player_lost)}**\n{stats}'

    @classmethod
    def build_embed(cls, summary: MonthlySummary, year: int, month: int) -> dict:
        """
        Returns:
            The summary of the given month as an embed, in the shape of Discord's embed object.
            The longest match and the most moves fields are left out if there is no such match.
        """
        podium = []
        for place, (medal, entry) in enumerate(zip(cls.MEDALS, summary.ranking)):
            header = f'### {medal}  **{cls._escape_markdown(entry.username)}**'
            if place == 0 and summary.champion_streak >= 2:
                header += f'  ·  👑 *reigning, unconquered for {summary.champion_streak} months*'
            podium.append(f'{header}\n🎯 **{entry.wins}**/{entry.games} wins')

        description = (
            cls.SPACER + '\n'  # gap under the title
            + '\n\n'.join(podium)
            + '\n\n✦ ▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬▬ ✦\n'  # divider between podium and stats
            + cls.SPACER
        )

        fields = []
        if summary.longest_match is not None:
            fields.append({
                'name': '⏱️ Longest match',
                'value': cls._format_match(summary.longest_match, duration_first=True),
                'inline': True,
            })
        if summary.most_moves_match is not None:
            fields.append({
                'name': '♟️ Most moves',
                'value': cls._format_match(summary.most_moves_match, duration_first=False),
                'inline': True,
            })
        # empty full-width row: pushes the footer away from the fields
        fields.append({'name': cls.SPACER, 'value': cls.SPACER, 'inline': False})

        return {
            'title': f'🏆✨  {calendar.month_name[month]} {year} champions  ✨🏆',
            'color': 0xFFD700,
            'description': description,
            'fields': fields,
            'footer': {'text': '🎉 Quadradius monthly summary'},
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }

    def next_run(self, after: datetime) -> datetime | None:
        if not self.bot.leaderboard_channel_id:
            return None
        return utils.first_of_next_month(after)

    async def run(self, task: ScheduledTask) -> None:
        channel_id = self.bot.leaderboard_channel_id
        if not channel_id:
            log.info('Leaderboard channel is not set, not posting the summary')
            return

        # `run_at` is the 1st of a month (see `next_run`), so the month before it is the one which has ended.
        # It is taken from there, not from the current time, so that a run delayed past the end of the month
        # (e.g. by downtime) still reports the month it was scheduled for.
        previous_month_date = utils.previous_month(task.run_at)
        year, month = (previous_month_date.year, previous_month_date.month)
        summary = await self.connector.get_monthly_summary(year, month)
        if not summary.ranking:
            log.info(f'No games were played in {year}-{month:02}, not posting the summary')
            return

        await self.bot.send_embed(channel_id, self.build_embed(summary, year, month))
