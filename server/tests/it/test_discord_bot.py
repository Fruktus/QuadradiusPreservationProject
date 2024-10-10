from unittest.mock import AsyncMock, patch

from QRServer.common.classes import LobbyPlayer
from QRServer.common.messages import JoinLobbyRequest, LobbyStateResponse
from QRServer.discord.bot import DiscordBot
from . import QuadradiusIntegrationTestCase


class LobbyIT(QuadradiusIntegrationTestCase):
    async def itSetUpConfig(self, config):
        config.set('discord.bot.token', 'test_token')
        config.set('discord.bot.guild_id', '123')
        config.set('discord.bot.max_aliases', 1)
        config.set('discord.bot.channel_user_notifications.id', '111')

    async def itSetUp(self):
        self.bot = DiscordBot(self.config, self._server.connector)

    async def test_join_lobby(self):
        password = '123asd4567'
        password_hash = '278d56441e94b2b570ec09486466f64f'

        with patch('QRServer.discord.bot.utils.generate_random_password', return_value=password):
            username = 'John'

            interaction = AsyncMock()
            interaction.user.__repr__ = lambda _: username
            interaction.user.id = '123'
            interaction.user.guild.id = self.config.get('discord.bot.guild_id')

            await self.bot._register(interaction, username)

            client = await self.new_lobby_client()

            await client.send_message(
                JoinLobbyRequest.new('John', password_hash))

            await client.assert_received_message(
                LobbyStateResponse.new([LobbyPlayer(username='John')]))
