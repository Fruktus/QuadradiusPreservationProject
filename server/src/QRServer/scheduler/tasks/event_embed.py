import logging

from QRServer.db.models import ScheduledTask
from QRServer.discord.bot import DiscordBot
from QRServer.scheduler.task import Task

log = logging.getLogger('qr.scheduler.embed_task')


class EventEmbedTask(Task):
    """
    Posts the payload (which is in the shape of Discord embed) to configured event_channel
    """
    name = 'event_embed'

    def __init__(self, bot: DiscordBot):
        self.bot = bot

    async def run(self, task: ScheduledTask) -> None:
        if not task.payload:
            raise ValueError(f'Embed task {task.id} has no payload')

        channel_id = self.bot.event_channel_id
        if not channel_id:
            log.info('Event channel is not set, not posting the embed')
            return

        await self.bot.send_embed(channel_id, task.payload)
