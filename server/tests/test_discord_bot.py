from datetime import datetime, timezone
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from QRServer.config import Config
from QRServer.db.connector import DbConnector
from QRServer.db.password import password_verify
from QRServer.discord.bot import DiscordBot, DiscordException
import discord


class DiscordBotTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.config = Config()
        self.config.set('discord.bot.token', 'test_token')
        self.config.set('discord.bot.guild_id', '123')
        self.config.set('discord.bot.max_aliases', 1)
        self.config.set('discord.bot.channel_user_notifications.id', '111')
        self.config.set('discord.bot.channel_ban_notifications.id', '222')

        self.conn = DbConnector(':memory:', self.config)
        await self.conn.connect()

        self.bot = DiscordBot(self.config, self.conn)

        self.interaction = AsyncMock()
        self.interaction.user.__repr__ = lambda _: 'test'
        self.interaction.user.id = '123'
        self.interaction.user.guild.id = self.config.get('discord.bot.guild_id')

        self.username = 'test_user'

    async def asyncTearDown(self):
        await self.conn.close()

    async def test_raises_when_no_token(self):
        config = Config()
        config.set('discord.bot.guild_id', '123')
        config.set('discord.bot.max_aliases', 1)
        config.set('discord.bot.channel_user_notifications.id', '111')

        with pytest.raises(DiscordException):
            DiscordBot(config, self.conn)
    
    async def test_raises_when_no_guild_id(self):
        config = Config()
        config.set('discord.bot.token', 'test_token')
        config.set('discord.bot.max_aliases', 1)
        config.set('discord.bot.channel_user_notifications.id', '111')

        with self.assertRaises(DiscordException):
            await DiscordBot(config, self.conn)

    async def test_register_new_user(self):
        with patch('QRServer.discord.bot.utils.generate_random_password', return_value='123asd4567'):
            self.bot._send_notification = AsyncMock()

            await self.bot._register(self.interaction, self.username)
            user = await self.conn.get_user_by_username(self.username)

            self.assertIsNotNone(user)
            self.assertEqual(user.discord_user_id, '123')
            self.assertEqual(user.username, self.username)
            self.assertTrue(password_verify('102d60e4ca91ecc1dd46f18ae5e45bce'.encode(), user.password))

            self.interaction.response.send_message.assert_called_once_with(
                "Registered account: `test_user`, credentials have been sent via DM.",
                ephemeral=True)
            self.interaction.user.send.assert_called_once_with(
                "### Registration successful\n"
                "- Registered account: `test_user`.\n"
                "- Current password is: ||`123asd4567`||.\n"
                "You can change it in the game.\n"
                "If you forget it, you can run `/resetpassword test_user` to reset it.")

            self.bot._send_notification.assert_called_once_with(
                "### Account registered\n"
                "- Owner: <@123>\n"
                "- Username: `test_user`",
                "111",
                )

    async def test_register_user_in_wrong_guild(self):
        self.interaction.user.guild.id = '1111111'

        await self.bot._register(self.interaction, self.username)

        self.interaction.response.send_message.assert_called_once_with(
            "You must be in this bot's discord server to use it.",
            ephemeral=True)

    async def test_register_user_with_wrong_username(self):
        # Regex errors
        usernames = ['a' * 33, 'asd#^&*,\\/']

        for username in usernames:
            self.interaction.reset_mock()
            await self.bot._register(self.interaction, username)
            self.interaction.response.send_message.assert_called_once_with(
                "Username should:\n- contain at least one non-whitespace character\n"
                "- contain only letters, numbers, dots, hyphens, and underscores\n"
                "- be no longer than 15 characters.",
                ephemeral=True)

        # Guest errors
        usernames = ['asd GUEST', 'asd gUeSt ', 'asd    GUEST', 'asd guest']

        for username in usernames:
            self.interaction.reset_mock()
            await self.bot._register(self.interaction, username)
            self.interaction.response.send_message.assert_called_once_with(
                'Username cannot end with guest.',
                ephemeral=True)

    async def test_register_user_with_too_many_aliases(self):
        await self.bot._register(self.interaction, self.username)

        self.interaction.reset_mock()
        await self.bot._register(self.interaction, 'test_user2')
        self.interaction.response.send_message.assert_called_once_with(
            "You have reached the maximum number of aliases: 1.",
            ephemeral=True)

    async def test_register_user_with_existing_username(self):
        await self.conn.create_member(self.username, 'asd'.encode())

        self.interaction.reset_mock()
        await self.bot._register(self.interaction, self.username)
        self.interaction.response.send_message.assert_called_once_with(
            "Username `test_user` is taken. Please choose a different one.",
            ephemeral=True)

    async def test_register_user_with_existing_autoregistered_username(self):
        await self.conn.authenticate_user(self.username, None, verify_password=False, auto_create=True)

        self.interaction.reset_mock()
        await self.bot._register(self.interaction, self.username)
        self.interaction.response.send_message.assert_called_once_with(
            "Username `test_user` is in use but can be claimed.\nRun `/claim test_user` to claim it.",
            ephemeral=True)

    async def test_claim_user(self):
        with patch('QRServer.discord.bot.utils.generate_random_password', return_value='123asd4567'):
            self.bot._send_notification = AsyncMock()
            await self.conn.authenticate_user(self.username, password=None, verify_password=False, auto_create=True)

            await self.bot._claim(self.interaction, self.username)

            user = await self.conn.get_user_by_username(self.username)

            self.assertEqual(user.discord_user_id, '123')
            self.interaction.response.send_message.assert_called_once_with(
                "Claimed account: `test_user`, credentials have been sent via DM.",
                ephemeral=True)
            self.interaction.user.send.assert_called_once_with(
                "### Claim successful\n- Claimed account: `test_user`.\n"
                "- Current password is: ||`123asd4567`||.\n"
                "You can change it in the game.\n"
                "If you forget it, you can run `/resetpassword test_user` to reset it.")

            self.bot._send_notification.assert_called_once_with(
                "### Account claimed\n"
                "- Owner: <@123>\n"
                "- Username: `test_user`",
                "111",
                )

    async def test_claim_user_in_wrong_guild(self):
        self.interaction.user.guild.id = '1111111'

        await self.bot._claim(self.interaction, self.username)

        self.interaction.response.send_message.assert_called_once_with(
            "You must be in this bot's discord server to use it.",
            ephemeral=True)

    async def test_claim_user_with_wrong_username(self):
        # Regex errors
        usernames = ['a' * 33, 'asd#^&*,\\/']

        for username in usernames:
            self.interaction.reset_mock()
            await self.bot._claim(self.interaction, username)
            self.interaction.response.send_message.assert_called_once_with(
                "Username should:\n- contain at least one non-whitespace character\n"
                "- contain only letters, numbers, dots, hyphens, and underscores\n"
                "- be no longer than 15 characters.",
                ephemeral=True)

        # Guest errors
        usernames = ['asd GUEST', 'asd gUeSt ', 'asd    GUEST', 'asd guest']

        for username in usernames:
            self.interaction.reset_mock()
            await self.bot._claim(self.interaction, username)
            self.interaction.response.send_message.assert_called_once_with(
                'Username cannot end with guest.',
                ephemeral=True)

    async def test_claim_user_with_too_many_aliases(self):
        await self.bot._register(self.interaction, self.username)

        self.interaction.reset_mock()
        await self.bot._claim(self.interaction, 'test_user2')
        self.interaction.response.send_message.assert_called_once_with(
            "You have reached the maximum number of aliases: 1.",
            ephemeral=True)

    async def test_claim_non_existent_user(self):
        await self.bot._claim(self.interaction, self.username)

        self.interaction.response.send_message.assert_called_once_with(
            "This username is not registered."
            " Please register it instead by running `/register test_user`.",
            ephemeral=True)

    async def test_claim_registered_user(self):
        await self.conn.create_member(self.username, 'asd'.encode())

        await self.bot._claim(self.interaction, self.username)

        self.interaction.response.send_message.assert_called_once_with(
            "This username is taken. Please choose a different one.",
            ephemeral=True)

    async def test_reset_password(self):
        with patch('QRServer.discord.bot.utils.generate_random_password', return_value='123asd4567'):
            await self.conn.create_member(self.username, 'asd'.encode(), discord_user_id='123')

            await self.bot._reset_password(self.interaction, self.username)

            user = await self.conn.get_user_by_username(self.username)

            self.assertTrue(password_verify('102d60e4ca91ecc1dd46f18ae5e45bce'.encode(), user.password))
            self.interaction.response.send_message.assert_called_once_with(
                "Password for account was reset: `test_user`, credentials have been sent via DM.",
                ephemeral=True)
            self.interaction.user.send.assert_called_once_with(
                "### Password reset successful\n"
                "Password was reset for account: `test_user`.\n"
                "Your new password is: ||`123asd4567`||.")

    async def test_reset_password_unowned_user(self):
        await self.conn.create_member('test_user2', 'asd'.encode(), discord_user_id='123')
        await self.conn.create_member('test_user3', 'asd'.encode(), discord_user_id='123')

        await self.bot._reset_password(self.interaction, self.username)

        self.interaction.response.send_message.assert_called_once_with(
            "You do not have an account with username: `test_user`.\nOwned accounts: `test_user2`, `test_user3`",
            ephemeral=True)

    async def test_ban_user(self):
        self.bot._send_notification = AsyncMock()
        user_sender_mock = AsyncMock()
        self.bot.client.fetch_user = AsyncMock()
        self.bot.client.fetch_user.return_value = user_sender_mock

        await self.conn.create_member(self.username, 'asd'.encode(), discord_user_id='123')

        await self.bot._ban_user(self.interaction, self.username, 'Test Ban')

        self.interaction.response.send_message.assert_called_once_with('Banned user: `test_user`.', ephemeral=True)
        self.interaction.user.send.assert_not_called()

        self.bot._send_notification.assert_called_once_with(
            "### Account banned\n"
            "- Banned user: `test_user`\n"
            "- Banned by: <@123>\n"
            "- Reason: *Test Ban*\n", '222')

        user_sender_mock.send.assert_called_once_with(
            "### Ban\n"
            "- Your account: `test_user` has been banned.\n"
            "- Reason: *Test Ban*\n"
        )

    async def test_ban_nonexistent_user(self):
        self.bot._send_notification = AsyncMock()

        await self.bot._ban_user(self.interaction, self.username, 'Test Ban')

        self.interaction.response.send_message.assert_called_once_with(
            'User with username "test_user" has not been found', ephemeral=True)
        self.interaction.user.send.assert_not_called()

        self.bot._send_notification.assert_not_called()

    async def test_ban_banned_user(self):
        self.bot._send_notification = AsyncMock()
        user_sender_mock = AsyncMock()
        self.bot.client.fetch_user = AsyncMock()
        user_id = await self.conn.create_member(self.username, 'asd'.encode(), discord_user_id='123')

        with patch('QRServer.db.connector.datetime') as mock_dt:
            mock_dt.now.return_value = datetime(2020, 1, 2, 3, 4, 5, tzinfo=timezone.utc)
            result = await self.conn.ban_user(user_id, '123', 'Test Ban')
            self.assertTrue(result)

        self.bot.client.fetch_user.return_value = user_sender_mock
        await self.bot._ban_user(self.interaction, self.username, 'Test Ban')

        self.interaction.response.send_message.assert_called_once_with('Banned user: `test_user`.', ephemeral=True)
        self.interaction.user.send.assert_not_called()

        self.bot._send_notification.assert_called_once_with(
            "### Account banned (again)\n"
            "- Banned user: `test_user`\n"
            "- Banned by: <@123>\n"
            "- Reason: *Test Ban*\n", '222')

        user_sender_mock.send.assert_not_called()

    async def test_unban_user(self):
        self.bot._send_notification = AsyncMock()
        user_sender_mock = AsyncMock()
        self.bot.client.fetch_user = AsyncMock()
        self.bot.client.fetch_user.return_value = user_sender_mock

        user_id = await self.conn.create_member(self.username, 'asd'.encode(), discord_user_id='123')
        await self.conn.ban_user(user_id, '123', 'Test Ban')

        await self.bot._unban_user(self.interaction, self.username)

        self.interaction.response.send_message.assert_called_once_with('Unbanned user: `test_user`.', ephemeral=True)
        self.interaction.user.send.assert_not_called()

        self.bot._send_notification.assert_called_once_with(
            "### Account unbanned\n"
            "- Unbanned user: `test_user`\n"
            "- Unbanned by: <@123>\n", '222')

        user_sender_mock.send.assert_called_once_with(
            "### Unban\n"
            "- Your account: `test_user` has been unbanned.\n"
        )

    async def test_unban_nonexistent_user(self):
        self.bot._send_notification = AsyncMock()

        await self.bot._unban_user(self.interaction, self.username)

        self.interaction.response.send_message.assert_called_once_with(
            'User with username "test_user" has not been found', ephemeral=True)
        self.interaction.user.send.assert_not_called()

        self.bot._send_notification.assert_not_called()

    async def test_unban_nonbanned_user(self):
        self.bot._send_notification = AsyncMock()
        await self.conn.create_member(self.username, 'asd'.encode(), discord_user_id='123')

        await self.bot._unban_user(self.interaction, self.username)

        self.interaction.response.send_message.assert_called_once_with(
            'This user is not currently banned',
            ephemeral=True)
        self.interaction.user.send.assert_not_called()

        self.bot._send_notification.assert_not_called()

    async def test_ban_user_without_dc_id(self):
        self.bot._send_notification = AsyncMock()
        user_sender_mock = AsyncMock()
        self.bot.client.fetch_user = AsyncMock()
        self.bot.client.fetch_user.return_value = user_sender_mock

        await self.conn.create_member(self.username, 'asd'.encode())

        await self.bot._ban_user(self.interaction, self.username, 'Test Ban')

        self.interaction.response.send_message.assert_called_once_with(
            "Banned user: `test_user`.\n"
            "This user has no Discord ID",
            ephemeral=True,
        )
        self.interaction.user.send.assert_not_called()

        self.bot._send_notification.assert_called_once_with(
            "### Account banned\n"
            "- Banned user: `test_user`\n"
            "- Banned by: <@123>\n"
            "- Reason: *Test Ban*\n", '222')

        user_sender_mock.send.assert_not_called()

    async def test_unban_user_without_dc_id(self):
        self.bot._send_notification = AsyncMock()
        user_sender_mock = AsyncMock()
        self.bot.client.fetch_user = AsyncMock()
        self.bot.client.fetch_user.return_value = user_sender_mock

        user_id = await self.conn.create_member(self.username, 'asd'.encode())
        await self.conn.ban_user(user_id, '123', 'Test Ban')

        await self.bot._unban_user(self.interaction, self.username)

        self.interaction.response.send_message.assert_called_once_with(
            "Unbanned user: `test_user`.\n"
            "This user has no Discord ID",
            ephemeral=True,
        )
        self.interaction.user.send.assert_not_called()

        self.bot._send_notification.assert_called_once_with(
            "### Account unbanned\n"
            "- Unbanned user: `test_user`\n"
            "- Unbanned by: <@123>\n", '222')

        user_sender_mock.send.assert_not_called()

    async def _setup_challenge_users(self):
        await self.conn.create_member('challenger', 'asd'.encode(), discord_user_id='123')
        await self.conn.create_member('challenged', 'asd'.encode(), discord_user_id='456')
        challenged_dc = AsyncMock()
        self.bot.client.fetch_user = AsyncMock(return_value=challenged_dc)
        return challenged_dc

    async def test_challenge_member(self):
        challenged_dc = await self._setup_challenge_users()

        with patch('QRServer.db.connector.uuid.uuid4') as mock_uuid, \
             patch('QRServer.db.connector.datetime') as mock_datetime, \
             patch('QRServer.db.connector.random.randint', return_value=1):
            mock_datetime.now.return_value = datetime(2020, 1, 1, tzinfo=timezone.utc)
            mock_uuid.side_effect = ['invite-id', 't1', 't2']

            await self.bot._challenge_member(self.interaction, 'challenged')

        url = 'http://localhost/challenge?id=invite-id'

        challenged_dc.send.assert_called_once_with(
            "### Match Invite\n"
            "- You have been invited to a match!\n"
            "- Your opponent is: <@123> - `challenger`\n"
            f"- Match link: {url}\n"
            "- The match link will be valid for the next 15 minutes")

        self.interaction.user.send.assert_called_once_with(
            "### Match Invite\n"
            "- You have been invited to a match!\n"
            "- Your opponent is: <@456> - `challenged`\n"
            f"- Match link: {url}\n"
            "- The match link will be valid for the next 15 minutes")

        self.interaction.response.send_message.assert_called_once_with(
            "### Invite has been sent", ephemeral=True)

        self.bot.client.fetch_user.assert_called_once_with(456)

    async def test_challenge_unregistered_challenger(self):
        await self.bot._challenge_member(self.interaction, 'someone')
        self.interaction.response.send_message.assert_called_once_with(
            "You need to register first.", ephemeral=True)

    async def test_challenge_banned_challenger(self):
        await self.conn.create_member('challenger', 'asd'.encode(), discord_user_id='123')
        challenger = await self.conn.get_user_by_username('challenger')
        await self.conn.ban_user(challenger.user_id, 'admin', 'test')

        await self.bot._challenge_member(self.interaction, 'someone')

        self.interaction.response.send_message.assert_called_once_with(
            "Your account: `challenger` has been banned.", ephemeral=True)

    async def test_challenge_self(self):
        await self.conn.create_member('challenger', 'asd'.encode(), discord_user_id='123')

        await self.bot._challenge_member(self.interaction, 'challenger')

        self.interaction.response.send_message.assert_called_once_with(
            "You cannot challenge a different account tied to the same Discord account.",
            ephemeral=True)

    async def test_challenge_unknown_player(self):
        await self.conn.create_member('challenger', 'asd'.encode(), discord_user_id='123')

        await self.bot._challenge_member(self.interaction, 'ghost')

        self.interaction.response.send_message.assert_called_once_with(
            "Failed to find a player with username: `ghost`. Check for typos and case.", ephemeral=True)

    async def test_challenge_banned_player(self):
        await self.conn.create_member('challenger', 'asd'.encode(), discord_user_id='123')
        await self.conn.create_member('challenged', 'asd'.encode(), discord_user_id='456')
        challenged = await self.conn.get_user_by_username('challenged')
        await self.conn.ban_user(challenged.user_id, 'admin', 'test')

        await self.bot._challenge_member(self.interaction, 'challenged')

        self.interaction.response.send_message.assert_called_once_with(
            "Your opponent's account: `challenged` has been banned.", ephemeral=True)

    async def test_challenge_existing_active_invite(self):
        await self._setup_challenge_users()
        challenger = await self.conn.get_user_by_username('challenger')
        challenged = await self.conn.get_user_by_username('challenged')

        with patch('QRServer.db.connector.uuid.uuid4') as mock_uuid, \
             patch('QRServer.db.connector.datetime') as mock_datetime, \
             patch('QRServer.db.connector.random.randint', return_value=1):
            mock_datetime.now.return_value = datetime(2020, 1, 1, tzinfo=timezone.utc)
            mock_uuid.side_effect = ['existing-invite', 't1', 't2']
            await self.conn.create_match_invite(challenger.user_id, challenged.user_id)

        self.interaction.reset_mock()

        with patch('QRServer.db.models.datetime') as mock_models_datetime:
            mock_models_datetime.now.return_value = datetime(2020, 1, 1, 0, 5, tzinfo=timezone.utc)
            await self.bot._challenge_member(self.interaction, 'challenged')

        self.interaction.response.send_message.assert_called_once_with(
            "You already have an active invite with this user: "
            "http://localhost/challenge?id=existing-invite",
            ephemeral=True)
        self.bot.client.fetch_user.assert_not_called()

    async def test_challenge_dm_to_challenged_fails(self):
        challenged_dc = await self._setup_challenge_users()
        challenged_dc.send.side_effect = discord.Forbidden(
            MagicMock(status=403, reason='Forbidden'), 'Cannot send messages to this user')

        with patch('QRServer.db.connector.uuid.uuid4') as mock_uuid, \
             patch('QRServer.db.connector.datetime') as mock_datetime, \
             patch('QRServer.db.connector.random.randint', return_value=1):
            mock_datetime.now.return_value = datetime(2020, 1, 1, tzinfo=timezone.utc)
            mock_uuid.side_effect = ['invite-id', 't1', 't2']
            await self.bot._challenge_member(self.interaction, 'challenged')

        self.interaction.response.send_message.assert_called_once_with(
            "Created a challenge for `challenged`, but couldn't DM them "
            "(their privacy settings may block it).\n"
            "You can send them this link yourself: http://localhost/challenge?id=invite-id",
            ephemeral=True)
        self.interaction.user.send.assert_not_called()

        # invite still exists in the db even though delivery failed
        invite = await self.conn.get_match_invite('invite-id')
        self.assertIsNotNone(invite)

    async def test_challenge_dm_to_challenger_fails(self):
        await self._setup_challenge_users()
        self.interaction.user.send.side_effect = discord.Forbidden(
            MagicMock(status=403, reason='Forbidden'), 'Cannot send messages to this user')

        with patch('QRServer.db.connector.uuid.uuid4') as mock_uuid, \
             patch('QRServer.db.connector.datetime') as mock_datetime, \
             patch('QRServer.db.connector.random.randint', return_value=1):
            mock_datetime.now.return_value = datetime(2020, 1, 1, tzinfo=timezone.utc)
            mock_uuid.side_effect = ['invite-id', 't1', 't2']
            await self.bot._challenge_member(self.interaction, 'challenged')

        self.interaction.response.send_message.assert_called_once_with(
            "Challenge sent to `challenged`, but I couldn't DM you the link.\n"
            "Here it is: http://localhost/challenge?id=invite-id",
            ephemeral=True)

    async def test_challenge_guest_player(self):
        await self.conn.create_member('challenger', 'asd'.encode(), discord_user_id='123')
        await self.conn.create_member('Random Guest', 'asd'.encode(), discord_user_id='456')

        await self.bot._challenge_member(self.interaction, 'Random Guest')

        self.interaction.response.send_message.assert_called_once_with(
            "You cannot challenge guest users.", ephemeral=True)

    async def test_challenge_wrong_guild(self):
        self.interaction.user.guild.id = 999

        await self.bot._challenge_member(self.interaction, 'someone')

        self.interaction.response.send_message.assert_called_once_with(
            "You must be in this bot's discord server to use it.", ephemeral=True)
