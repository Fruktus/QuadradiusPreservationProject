from datetime import datetime, timezone
import unittest
from unittest.mock import AsyncMock, MagicMock, patch

from QRServer.config import Config
from QRServer.db.connector import DbConnector
from QRServer.db.password import password_verify
from QRServer.discord.bot import DiscordBot, DiscordException, PreconditionFailedException, MAX_SVG_BYTES
import discord


TROPHY_SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><path d="M2 1h6v3a3 3 0 0 1-6 0z"/></svg>'


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
        self.interaction.guild.id = int(self.config.get('discord.bot.guild_id'))

        self.username = 'test_user'

        response = self.interaction.response
        response.is_done = MagicMock(
            side_effect=lambda: response.defer.called or response.send_message.called)

    async def asyncTearDown(self):
        await self.conn.close()

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
        self.interaction.guild.id = '1111111'

        with self.assertRaises(PreconditionFailedException):
            await self.bot._register(self.interaction, self.username)

        self.interaction.response.send_message.assert_called_once_with(
            "You must be in this bot's discord server to use it.",
            ephemeral=True)

    async def test_register_user_with_wrong_username(self):
        # Regex errors
        usernames = ['a' * 33, 'asd#^&*,\\/']

        for username in usernames:
            self.interaction.reset_mock()
            with self.assertRaises(PreconditionFailedException):
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
            with self.assertRaises(PreconditionFailedException):
                await self.bot._register(self.interaction, username)
            self.interaction.response.send_message.assert_called_once_with(
                'Username cannot end with guest.',
                ephemeral=True)

    async def test_register_user_with_too_many_aliases(self):
        await self.bot._register(self.interaction, self.username)

        self.interaction.reset_mock()
        with self.assertRaises(PreconditionFailedException):
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
        self.interaction.guild.id = '1111111'

        with self.assertRaises(PreconditionFailedException):
            await self.bot._claim(self.interaction, self.username)

        self.interaction.response.send_message.assert_called_once_with(
            "You must be in this bot's discord server to use it.",
            ephemeral=True)

    async def test_claim_user_with_wrong_username(self):
        # Regex errors
        usernames = ['a' * 33, 'asd#^&*,\\/']

        for username in usernames:
            self.interaction.reset_mock()
            with self.assertRaises(PreconditionFailedException):
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
            with self.assertRaises(PreconditionFailedException):
                await self.bot._claim(self.interaction, username)
            self.interaction.response.send_message.assert_called_once_with(
                'Username cannot end with guest.',
                ephemeral=True)

    async def test_claim_user_with_too_many_aliases(self):
        await self.bot._register(self.interaction, self.username)

        self.interaction.reset_mock()
        with self.assertRaises(PreconditionFailedException):
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

        with self.assertRaises(PreconditionFailedException):
            await self.bot._ban_user(self.interaction, self.username, 'Test Ban')

        self.interaction.response.send_message.assert_called_once_with(
            "Failed to find a player with username: `test_user`. Check for typos and case.", ephemeral=True)
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

        with self.assertRaises(PreconditionFailedException):
            await self.bot._unban_user(self.interaction, self.username)

        self.interaction.response.send_message.assert_called_once_with(
            "Failed to find a player with username: `test_user`. Check for typos and case.", ephemeral=True)
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
        with self.assertRaises(PreconditionFailedException):
            await self.bot._challenge_member(self.interaction, 'someone')
        self.interaction.response.send_message.assert_called_once_with(
            "You need to register first.", ephemeral=True)

    async def test_challenge_banned_challenger(self):
        await self.conn.create_member('challenger', 'asd'.encode(), discord_user_id='123')
        challenger = await self.conn.get_user_by_username('challenger')
        await self.conn.ban_user(challenger.user_id, 'admin', 'test')

        with self.assertRaises(PreconditionFailedException):
            await self.bot._challenge_member(self.interaction, 'someone')

        self.interaction.response.send_message.assert_called_once_with(
            "Account `challenger` is banned.", ephemeral=True)

    async def test_challenge_self(self):
        await self.conn.create_member('challenger', 'asd'.encode(), discord_user_id='123')

        with self.assertRaises(PreconditionFailedException):
            await self.bot._challenge_member(self.interaction, 'challenger')

        self.interaction.response.send_message.assert_called_once_with(
            "You cannot interact with a different account tied to the same Discord account.",
            ephemeral=True)

    async def test_challenge_unknown_player(self):
        await self.conn.create_member('challenger', 'asd'.encode(), discord_user_id='123')

        with self.assertRaises(PreconditionFailedException):
            await self.bot._challenge_member(self.interaction, 'ghost')

        self.interaction.response.send_message.assert_called_once_with(
            "Failed to find a player with username: `ghost`. Check for typos and case.", ephemeral=True)

    async def test_challenge_banned_player(self):
        await self.conn.create_member('challenger', 'asd'.encode(), discord_user_id='123')
        await self.conn.create_member('challenged', 'asd'.encode(), discord_user_id='456')
        challenged = await self.conn.get_user_by_username('challenged')
        await self.conn.ban_user(challenged.user_id, 'admin', 'test')

        with self.assertRaises(PreconditionFailedException):
            await self.bot._challenge_member(self.interaction, 'challenged')

        self.interaction.response.send_message.assert_called_once_with(
            "Account `challenged` is banned.", ephemeral=True)

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

        with self.assertRaises(PreconditionFailedException):
            await self.bot._challenge_member(self.interaction, 'Random Guest')

        self.interaction.response.send_message.assert_called_once_with(
            "You cannot interact with guest users.", ephemeral=True)

    async def test_challenge_wrong_guild(self):
        self.interaction.guild.id = 999

        with self.assertRaises(PreconditionFailedException):
            await self.bot._challenge_member(self.interaction, 'someone')

        self.interaction.response.send_message.assert_called_once_with(
            "You must be in this bot's discord server to use it.", ephemeral=True)

    # Guild restriction on admin / account commands

    async def test_reset_password_wrong_guild(self):
        self.interaction.guild.id = '1111111'

        with self.assertRaises(PreconditionFailedException):
            await self.bot._reset_password(self.interaction, self.username)

        self.interaction.response.send_message.assert_called_once_with(
            "You must be in this bot's discord server to use it.", ephemeral=True)

    async def test_reset_password_outside_guild(self):
        self.interaction.guild = None

        with self.assertRaises(PreconditionFailedException):
            await self.bot._reset_password(self.interaction, self.username)

        self.interaction.response.send_message.assert_called_once_with(
            "You must be in this bot's discord server to use it.", ephemeral=True)

    async def test_ban_user_wrong_guild(self):
        self.interaction.guild.id = '1111111'

        with self.assertRaises(PreconditionFailedException):
            await self.bot._ban_user(self.interaction, self.username, 'Test Ban')

        self.interaction.response.send_message.assert_called_once_with(
            "You must be in this bot's discord server to use it.", ephemeral=True)

    async def test_unban_user_wrong_guild(self):
        self.interaction.guild.id = '1111111'

        with self.assertRaises(PreconditionFailedException):
            await self.bot._unban_user(self.interaction, self.username)

        self.interaction.response.send_message.assert_called_once_with(
            "You must be in this bot's discord server to use it.", ephemeral=True)

    async def test_unban_guest_user(self):
        self.bot._send_notification = AsyncMock()
        user_id = await self.conn.create_member('Random Guest', 'asd'.encode())
        await self.conn.ban_user(user_id, 'admin', 'test')

        await self.bot._unban_user(self.interaction, 'Random Guest')

        self.interaction.response.send_message.assert_called_once_with(
            "Unbanned user: `Random Guest`.\nThis user has no Discord ID", ephemeral=True)

    # Failure messages must not leak internal ids

    async def test_ban_failure_message_has_no_internal_ids(self):
        self.bot._send_notification = AsyncMock()
        await self.conn.create_member(self.username, 'asd'.encode(), discord_user_id='456')

        with patch.object(self.conn, 'ban_user', AsyncMock(return_value=False)):
            await self.bot._ban_user(self.interaction, self.username, 'Test Ban')

        self.interaction.response.send_message.assert_called_once_with(
            "Something went wrong while banning user: `test_user`.", ephemeral=True)
        self.bot._send_notification.assert_not_called()

    async def test_unban_failure_message_has_no_internal_ids(self):
        self.bot._send_notification = AsyncMock()
        user_id = await self.conn.create_member(self.username, 'asd'.encode(), discord_user_id='456')
        await self.conn.ban_user(user_id, 'admin', 'test')

        with patch.object(self.conn, 'unban_user', AsyncMock(return_value=False)):
            await self.bot._unban_user(self.interaction, self.username)

        self.interaction.response.send_message.assert_called_once_with(
            "Something went wrong while unbanning user: `test_user`.", ephemeral=True)
        self.bot._send_notification.assert_not_called()

    # Every failed precondition must be logged with its code

    async def _assert_precondition_logged(self, code: str, call) -> None:
        with self.assertLogs('qr.bot', level='DEBUG') as logs:
            try:
                await call
            except PreconditionFailedException:
                pass
        self.assertTrue(
            any(f'precondition failed: {code}' in line for line in logs.output),
            f'expected "precondition failed: {code}" in {logs.output}')

    async def test_logged_invalid_user_guild(self):
        self.interaction.guild.id = '1111111'
        await self._assert_precondition_logged(
            'invalid_user_guild', self.bot._register(self.interaction, self.username))

    async def test_logged_invalid_username(self):
        await self._assert_precondition_logged(
            'invalid_username', self.bot._register(self.interaction, 'asd#^&*,'))

    async def test_logged_guest_username(self):
        await self._assert_precondition_logged(
            'guest_username', self.bot._register(self.interaction, 'asd guest'))

    async def test_logged_over_max_aliases(self):
        await self.conn.create_member('other', 'asd'.encode(), discord_user_id='123')
        await self._assert_precondition_logged(
            'over_max_aliases', self.bot._register(self.interaction, self.username))

    async def test_logged_username_taken(self):
        await self.conn.create_member(self.username, 'asd'.encode(), discord_user_id='456')
        await self._assert_precondition_logged(
            'username_taken', self.bot._register(self.interaction, self.username))
        await self._assert_precondition_logged(
            'username_taken', self.bot._claim(self.interaction, self.username))

    async def test_logged_username_claimable(self):
        await self.conn.authenticate_user(self.username, None, verify_password=False, auto_create=True)
        await self._assert_precondition_logged(
            'username_claimable', self.bot._register(self.interaction, self.username))

    async def test_logged_nonexistent_user(self):
        await self._assert_precondition_logged(
            'nonexistent_user', self.bot._claim(self.interaction, self.username))
        await self._assert_precondition_logged(
            'nonexistent_user', self.bot._ban_user(self.interaction, self.username, 'Test Ban'))
        await self._assert_precondition_logged(
            'nonexistent_user', self.bot._unban_user(self.interaction, self.username))

    async def test_logged_not_owned_account(self):
        await self.conn.create_member('other', 'asd'.encode(), discord_user_id='123')
        await self._assert_precondition_logged(
            'not_owned_account', self.bot._reset_password(self.interaction, self.username))

    async def test_logged_user_not_banned(self):
        await self.conn.create_member(self.username, 'asd'.encode(), discord_user_id='456')
        await self._assert_precondition_logged(
            'user_not_banned', self.bot._unban_user(self.interaction, self.username))

    async def test_logged_challenge_preconditions(self):
        await self._assert_precondition_logged(
            'user_not_registered', self.bot._challenge_member(self.interaction, 'challenged'))

        await self._setup_challenge_users()
        await self._assert_precondition_logged(
            'same_discord_account_interaction', self.bot._challenge_member(self.interaction, 'challenger'))
        await self._assert_precondition_logged(
            'nonexistent_user', self.bot._challenge_member(self.interaction, 'ghost'))

        await self.conn.create_member('Random Guest', 'asd'.encode(), discord_user_id='789')
        await self._assert_precondition_logged(
            'targeted_guest_user', self.bot._challenge_member(self.interaction, 'Random Guest'))

        challenged = await self.conn.get_user_by_username('challenged')
        await self.conn.ban_user(challenged.user_id, 'admin', 'test')
        await self._assert_precondition_logged(
            'user_banned', self.bot._challenge_member(self.interaction, 'challenged'))

    async def test_logged_active_invite_exists(self):
        await self._setup_challenge_users()
        challenger = await self.conn.get_user_by_username('challenger')
        challenged = await self.conn.get_user_by_username('challenged')
        await self.conn.create_match_invite(challenger.user_id, challenged.user_id)

        await self._assert_precondition_logged(
            'active_invite_exists', self.bot._challenge_member(self.interaction, 'challenged'))

    # Trophies
    def _svg_attachment(self, data: bytes = TROPHY_SVG, size: int | None = None) -> AsyncMock:
        attachment = AsyncMock()
        attachment.size = len(data) if size is None else size
        attachment.read.return_value = data
        return attachment

    async def test_create_trophy(self):
        await self.bot._create_trophy(self.interaction, '  Season 1 Champion ', self._svg_attachment())

        trophy = await self.conn.get_trophy_by_name('Season 1 Champion')
        self.assertIsNotNone(trophy)
        self.assertEqual(trophy.svg, TROPHY_SVG)
        self.assertIsNone(trophy.user_id)
        self.assertIsNone(trophy.tournament_id)
        self.interaction.response.defer.assert_called_once_with(ephemeral=True)
        self.interaction.followup.send.assert_called_once_with(
            "Created trophy: `Season 1 Champion`. Use `/awardtrophy` to award it to a player.", ephemeral=True)

    async def test_create_trophy_in_wrong_guild(self):
        self.interaction.guild.id = '1111111'

        with self.assertRaises(PreconditionFailedException):
            await self.bot._create_trophy(self.interaction, 'trophy', self._svg_attachment())

        self.assertIsNone(await self.conn.get_trophy_by_name('trophy'))

    async def test_create_trophy_with_taken_name(self):
        await self.conn.create_trophy('trophy', TROPHY_SVG, None)

        with self.assertRaises(PreconditionFailedException):
            await self.bot._create_trophy(self.interaction, 'trophy', self._svg_attachment())

        self.interaction.followup.send.assert_called_once_with(
            "Failed to create trophy `trophy`. "
            "The name may be taken, or the tournament may already have a trophy.", ephemeral=True)

        with self.assertRaises(PreconditionFailedException):
            # Handle different case as well
            await self.bot._create_trophy(self.interaction, 'Trophy', self._svg_attachment())

    async def test_create_trophy_with_invalid_name(self):
        for name in ['', '   ', 'a' * 65, 'bad`name', 'two\nlines']:
            self.interaction.reset_mock()
            with self.assertRaises(PreconditionFailedException, msg=name):
                await self.bot._create_trophy(self.interaction, name, self._svg_attachment())
            self.interaction.response.send_message.assert_called_once_with(
                "Trophy name should be 1-64 printable characters and not contain backticks.", ephemeral=True)

    async def test_create_trophy_with_invalid_svg(self):
        # The exhaustive cases live in ValidateSvgTest, here we only check that the message is forwarded
        self.interaction.reset_mock()
        with self.assertRaises(PreconditionFailedException):
            await self.bot._create_trophy(self.interaction, 'trophy', self._svg_attachment(b'not xml at all'))

        self.interaction.followup.send.assert_called_once_with(
            "Invalid trophy SVG: The file is not valid XML.", ephemeral=True)
        self.assertIsNone(await self.conn.get_trophy_by_name('trophy'))

    async def test_create_trophy_with_too_big_svg(self):
        # Rejected based on the reported size, without deferring or downloading
        attachment = self._svg_attachment(size=MAX_SVG_BYTES + 1)
        with self.assertRaises(PreconditionFailedException):
            await self.bot._create_trophy(self.interaction, 'trophy', attachment)
        attachment.read.assert_not_called()
        self.interaction.response.defer.assert_not_called()

        # Reported size can not be trusted either
        self.interaction.reset_mock()
        attachment = self._svg_attachment(TROPHY_SVG + b' ' * MAX_SVG_BYTES, size=10)
        with self.assertRaises(PreconditionFailedException):
            await self.bot._create_trophy(self.interaction, 'trophy', attachment)
        self.assertIsNone(await self.conn.get_trophy_by_name('trophy'))

    async def test_create_trophy_when_download_fails(self):
        attachment = self._svg_attachment()
        attachment.read.side_effect = discord.HTTPException(MagicMock(), 'fail')

        with self.assertRaises(PreconditionFailedException):
            await self.bot._create_trophy(self.interaction, 'trophy', attachment)

        self.interaction.followup.send.assert_called_once_with(
            "Invalid trophy SVG: Could not download the file, please try again.", ephemeral=True)
        self.assertIsNone(await self.conn.get_trophy_by_name('trophy'))

    async def test_award_trophy(self):
        user_id = await self.conn.create_member(self.username, 'asd'.encode(), discord_user_id='456')
        trophy_id = await self.conn.create_trophy('trophy', TROPHY_SVG, None)

        await self.bot._award_trophy(self.interaction, self.username, 'trophy')

        trophies = await self.conn.get_user_trophies(user_id)
        self.assertEqual([t.trophy_id for t in trophies], [trophy_id])
        self.interaction.response.send_message.assert_called_once_with(
            "Awarded trophy `trophy` to: `test_user`.", ephemeral=True)

    async def test_award_trophy_to_nonexistent_user(self):
        await self.conn.create_trophy('trophy', TROPHY_SVG, None)

        with self.assertRaises(PreconditionFailedException):
            await self.bot._award_trophy(self.interaction, self.username, 'trophy')

        self.interaction.response.send_message.assert_called_once_with(
            "Failed to find a player with username: `test_user`. Check for typos and case.", ephemeral=True)

    async def test_award_trophy_to_guest(self):
        await self.conn.authenticate_user('test_user GUEST', None, verify_password=False, auto_create=True)
        await self.conn.create_trophy('trophy', TROPHY_SVG, None)

        with self.assertRaises(PreconditionFailedException):
            await self.bot._award_trophy(self.interaction, 'test_user GUEST', 'trophy')

        self.interaction.response.send_message.assert_called_once_with(
            "You cannot interact with guest users.", ephemeral=True)

    async def test_award_nonexistent_trophy(self):
        await self.conn.create_member(self.username, 'asd'.encode())

        with self.assertRaises(PreconditionFailedException):
            await self.bot._award_trophy(self.interaction, self.username, 'trophy')

        self.interaction.response.send_message.assert_called_once_with(
            "Failed to find a trophy with name: `trophy`. Check for typos.", ephemeral=True)

    async def test_award_already_awarded_trophy(self):
        user_id = await self.conn.create_member(self.username, 'asd'.encode())
        other_id = await self.conn.create_member('other_user', 'asd'.encode())
        trophy_id = await self.conn.create_trophy('trophy', TROPHY_SVG, None)
        await self.conn.award_trophy(trophy_id, other_id)

        with self.assertRaises(PreconditionFailedException):
            await self.bot._award_trophy(self.interaction, self.username, 'trophy')

        self.interaction.response.send_message.assert_called_once_with(
            "Trophy `trophy` has already been awarded.", ephemeral=True)
        self.assertEqual(await self.conn.get_user_trophies(user_id), [])
        self.assertEqual(len(await self.conn.get_user_trophies(other_id)), 1)

    async def test_award_tournament_trophy(self):
        user_id = await self.conn.create_member(self.username, 'asd'.encode())
        tournament_id = await self.conn.create_tournament('test_tournament', '123', '456', 3)
        await self.conn.create_trophy('trophy', TROPHY_SVG, tournament_id)

        with self.assertRaises(PreconditionFailedException):
            await self.bot._award_trophy(self.interaction, self.username, 'trophy')

        self.interaction.response.send_message.assert_called_once_with(
            "Trophy `trophy` belongs to a tournament and cannot be awarded manually.", ephemeral=True)
        self.assertEqual(await self.conn.get_user_trophies(user_id), [])

    async def test_command_error_handler_ignores_failed_preconditions(self):
        error = discord.app_commands.CommandInvokeError(MagicMock(), PreconditionFailedException('test'))

        with patch.object(discord.app_commands.CommandTree, 'on_error', new_callable=AsyncMock) as default_handler:
            await self.bot._on_command_error(self.interaction, error)

        default_handler.assert_not_called()
        self.interaction.response.send_message.assert_not_called()

    async def test_command_error_handler_delegates_other_errors(self):
        error = discord.app_commands.CommandInvokeError(MagicMock(), ValueError('boom'))

        with patch.object(discord.app_commands.CommandTree, 'on_error', new_callable=AsyncMock) as default_handler:
            await self.bot._on_command_error(self.interaction, error)

        default_handler.assert_called_once_with(self.bot.tree, self.interaction, error)

    async def test_command_error_handler_is_registered_on_tree(self):
        self.assertEqual(self.bot.tree.on_error, self.bot._on_command_error)

    async def test_update_trophy(self):
        await self.conn.create_trophy('trophy', TROPHY_SVG, None)
        new_svg = TROPHY_SVG + b' '

        await self.bot._update_trophy(self.interaction, ' trophy ', self._svg_attachment(new_svg))

        self.assertEqual((await self.conn.get_trophy_by_name('trophy')).svg, new_svg)
        self.interaction.followup.send.assert_called_once_with(
            "Updated graphic of trophy: `trophy`.", ephemeral=True)

    async def test_update_trophy_in_wrong_guild(self):
        self.interaction.guild.id = '1111111'
        await self.conn.create_trophy('trophy', TROPHY_SVG, None)

        with self.assertRaises(PreconditionFailedException):
            await self.bot._update_trophy(self.interaction, 'trophy', self._svg_attachment(TROPHY_SVG + b' '))

        self.assertEqual((await self.conn.get_trophy_by_name('trophy')).svg, TROPHY_SVG)

    async def test_update_nonexistent_trophy(self):
        attachment = self._svg_attachment()

        with self.assertRaises(PreconditionFailedException):
            await self.bot._update_trophy(self.interaction, 'trophy', attachment)

        self.interaction.response.send_message.assert_called_once_with(
            "Failed to find a trophy with name: `trophy`. Check for typos.", ephemeral=True)
        attachment.read.assert_not_called()

    async def test_update_trophy_with_too_big_svg(self):
        await self.conn.create_trophy('trophy', TROPHY_SVG, None)
        attachment = self._svg_attachment(size=MAX_SVG_BYTES + 1)

        with self.assertRaises(PreconditionFailedException):
            await self.bot._update_trophy(self.interaction, 'trophy', attachment)

        attachment.read.assert_not_called()
        self.assertEqual((await self.conn.get_trophy_by_name('trophy')).svg, TROPHY_SVG)

    async def test_trophy_choices(self):
        user_id = await self.conn.create_member(self.username, b'asd')
        await self.conn.create_trophy('Alpha', TROPHY_SVG, None)
        awarded = await self.conn.create_trophy('Awarded', TROPHY_SVG, None)
        await self.conn.award_trophy(awarded, user_id)

        def names(choices):
            return [c.value for c in choices]

        self.assertEqual(names(await self.bot._trophy_choices('', unawarded_only=True)), ['Alpha'])
        self.assertEqual(names(await self.bot._trophy_choices('', unawarded_only=False)), ['Alpha', 'Awarded'])
        self.assertEqual(names(await self.bot._trophy_choices('AWA', unawarded_only=False)), ['Awarded'])

    async def test_trophy_choices_are_cached_and_invalidated_on_create(self):
        self.assertEqual(await self.bot._trophy_choices('', True), [])
        await self.conn.create_trophy('late', TROPHY_SVG, None)
        self.assertEqual(await self.bot._trophy_choices('', True), [])  # cached
        self.bot._invalidate_trophy_names()
        self.assertEqual([c.value for c in await self.bot._trophy_choices('', True)], ['late'])

    async def test_create_trophy_with_taken_name_different_case(self):
        await self.conn.create_trophy('trophy', TROPHY_SVG, None)

        with self.assertRaises(PreconditionFailedException):
            await self.bot._create_trophy(self.interaction, 'Trophy', self._svg_attachment())

        self.interaction.followup.send.assert_called_once_with(
            "Failed to create trophy `Trophy`. "
            "The name may be taken, or the tournament may already have a trophy.", ephemeral=True)

    async def test_award_trophy_to_user_without_discord_id(self):
        await self.conn.create_member(self.username, 'asd'.encode())
        await self.conn.create_trophy('trophy', TROPHY_SVG, None)

        await self.bot._award_trophy(self.interaction, self.username, 'trophy')

        self.interaction.response.send_message.assert_called_once_with(
            "Awarded trophy `trophy` to: `test_user`.\nThis user has no Discord ID", ephemeral=True)

    async def test_award_trophy_failure(self):
        await self.conn.create_member(self.username, 'asd'.encode())
        await self.conn.create_trophy('trophy', TROPHY_SVG, None)

        with patch.object(self.conn, 'award_trophy', AsyncMock(return_value=False)):
            await self.bot._award_trophy(self.interaction, self.username, 'trophy')

        self.interaction.response.send_message.assert_called_once_with(
            "Something went wrong while awarding trophy `trophy` to: `test_user`.", ephemeral=True)

    async def test_award_trophy_to_banned_user(self):
        user_id = await self.conn.create_member(self.username, 'asd'.encode())
        await self.conn.ban_user(user_id, '1111', 'asd')
        await self.conn.create_trophy('trophy', TROPHY_SVG, None)
        with self.assertRaises(PreconditionFailedException):
            await self.bot._award_trophy(self.interaction, self.username, 'trophy')

        trophy = await self.conn.get_trophy_by_name('trophy')
        self.interaction.response.send_message.assert_called_once()
        self.assertEqual(trophy.user_id, None)

    async def test_update_trophy_with_invalid_svg(self):
        await self.conn.create_trophy('trophy', TROPHY_SVG, None)

        with self.assertRaises(PreconditionFailedException):
            await self.bot._update_trophy(self.interaction, 'trophy', self._svg_attachment(b'not xml at all'))

        self.interaction.followup.send.assert_called_once_with(
            "Invalid trophy SVG: The file is not valid XML.", ephemeral=True)
        self.assertEqual((await self.conn.get_trophy_by_name('trophy')).svg, TROPHY_SVG)

    async def test_update_trophy_failure(self):
        await self.conn.create_trophy('trophy', TROPHY_SVG, None)

        with patch.object(self.conn, 'update_trophy_svg', AsyncMock(return_value=False)):
            await self.bot._update_trophy(self.interaction, 'trophy', self._svg_attachment())

        self.interaction.followup.send.assert_called_once_with(
            "Something went wrong while updating trophy `trophy`.", ephemeral=True)

    async def test_logged_nonexistent_trophy(self):
        await self._assert_precondition_logged(
            'nonexistent_trophy', self.bot._update_trophy(self.interaction, 'missing', self._svg_attachment()))

    async def test_logged_invalid_trophy_name(self):
        await self._assert_precondition_logged(
            'invalid_trophy_name', self.bot._create_trophy(self.interaction, '', self._svg_attachment()))

    async def test_logged_invalid_trophy_svg(self):
        await self._assert_precondition_logged(
            'invalid_trophy_svg',
            self.bot._create_trophy(self.interaction, 'trophy', self._svg_attachment(b'not xml')))

    async def test_logged_trophy_name_taken(self):
        await self.conn.create_trophy('trophy', TROPHY_SVG, None)
        await self._assert_precondition_logged(
            'trophy_name_taken', self.bot._create_trophy(self.interaction, 'trophy', self._svg_attachment()))

    async def test_logged_tournament_trophy(self):
        await self.conn.create_member(self.username, 'asd'.encode())
        tournament_id = await self.conn.create_tournament('test_tournament', '123', '456', 3)
        await self.conn.create_trophy('trophy', TROPHY_SVG, tournament_id)
        await self._assert_precondition_logged(
            'tournament_trophy', self.bot._award_trophy(self.interaction, self.username, 'trophy'))

    async def test_logged_trophy_already_awarded(self):
        await self.conn.create_member(self.username, 'asd'.encode())
        other_id = await self.conn.create_member('other_user', 'asd'.encode())
        trophy_id = await self.conn.create_trophy('trophy', TROPHY_SVG, None)
        await self.conn.award_trophy(trophy_id, other_id)
        await self._assert_precondition_logged(
            'trophy_already_awarded', self.bot._award_trophy(self.interaction, self.username, 'trophy'))

    async def test_create_trophy_for_tournament(self):
        tournament_id = await self.conn.create_tournament('test_tournament', '123', '456', 3)

        await self.bot._create_trophy(self.interaction, 'trophy', self._svg_attachment(), tournament_id)

        trophy = await self.conn.get_tournament_trophy(tournament_id)
        self.assertEqual(trophy.name, 'trophy')

    async def test_create_trophy_for_nonexistent_tournament(self):
        with self.assertRaises(PreconditionFailedException):
            await self.bot._create_trophy(self.interaction, 'trophy', self._svg_attachment(), 'missing')

        self.interaction.response.send_message.assert_called_once_with(
            "Failed to find a tournament with ID: `missing`.", ephemeral=True)
        self.assertIsNone(await self.conn.get_trophy_by_name('trophy'))

    async def test_logged_nonexistent_tournament(self):
        await self._assert_precondition_logged(
            'nonexistent_tournament',
            self.bot._create_trophy(self.interaction, 'trophy', self._svg_attachment(), 'missing'))


class DiscordBotSendEmbedTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.config = Config()
        self.config.set('discord.bot.token', 'test_token')
        self.config.set('discord.bot.guild_id', '123')

        self.bot = DiscordBot(self.config, MagicMock(spec=DbConnector))
        self.bot.client = MagicMock()
        self.bot.client.wait_until_ready = AsyncMock()
        self.channel = MagicMock(spec=discord.TextChannel)
        self.channel.send = AsyncMock()
        self.bot.client.get_channel.return_value = self.channel

    async def test_send_embed_looks_up_channel_by_id(self):
        await self.bot.send_embed('555', {'title': 'hello'})

        self.bot.client.get_channel.assert_called_once_with(555)

    async def test_send_embed_waits_for_the_bot_to_be_ready(self):
        # the channel cache is only filled once the bot is logged in
        async def become_ready():
            self.bot.client.get_channel.return_value = self.channel

        self.bot.client.get_channel.return_value = None
        self.bot.client.wait_until_ready.side_effect = become_ready

        await self.bot.send_embed('555', {'title': 'hello'})

        self.channel.send.assert_awaited_once()

    async def test_send_embed_sends_embed_built_from_dict(self):
        await self.bot.send_embed('555', {
            'title': 'hello',
            'color': 0xFFD700,
            'fields': [{'name': 'a', 'value': 'b', 'inline': True}],
        })

        embed = self.channel.send.call_args.kwargs['embed']
        self.assertIsInstance(embed, discord.Embed)
        self.assertEqual(embed.title, 'hello')
        self.assertEqual(embed.colour.value, 0xFFD700)
        self.assertEqual(len(embed.fields), 1)
        self.assertEqual(embed.fields[0].name, 'a')
        self.assertEqual(embed.fields[0].value, 'b')
        self.assertTrue(embed.fields[0].inline)

    async def test_send_embed_raises_when_channel_is_missing(self):
        self.bot.client.get_channel.return_value = None

        with self.assertRaises(DiscordException):
            await self.bot.send_embed('555', {'title': 'hello'})

    async def test_send_embed_raises_when_channel_does_not_accept_messages(self):
        self.bot.client.get_channel.return_value = MagicMock(spec=discord.CategoryChannel)

        with self.assertRaises(DiscordException):
            await self.bot.send_embed('555', {'title': 'hello'})
