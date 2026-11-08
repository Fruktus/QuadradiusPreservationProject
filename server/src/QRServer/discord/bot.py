import logging
import re
from hashlib import md5

from QRServer.common.utils import utils
from QRServer.common.utils.cache import ttl_cache
from QRServer.config import Config
from QRServer.db.connector import DbConnector
from QRServer.db.models import DbUser, Trophy
import discord

log = logging.getLogger('qr.bot')

_MESSAGEABLE_CHANNELS = (discord.VoiceChannel, discord.StageChannel, discord.TextChannel, discord.Thread)

MAX_TROPHY_NAME_LENGTH = 64
MAX_SVG_BYTES = 100 * 1024


class DiscordException(Exception):
    pass


class PreconditionFailedException(Exception):
    # Used when required condition to carry out the command is not met
    pass


class DiscordBot:
    def __init__(self, config: Config, connector: DbConnector):
        self.config = config
        self.connector = connector

        self.token = self.config.discord_bot_token.get()
        self.guild_id = self.config.guild_id.get()
        self.user_notifications_channel_id = self.config.discord_bot_channel_user_notifications_id.get()
        self.ban_notifications_channel_id = self.config.discord_bot_channel_ban_notifications_id.get()
        self.leaderboard_channel_id = self.config.discord_bot_channel_leaderboard_id.get()
        self.max_aliases = self.config.discord_bot_max_aliases.get()

        self.username_regex = re.compile(r'[a-zA-Z0-9.\-_][a-zA-Z0-9.\-_ ]{,14}')

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
        self.tree.error(self._on_command_error)

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

        @self.tree.command(name="banuser", description="Ban specified in-game user",
                           guild=discord.Object(id=self.guild_id))
        @discord.app_commands.describe(username="The in-game username to ban", reason="Ban reason")
        async def ban_user(interaction, username: str, reason: str):
            await self._ban_user(interaction, username, reason)
        # This makes the command unavailable to anyone unless overriden by admin
        ban_user.default_permissions = discord.Permissions(permissions=0)

        @self.tree.command(name="unbanuser", description="Unban specified in-game user",
                           guild=discord.Object(id=self.guild_id))
        @discord.app_commands.describe(username="The in-game username to unban")
        async def unban_user(interaction, username: str):
            await self._unban_user(interaction, username)
        unban_user.default_permissions = discord.Permissions(permissions=0)

        @self.tree.command(name="createtrophy", description="Create a trophy that can later be awarded to a player",
                           guild=discord.Object(id=self.guild_id))
        @discord.app_commands.describe(name="Unique trophy name", svg="SVG image of the trophy",
                                       tournament_id="ID of the tournament to attach the trophy to (optional)")
        async def create_trophy(interaction, name: str, svg: discord.Attachment, tournament_id: str | None = None):
            await self._create_trophy(interaction, name, svg, tournament_id)
        create_trophy.default_permissions = discord.Permissions(permissions=0)

        @self.tree.command(name="updatetrophy", description="Replace the graphic of an existing trophy",
                           guild=discord.Object(id=self.guild_id))
        @discord.app_commands.describe(name="Name of the trophy to update", svg="New SVG image of the trophy")
        async def update_trophy(interaction, name: str, svg: discord.Attachment):
            await self._update_trophy(interaction, name, svg)
        update_trophy.default_permissions = discord.Permissions(permissions=0)

        @self.tree.command(name="awardtrophy", description="Award a trophy to the specified in-game user",
                           guild=discord.Object(id=self.guild_id))
        @discord.app_commands.describe(username="The in-game username to award the trophy to",
                                       trophy="Name of the trophy to award")
        async def award_trophy(interaction, username: str, trophy: str):
            await self._award_trophy(interaction, username, trophy)
        award_trophy.default_permissions = discord.Permissions(permissions=0)

        @award_trophy.autocomplete('trophy')
        async def award_trophy_autocomplete(interaction, current: str):
            return await self._trophy_choices(current, unawarded_only=True)

        @update_trophy.autocomplete('name')
        async def update_trophy_autocomplete(interaction, current: str):
            return await self._trophy_choices(current, unawarded_only=False)

        @self.tree.command(name="challenge", description="Challenge the specified member to a match",
                           guild=discord.Object(id=self.guild_id))
        @discord.app_commands.describe(username="The in-game member username to challenge (case-sensitive)")
        async def challenge_member(interaction, username: str):
            await self._challenge_member(interaction, username)
        challenge_member.default_permissions = discord.Permissions(permissions=0)

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

    async def _on_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """
        Called when a slash command raises.
        Precondition fails are ignored, since they are already handled, the rest is propagated.
        """
        if (isinstance(error, discord.app_commands.CommandInvokeError)
                and isinstance(error.original, PreconditionFailedException)):
            return

        await discord.app_commands.CommandTree.on_error(self.tree, interaction, error)

    # # # # # #
    # Helpers #
    # # # # # #
    async def send_embed(self, channel_id: str, embed: dict) -> None:
        """
        Args:
            embed: the embed in the shape of Discord's embed object

        Raises:
            DiscordException: if the channel is not found or does not accept messages
        """
        # Ensure that the bot is ready before messaging
        await self.client.wait_until_ready()
        channel = self.client.get_channel(int(channel_id))
        if not isinstance(channel, _MESSAGEABLE_CHANNELS):
            raise DiscordException(f'Channel {channel_id} not found or not accepting messages: {channel}')
        await channel.send(embed=discord.Embed.from_dict(embed))

    async def _send_notification(self, message: str, channel: str) -> None:
        discord_channel = self.client.get_channel(int(channel))

        if isinstance(discord_channel, _MESSAGEABLE_CHANNELS):
            log.debug(f"Sending notification: {repr(message)}")
            await discord_channel.send(message)
        else:
            log.warning(
                'notifications channel not found or not accepting messages: ' +
                str(discord_channel))

    @ttl_cache(ttl=60)
    async def _trophy_names(self, search: str, unawarded_only: bool) -> list[str]:
        return await self.connector.get_trophy_names(search, unawarded_only)

    def _invalidate_trophy_names(self) -> None:
        self._trophy_names.cache_clear(self)

    async def _trophy_choices(self, current: str, unawarded_only: bool):
        names = await self._trophy_names(current.strip().lower(), unawarded_only)
        return [discord.app_commands.Choice(name=n, value=n) for n in names]

    async def _respond(self, interaction: discord.Interaction, message: str) -> None:
        """Replies ephemerally, picking the right path depending on whether the interaction was deferred."""
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)

    async def _download_svg(self, interaction: discord.Interaction,
                            attachment: discord.Attachment) -> tuple[bytes, str | None]:
        """Returns (data, error). Defers the interaction before the (potentially slow) download."""
        too_big = f"The file is too big, the limit is {MAX_SVG_BYTES // 1024} KiB."
        if attachment.size > MAX_SVG_BYTES:
            return b'', too_big

        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)
        try:
            data = await attachment.read()
        except discord.HTTPException:
            return b'', "Could not download the file, please try again."

        if len(data) > MAX_SVG_BYTES:  # reported size can't be fully trusted
            return b'', too_big
        return data, utils.validate_svg(data)

    # # # # # # # # #
    # Preconditions #
    # # # # # # # # #
    async def _require_valid_username(self, interaction_id: str, interaction: discord.Interaction, username: str):
        # Checks if the username is of correct length and format

        if not self.username_regex.fullmatch(username):
            log.debug(f"({interaction_id}) precondition failed: invalid_username")
            await interaction.response.send_message(
                "Username should:\n"
                "- contain at least one non-whitespace character\n"
                "- contain only letters, numbers, dots, hyphens, and underscores\n"
                "- be no longer than 15 characters.",
                ephemeral=True)
            raise PreconditionFailedException('invalid_username')

        if username.lower().endswith(' guest'):
            log.debug(f"({interaction_id}) precondition failed: guest_username")
            await interaction.response.send_message(
                "Username cannot end with guest.",
                ephemeral=True)
            raise PreconditionFailedException('guest_username')

    async def _require_has_available_aliases(self, interaction_id: str, interaction: discord.Interaction,
                                             discord_user_id: int):
        user_accounts = await self.connector.get_users_by_discord_id(str(discord_user_id))
        if len(user_accounts) >= self.max_aliases:
            log.debug(f"({interaction_id}) precondition failed: over_max_aliases")
            await interaction.response.send_message(
                    f"You have reached the maximum number of aliases: {self.max_aliases}.",
                    ephemeral=True)
            raise PreconditionFailedException('over_max_aliases')

    async def _require_in_guild_context(self, interaction_id: str, interaction: discord.Interaction):
        # Checks that the command was invoked from within a guild (not a DM)
        if not hasattr(interaction.user, 'guild'):
            log.debug(f"({interaction_id}) precondition failed: no_guild_context")
            await interaction.response.send_message(
                "I'm a bot, I don't respond to messages. Please use the slash command in an appropriate channel.",
                ephemeral=True)
            raise PreconditionFailedException('no_guild_context')

    async def _require_belongs_to_bot_guild(self, interaction_id: str, interaction: discord.Interaction):
        # Checks if the user is allowed to use the bot
        # If the user is not part of the server, then not

        if not interaction.guild or int(interaction.guild.id) != int(self.guild_id):
            log.debug(f"({interaction_id}) precondition failed: invalid_user_guild")
            await interaction.response.send_message(
                "You must be in this bot's discord server to use it.",
                ephemeral=True)
            raise PreconditionFailedException('invalid_user_guild')

    async def _require_user_by_username(self, interaction_id: str, interaction: discord.Interaction,
                                        username: str) -> DbUser:
        user = await self.connector.get_user_by_username(username)
        if not user:
            log.debug(f"({interaction_id}) precondition failed: nonexistent_user")
            await interaction.response.send_message(
                f"Failed to find a player with username: `{username}`. Check for typos and case.",
                ephemeral=True)
            raise PreconditionFailedException('nonexistent_user')
        return user

    async def _require_has_registered_aliases(self, interaction_id: str, interaction: discord.Interaction,
                                              interaction_user_id: int) -> list[DbUser]:
        user_account_list = await self.connector.get_users_by_discord_id(str(interaction_user_id))
        if not user_account_list:
            log.debug(f"({interaction_id}) precondition failed: user_not_registered")
            await interaction.response.send_message(
                "You need to register first.",
                ephemeral=True)
            raise PreconditionFailedException('user_not_registered')
        return sorted(user_account_list, key=lambda u: u.created_at)

    async def _require_user_not_banned(self, interaction_id: str, interaction: discord.Interaction, user: DbUser):
        if user.is_banned:
            log.debug(f"({interaction_id}) precondition failed: user_banned")
            await interaction.response.send_message(
                f"Account `{user.username}` is banned.",
                ephemeral=True)
            raise PreconditionFailedException('user_banned')

    async def _require_user_not_guest(self, interaction_id: str, interaction: discord.Interaction, user: DbUser):
        if user.is_guest:
            log.debug(f"({interaction_id}) precondition failed: targeted_guest_user")
            await interaction.response.send_message(
                "You cannot interact with guest users.",
                ephemeral=True)
            raise PreconditionFailedException('targeted_guest_user')

    async def _require_interaction_with_non_owned_account(
        self, interaction_id: str, interaction: discord.Interaction, user: DbUser, alias_list: list[DbUser]
    ):
        if user.username in {alias.username for alias in alias_list}:
            log.debug(f"({interaction_id}) precondition failed: same_discord_account_interaction")
            await interaction.response.send_message(
                "You cannot interact with a different account tied to the same Discord account.",
                ephemeral=True)
            raise PreconditionFailedException('same_discord_account_interaction')

    async def _require_trophy_by_name(self, interaction_id: str, interaction: discord.Interaction,
                                      name: str) -> Trophy:
        trophy = await self.connector.get_trophy_by_name(name)
        if not trophy:
            log.debug(f"({interaction_id}) precondition failed: nonexistent_trophy")
            await interaction.response.send_message(
                f"Failed to find a trophy with name: `{name}`. Check for typos.", ephemeral=True)
            raise PreconditionFailedException('nonexistent_trophy')
        return trophy

    async def _require_valid_trophy_name(self, interaction_id: str, interaction: discord.Interaction, name: str):
        if not name or len(name) > MAX_TROPHY_NAME_LENGTH or '`' in name or not name.isprintable():
            log.debug(f"({interaction_id}) precondition failed: invalid_trophy_name")
            await interaction.response.send_message(
                f"Trophy name should be 1-{MAX_TROPHY_NAME_LENGTH} printable characters "
                "and not contain backticks.",
                ephemeral=True)
            raise PreconditionFailedException('invalid_trophy_name')

    async def _require_valid_svg(self, interaction_id: str, interaction: discord.Interaction,
                                 attachment: discord.Attachment) -> bytes:
        data, error = await self._download_svg(interaction, attachment)
        if error:
            log.debug(f"({interaction_id}) precondition failed: invalid_trophy_svg")
            await self._respond(interaction, f"Invalid trophy SVG: {error}")
            raise PreconditionFailedException('invalid_trophy_svg')
        return data

    async def _require_tournament_exists(self, interaction_id: str, interaction: discord.Interaction,
                                         tournament_id: str) -> None:
        if not await self.connector.get_tournament(tournament_id):
            log.debug(f"({interaction_id}) precondition failed: nonexistent_tournament")
            await interaction.response.send_message(
                f"Failed to find a tournament with ID: `{tournament_id}`.", ephemeral=True)
            raise PreconditionFailedException('nonexistent_tournament')

    # # # # # # # # # # #
    # Command Handlers  #
    # # # # # # # # # # #
    async def _register(self, interaction: discord.Interaction, username: str) -> None:
        interaction_id = utils.base62_id()

        log.debug(f"({interaction_id}) Register command received from '{interaction.user}' for account '{username}'")
        username = username.strip()

        await self._require_in_guild_context(interaction_id, interaction)
        await self._require_belongs_to_bot_guild(interaction_id, interaction)
        await self._require_valid_username(interaction_id, interaction, username)
        await self._require_has_available_aliases(interaction_id, interaction, interaction.user.id)

        # check if the username is available
        user = await self.connector.get_user_by_username(username)
        if user:
            # Check if the user is auto-registered, if so let know that it can be claimed
            if not user.password:
                log.debug(f"({interaction_id}) precondition failed: username_claimable")
                await interaction.response.send_message(
                    f"Username `{username}` is in use but can be claimed.\n"
                    f"Run `/claim {username}` to claim it.",
                    ephemeral=True)
            else:
                log.debug(f"({interaction_id}) precondition failed: username_taken")
                await interaction.response.send_message(
                    f"Username `{username}` is taken. Please choose a different one.", ephemeral=True)
            return

        log.debug(f"({interaction_id}) Registering new account for '{interaction.user}' with username '{username}'")

        # if it is register the user and send temp password
        password = utils.generate_random_password(20)
        await self.connector.create_member(
            username=username,
            password=md5(f'++{username.upper()}++{password}'.encode()).hexdigest().encode(),
            discord_user_id=str(interaction.user.id),
        )

        await self._send_notification(
            "### Account registered\n"
            f"- Owner: <@{interaction.user.id}>\n"
            f"- Username: `{username}`",
            self.user_notifications_channel_id,
        )

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
            log.warning(f"({interaction_id}) Failed to send register credentials via DM", exc_info=e)
            await interaction.response.send_message(
                f"Registered account: `{username}`, failed to send credentials - check privacy settings.",
                ephemeral=True)

    async def _claim(self, interaction: discord.Interaction, username: str) -> None:
        interaction_id = utils.base62_id()
        log.debug(f"({interaction_id}) Claim command received from '{interaction.user}' for account '{username}'")
        username = username.strip()

        # Run basic validations
        await self._require_in_guild_context(interaction_id, interaction)
        await self._require_belongs_to_bot_guild(interaction_id, interaction)
        await self._require_valid_username(interaction_id, interaction, username)
        await self._require_has_available_aliases(interaction_id, interaction, interaction.user.id)

        # check if the username is available for claim - no preconditions to allow custom message
        user = await self.connector.get_user_by_username(username)
        if not user:
            log.debug(f"({interaction_id}) precondition failed: nonexistent_user")
            await interaction.response.send_message(
                "This username is not registered."
                f" Please register it instead by running `/register {username}`.",
                ephemeral=True)
            return

        if user.password:
            log.debug(f"({interaction_id}) precondition failed: username_taken")
            await interaction.response.send_message(
                "This username is taken. Please choose a different one.", ephemeral=True)
            return

        # if it is claim the user and send temp password
        log.debug(f"({interaction_id}) Claiming the account '{interaction.user}' with username '{username}'")
        password = utils.generate_random_password(20)

        await self.connector.claim_member(
            user_id=user.user_id,
            password=md5(f'++{username.upper()}++{password}'.encode()).hexdigest().encode(),
            discord_user_id=str(interaction.user.id),
        )

        await self._send_notification(
            "### Account claimed\n"
            f"- Owner: <@{interaction.user.id}>\n"
            f"- Username: `{username}`",
            self.user_notifications_channel_id,
        )

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
            log.warning(f"({interaction_id}) Failed to send claim credentials via DM", exc_info=e)
            await interaction.response.send_message(
                f"Claimed account: `{username}`, failed to send credentials - check privacy settings.",
                ephemeral=True)

    async def _reset_password(self, interaction: discord.Interaction, username: str) -> None:
        interaction_id = utils.base62_id()
        log.debug(f"({interaction_id}) resetpassword command received from '{interaction.user}'")
        username = username.strip()

        await self._require_belongs_to_bot_guild(interaction_id, interaction)

        # Get user's accounts
        user_account_list = await self.connector.get_users_by_discord_id(str(interaction.user.id))
        user_accounts = {user.username: user for user in user_account_list}

        if username not in user_accounts:
            log.debug(
                f"({interaction_id}) precondition failed: not_owned_account -"
                f" '{interaction.user}' tried to change password for '{username}'")

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
            log.warning(f"({interaction_id}) Failed to send new password via DM", exc_info=e)
            await interaction.response.send_message(
                f"Password for account was reset: `{username}`, failed to send credentials - check privacy settings.",
                ephemeral=True)

    async def _ban_user(self, interaction: discord.Interaction, username: str, reason: str) -> None:
        interaction_id = utils.base62_id()
        log.debug(f"({interaction_id}) banuser command received from '{interaction.user}'")
        username = username.strip()

        await self._require_belongs_to_bot_guild(interaction_id, interaction)
        user = await self._require_user_by_username(interaction_id, interaction, username)

        result = await self.connector.ban_user(user.user_id, str(interaction.user.id), reason)
        if not result:
            log.warning(
                f'({interaction_id}) Something went wrong while banning user. '
                f'Username: {username}, user_id: {user.user_id}')
            await interaction.response.send_message(
                f'Something went wrong while banning user: `{username}`.', ephemeral=True)
            return

        await self._send_notification(
            f"### Account banned{' (again)' if user.is_banned else ''}\n"
            f"- Banned user: `{username}`\n"
            f"- Banned by: <@{interaction.user.id}>\n"
            f"- Reason: *{reason}*\n",
            self.ban_notifications_channel_id,
        )

        # Ban already happened at this point - this only decides whether we can also DM the user,
        # not whether the ban itself is valid, so it's handled inline rather than as a precondition.
        if not user.discord_user_id:
            log.debug(f"({interaction_id}) banned user '{username}' has no Discord ID, skipping DM")
            await interaction.response.send_message(
                f"Banned user: `{username}`.\n"
                "This user has no Discord ID",
                ephemeral=True,
            )
            return
        else:
            await interaction.response.send_message(
                f"Banned user: `{username}`.", ephemeral=True
            )

        if not user.is_banned:
            discord_user = await self.client.fetch_user(int(user.discord_user_id))
            await discord_user.send(
                f"### Ban\n"
                f"- Your account: `{username}` has been banned.\n"
                f"- Reason: *{reason}*\n"
            )

    async def _unban_user(self, interaction: discord.Interaction, username: str):
        interaction_id = utils.base62_id()
        log.debug(f"({interaction_id}) unbanuser command received from '{interaction.user}'")
        username = username.strip()

        await self._require_belongs_to_bot_guild(interaction_id, interaction)

        # Get user's accounts
        user = await self._require_user_by_username(interaction_id, interaction, username)

        if not user.is_banned:
            log.debug(f"({interaction_id}) precondition failed: user_not_banned")
            await interaction.response.send_message(
                "This user is not currently banned",
                ephemeral=True,
            )
            return

        result = await self.connector.unban_user(user.user_id, str(interaction.user.id))
        if not result:
            log.warning(
                f'({interaction_id}) Something went wrong while unbanning user. '
                f'Username: {username}, user_id: {user.user_id}')
            await interaction.response.send_message(
                f'Something went wrong while unbanning user: `{username}`.', ephemeral=True)
            return

        await self._send_notification(
            "### Account unbanned\n"
            f"- Unbanned user: `{username}`\n"
            f"- Unbanned by: <@{interaction.user.id}>\n",
            self.ban_notifications_channel_id
        )

        if not user.discord_user_id:
            log.debug(f"({interaction_id}) unbanned user '{username}' has no Discord ID, skipping DM")
            await interaction.response.send_message(
                f"Unbanned user: `{username}`.\n"
                "This user has no Discord ID",
                ephemeral=True,
            )
            return
        else:
            await interaction.response.send_message(
                f"Unbanned user: `{username}`.",
                ephemeral=True,
            )

        discord_user = await self.client.fetch_user(int(user.discord_user_id))
        await discord_user.send(
            f"### Unban\n"
            f"- Your account: `{username}` has been unbanned.\n"
        )

    async def _create_trophy(self, interaction: discord.Interaction, name: str, svg: discord.Attachment,
                             tournament_id: str | None = None) -> None:
        interaction_id = utils.base62_id()
        log.debug(f"({interaction_id}) createtrophy command received from '{interaction.user}'")
        name = name.strip()
        tournament_id = tournament_id.strip() if tournament_id else None

        await self._require_belongs_to_bot_guild(interaction_id, interaction)
        await self._require_valid_trophy_name(interaction_id, interaction, name)
        if tournament_id:
            await self._require_tournament_exists(interaction_id, interaction, tournament_id)
        svg_data = await self._require_valid_svg(interaction_id, interaction, svg)

        trophy_id = await self.connector.create_trophy(name, svg_data, tournament_id)
        if not trophy_id:
            log.debug(f"({interaction_id}) precondition failed: trophy_name_taken")
            await self._respond(interaction,
                                f"Failed to create trophy `{name}`. The name may be taken, "
                                "or the tournament may already have a trophy.")
            raise PreconditionFailedException('trophy_create_conflict')

        log.info(f"({interaction_id}) trophy '{name}' ({trophy_id}) created by '{interaction.user}'")
        self._invalidate_trophy_names()
        await self._respond(interaction, f"Created trophy: `{name}`. Use `/awardtrophy` to award it to a player.")

    async def _award_trophy(self, interaction: discord.Interaction, username: str, trophy_name: str) -> None:
        interaction_id = utils.base62_id()
        log.debug(f"({interaction_id}) awardtrophy command received from '{interaction.user}'")
        username = username.strip()
        trophy_name = trophy_name.strip()

        await self._require_belongs_to_bot_guild(interaction_id, interaction)
        user = await self._require_user_by_username(interaction_id, interaction, username)
        await self._require_user_not_guest(interaction_id, interaction, user)
        await self._require_user_not_banned(interaction_id, interaction, user)

        trophy = await self._require_trophy_by_name(interaction_id, interaction, trophy_name)

        if trophy.tournament_id:
            log.debug(f"({interaction_id}) precondition failed: tournament_trophy")
            await interaction.response.send_message(
                f"Trophy `{trophy_name}` belongs to a tournament and cannot be awarded manually.", ephemeral=True)
            raise PreconditionFailedException('tournament_trophy')

        if trophy.user_id:
            log.debug(f"({interaction_id}) precondition failed: trophy_already_awarded")
            await interaction.response.send_message(
                f"Trophy `{trophy_name}` has already been awarded.", ephemeral=True)
            raise PreconditionFailedException('trophy_already_awarded')

        result = await self.connector.award_trophy(trophy.trophy_id, user.user_id)
        if not result:
            log.warning(
                f'({interaction_id}) Something went wrong while awarding trophy. '
                f'Trophy: {trophy_name}, trophy_id: {trophy.trophy_id}, username: {username}, user_id: {user.user_id}')
            await interaction.response.send_message(
                f'Something went wrong while awarding trophy `{trophy_name}` to: `{username}`.', ephemeral=True)
            return

        log.info(f"({interaction_id}) trophy '{trophy_name}' ({trophy.trophy_id}) "
                 f"awarded to '{username}' by '{interaction.user}'")
        self._invalidate_trophy_names()

        if user.discord_user_id:
            await interaction.response.send_message(
                f"Awarded trophy `{trophy_name}` to: `{username}`.", ephemeral=True)
        else:
            log.warning(f"({interaction_id}) awarded user '{username}' has no Discord ID")
            await interaction.response.send_message(
                f"Awarded trophy `{trophy_name}` to: `{username}`.\n"
                "This user has no Discord ID",
                ephemeral=True,
            )

    async def _update_trophy(self, interaction: discord.Interaction, name: str, svg: discord.Attachment) -> None:
        interaction_id = utils.base62_id()
        log.debug(f"({interaction_id}) updatetrophy command received from '{interaction.user}'")
        name = name.strip()

        await self._require_belongs_to_bot_guild(interaction_id, interaction)
        trophy = await self._require_trophy_by_name(interaction_id, interaction, name)
        svg_data = await self._require_valid_svg(interaction_id, interaction, svg)

        if not await self.connector.update_trophy_svg(trophy.trophy_id, svg_data):
            log.warning(f"({interaction_id}) Something went wrong while updating trophy graphic. "
                        f"Trophy: {name}, trophy_id: {trophy.trophy_id}")
            await self._respond(interaction, f"Something went wrong while updating trophy `{name}`.")
            return

        log.info(f"({interaction_id}) trophy '{name}' ({trophy.trophy_id}) graphic updated by '{interaction.user}'")
        await self._respond(interaction, f"Updated graphic of trophy: `{name}`.")

    async def _challenge_member(self, interaction: discord.Interaction, username: str) -> None:
        """
        Generates invite links for direct matches.
        """
        interaction_id = utils.base62_id()

        # Note that challenger and challenged are similar, pay attention to code.
        log.debug(f"({interaction_id}) challenge command received from '{interaction.user}'")
        username = username.strip()

        await self._require_in_guild_context(interaction_id, interaction)
        await self._require_belongs_to_bot_guild(interaction_id, interaction)
        user_account_list = await self._require_has_registered_aliases(interaction_id, interaction, interaction.user.id)

        # Get the oldest challenger alias if they have more than one
        challenger_user = user_account_list[0]

        await self._require_user_not_banned(interaction_id, interaction, challenger_user)
        challenged_user = await self._require_user_by_username(interaction_id, interaction, username)
        await self._require_interaction_with_non_owned_account(
            interaction_id, interaction, challenged_user, user_account_list)
        await self._require_user_not_banned(interaction_id, interaction, challenged_user)
        await self._require_user_not_guest(interaction_id, interaction, challenged_user)

        # Check if there is a pending active invite, if so do not resend
        existing_invite = await self.connector.get_latest_match_invite_between(
            challenger_user.user_id, challenged_user.user_id)

        if existing_invite and existing_invite.can_be_used:
            log.debug(f"({interaction_id}) precondition failed: active_invite_exists")
            challenge_url = f'{self.config.origin.get()}/challenge?id={existing_invite.invite_id}'
            await interaction.response.send_message(
                f"You already have an active invite with this user: {challenge_url}",
                ephemeral=True)
            return

        challenger_user_dc = interaction.user
        challenged_user_dc = await self.client.fetch_user(int(challenged_user.discord_user_id))

        # Create the invite and prepare the link
        challenge_id = await self.connector.create_match_invite(
            challenged_id=challenged_user.user_id, challenger_id=challenger_user.user_id)
        challenge_url = f'{self.config.origin.get()}/challenge?id={challenge_id}'

        # Handle restrictive DM permissions exceptions
        try:
            await challenged_user_dc.send(
                "### Match Invite\n"
                "- You have been invited to a match!\n"
                f"- Your opponent is: <@{challenger_user.discord_user_id}> - `{challenger_user.username}`\n"
                f"- Match link: {challenge_url}\n"
                f"- The match link will be valid for the next {self.config.challenge_invite_duration.get()} minute"
                f"{'s' if self.config.challenge_invite_duration.get() != 1 else ''}"
            )
        except (discord.Forbidden, discord.HTTPException) as e:
            log.warning(
                f"({interaction_id}) Failed to DM challenged user '{challenged_user.username}'", exc_info=e)
            await interaction.response.send_message(
                f"Created a challenge for `{username}`, but couldn't DM them (their privacy settings may block it).\n"
                f"You can send them this link yourself: {challenge_url}",
                ephemeral=True)
            return

        try:
            await challenger_user_dc.send(
                "### Match Invite\n"
                "- You have been invited to a match!\n"
                f"- Your opponent is: <@{challenged_user.discord_user_id}> - `{challenged_user.username}`\n"
                f"- Match link: {challenge_url}\n"
                f"- The match link will be valid for the next {self.config.challenge_invite_duration.get()} minute"
                f"{'s' if self.config.challenge_invite_duration.get() != 1 else ''}"
            )
        except (discord.Forbidden, discord.HTTPException) as e:
            log.warning(f"({interaction_id}) Failed to DM challenger", exc_info=e)
            await interaction.response.send_message(
                f"Challenge sent to `{username}`, but I couldn't DM you the link.\n"
                f"Here it is: {challenge_url}",
                ephemeral=True)
            return

        await interaction.response.send_message(
            "### Invite has been sent",
            ephemeral=True)
