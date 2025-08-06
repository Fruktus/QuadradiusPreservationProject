import logging
import re
from hashlib import md5

from QRServer.common import utils
from QRServer.config import Config
from QRServer.db.connector import DbConnector
import discord

log = logging.getLogger('qr.bot')


class DiscordException(Exception):
    pass


class DiscordBot:
    def __init__(self, config: Config, connector: DbConnector):
        self.config = config
        self.connector = connector

        self.token = self.config.discord_bot_token.get()
        self.guild_id = self.config.guild_id.get()
        self.user_notifications_channel_id = self.config.discord_bot_channel_user_notifications_id.get()
        self.max_aliases = self.config.discord_bot_max_aliases.get()

        self.username_regex = re.compile(r'^[a-zA-Z0-9.\-_][a-zA-Z0-9.\-_\s]{,14}$')

        if not self.token:
            raise DiscordException('Discord bot token is not set. Bot will not be started.')

        if not self.guild_id:
            raise DiscordException('Discord guild ID is not set. Bot will not be started.')

        if not self.user_notifications_channel_id:
            log.info('Discord user notifications channel ID is not set. Notifications will not be sent.')

        intents = discord.Intents.default()
        intents.messages = True  # Listen to messages in general (includes DMs)
        intents.message_content = True  # Required for reading message content
        intents.guilds = True  # Used for guilds channels etc.

        self.client = discord.Client(intents=intents)
        self.tree = discord.app_commands.CommandTree(self.client)

    async def run_bot(self):
        @self.tree.command(name="register", description="Register a new member")
        @discord.app_commands.describe(username="The username to register")
        async def register(interaction, username: str):
            await self._register(interaction, username)

        @self.tree.command(name="claim", description="Claim autoregistered member")
        @discord.app_commands.describe(username="The username to claim")
        async def claim(interaction, username: str):
            await self._claim(interaction, username)

        @self.tree.command(name="resetpassword", description="Reset password for a member")
        @discord.app_commands.describe(username="The username to reset the password for")
        async def reset_password(interaction, username: str):
            await self._reset_password(interaction, username)

        @self.client.event
        async def on_ready():
            await self._on_ready()

        @self.client.event
        async def on_message(message):
            return

        # Set discord logger to use the same handlers as the main logger
        discord_logger = logging.getLogger('discord')
        discord_logger.setLevel(logging.INFO)
        discord_logger.handlers = logging.getLogger('qr').handlers

        try:
            await self.client.start(self.token)
        except discord.errors.LoginFailure:
            raise DiscordException('Discord bot token is invalid. Bot will not be started.')

    async def _on_ready(self):
        """
        Called when the bot is ready to start receiving events
        Sets bot's status and syncs the slash commands"""

        await self.client.change_presence(
            activity=discord.Activity(type=discord.ActivityType.watching, name="QR battles"))
        await self.tree.sync(guild=discord.Object(id=self.guild_id))
        log.info("Discord bot is ready")

    async def _register(self, interaction: discord.Interaction, username: str) -> None:
        log.debug(f"Register command received from '{interaction.user}' for account '{username}'")
        username = username.strip()

        valid, error_message = await self._basic_validations_passed(
            interaction=interaction, username=username)
        if not valid:
            await interaction.response.send_message(error_message, ephemeral=True)
            return

        # check if the username is available
        user = await self.connector.get_user_by_username(username)
        if user:
            # Check if the user is auto-registered, if so let know that it can be claimed
            if not user.password:
                await interaction.response.send_message(
                    f"Username `{username}` is in use but can be claimed.\n"
                    f"Run `/claim {username}` to claim it.",
                    ephemeral=True)
            else:
                await interaction.response.send_message(
                    f"Username `{username}` is taken. Please choose a different one.", ephemeral=True)
            return

        log.debug(f"Registering new account for '{interaction.user}' with username '{username}'")

        # if it is register the user and send temp password
        password = utils.generate_random_password(20)
        await self.connector.create_member(
            username=username,
            password=md5(f'++{username.upper()}++{password}'.encode()).hexdigest().encode(),
            discord_user_id=interaction.user.id,
        )

        await self._send_user_notification(
            "### Account registered\n"
            f"- Owner: <@{interaction.user.id}>\n"
            f"- Username: `{username}`")

        # Respond to interaction so it doesn't show as command fail
        # and send credentials via DM
        try:
            await interaction.user.send(
                "### Registration successful\n"
                f"- Registered account: `{username}`.\n"
                f"- Current password is: ||`{password}`||.\n"
                "You can change it in the game.\n"
                f"If you forget it, you can run `/resetpassword {username}` to reset it.")

            await interaction.response.send_message(
                f"Registered account: `{username}`, credentials have been sent via DM.",
                ephemeral=True)
        except Exception as e:
            log.warning("Failed to send register credentials via DM", exc_info=e)
            await interaction.response.send_message(
                f"Registered account: `{username}`, failed to send credentials - check privacy settings.",
                ephemeral=True)

    async def _claim(self, interaction: discord.Interaction, username: str) -> None:
        log.debug(f"Claim command received from '{interaction.user}' for account '{username}'")
        username = username.strip()

        # Run basic validations
        valid, error_message = await self._basic_validations_passed(
            interaction=interaction, username=username)
        if not valid:
            await interaction.response.send_message(error_message, ephemeral=True)
            return

        # check if the username is available for claim
        user = await self.connector.get_user_by_username(username)
        if not user:
            await interaction.response.send_message(
                "This username is not registered."
                f" Please register it instead by running `/register {username}`.",
                ephemeral=True)
            return

        if user and user.password:
            await interaction.response.send_message(
                "This username is taken. Please choose a different one.", ephemeral=True)
            return

        # if it is claim the user and send temp password
        log.debug(f"Claiming the account '{interaction.user}' with username '{username}'")
        password = utils.generate_random_password(20)

        await self.connector.claim_member(
            user_id=user.user_id,
            password=md5(f'++{username.upper()}++{password}'.encode()).hexdigest().encode(),
            discord_user_id=interaction.user.id,
        )

        await self._send_user_notification(
            "### Account claimed\n"
            f"- Owner: <@{interaction.user.id}>\n"
            f"- Username: `{username}`")

        # Respond to interaction so it doesn't show as command fail
        # and send credentials via DM
        try:
            await interaction.user.send(
                "### Claim successful\n"
                f"- Claimed account: `{username}`.\n"
                f"- Current password is: ||`{password}`||.\n"
                "You can change it in the game.\n"
                f"If you forget it, you can run `/resetpassword {username}` to reset it.")

            await interaction.response.send_message(
                f"Claimed account: `{username}`, credentials have been sent via DM.",
                ephemeral=True)
        except Exception as e:
            log.warning("Failed to send claim credentials via DM", exc_info=e)
            await interaction.response.send_message(
                f"Claimed account: `{username}`, failed to send credentials - check privacy settings.",
                ephemeral=True)

    async def _reset_password(self, interaction: discord.Interaction, username: str) -> None:
        log.debug(f"resetpassword command received from '{interaction.user}'")
        username = username.strip()

        # Get user's accounts
        user_accounts = await self.connector.get_users_by_discord_id(interaction.user.id)
        user_accounts = {user.username: user for user in user_accounts}

        if username not in user_accounts:
            log.debug(f"User '{interaction.user}' tried to change password for not owned account: '{username}'")

            owned_usernames = ', '.join([f'`{acc}`' for acc in list(user_accounts.keys())])
            await interaction.response.send_message(
                f"You do not have an account with username: `{username}`.\n"
                f"Owned accounts: {owned_usernames}",
                ephemeral=True)
            return

        # if it is reset the password and send temp password
        password = utils.generate_random_password(20)
        await self.connector.change_user_password(
            user_id=user_accounts[username].user_id,
            password=md5(f'++{username.upper()}++{password}'.encode()).hexdigest().encode(),
        )

        # Respond to interaction so it doesn't show as command fail
        # and send credentials via DM
        try:
            await interaction.user.send(
                "### Password reset successful\n"
                f"Password was reset for account: `{username}`.\n"
                f"Your new password is: ||`{password}`||.")
            await interaction.response.send_message(
                f"Password for account was reset: `{username}`, credentials have been sent via DM.",
                ephemeral=True)
        except Exception as e:
            log.warning("Failed to send new password via DM", exc_info=e)
            await interaction.response.send_message(
                f"Password for account was reset: `{username}`, failed to send credentials - check privacy settings.",
                ephemeral=True)

    def _validate_username(self, username: str) -> tuple[bool, str]:
        # Checks if the username is of correct length and format
        # Returns a tuple of (valid, error message)

        if not self.username_regex.match(username):
            return (False,
                    "Username should:\n"
                    "- contain at least one non-whitespace character\n"
                    "- contain only letters, numbers, dots, hyphens, and underscores\n"
                    "- be no longer than 15 characters.")

        if username.lower().endswith(' guest'):
            return (False, "Username cannot end with guest.")

        return (True, "")

    async def _is_allowed_to_register(self, discord_user_id: str) -> tuple[bool, str]:
        # Checks if the user meets criteria to register a new username
        # Such as max alias count or banned status
        # Returns a tuple of (allowed, error message)

        user_accounts = await self.connector.get_users_by_discord_id(discord_user_id)
        if len(user_accounts) >= self.max_aliases:
            return (False, f"You have reached the maximum number of aliases: {self.max_aliases}.")

        return (True, "")

    def _can_use_bot(self, guild_id: str) -> tuple[bool, str]:
        # Checks if the user is allowed to use the bot
        # If the user is not part of the server, then not
        # Returns a tuple of (allowed, error message)

        if guild_id != self.guild_id:
            return (False, "You must be in this bot's discord server to use it.")

        return (True, "")

    async def _basic_validations_passed(
            self, interaction: discord.Interaction, username: str) -> tuple[bool, str]:
        # Checks the basic things for registering and claiming a username
        discord_user_id = interaction.user.id

        if not hasattr(interaction.user, 'guild'):
            return (
                False,
                "I'm a bot, I don't respond to messages. Please use the slash command in an appropriate channel.")

        user_guild_id = str(interaction.user.guild.id)

        # Check if the discord user is allowed to interact with the bot
        can_use_bot, error_message = self._can_use_bot(user_guild_id)
        if not can_use_bot:
            return (False, error_message)

        # Check if the username specified is valid (run this first to avoid unnecessary queries)
        is_valid, error_message = self._validate_username(username)
        if not is_valid:
            return (False, error_message)

        # check if the client can register new username, otherwise send error with notif
        allowed_to_register, error_message = await self._is_allowed_to_register(
            discord_user_id=discord_user_id)
        if not allowed_to_register:
            return (False, error_message)

        return (True, "")

    async def _send_user_notification(self, message: str) -> None:
        # Send a message to the user notifications channel
        if not self.user_notifications_channel_id:
            return

        channel = self.client.get_channel(int(self.user_notifications_channel_id))
        if channel:
            log.debug(f"Sending user notification: {repr(message)}")
            await channel.send(message)
        else:
            log.warning(f'User notifications channel: {self.user_notifications_channel_id} not found')
