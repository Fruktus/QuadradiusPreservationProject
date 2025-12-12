from datetime import datetime
import logging
from random import shuffle
import re
from hashlib import md5

from QRServer.common import utils
from QRServer.common.full_binary_tree_indexer import FullBinaryTreeIndexer
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

        @self.tree.command(name="create_tournament", description="Create tournament")
        @discord.app_commands.describe(
            tournament_name="Name of the tournament",
            dc_msg_id="Tournament registration message",
            required_matches_per_duel="The amount of matches that are needed to qualify for round")
        async def create_tournament(interaction, tournament_name: str, dc_msg_id: str, required_matches_per_duel):
            await self._create_tournament(interaction, tournament_name, dc_msg_id, required_matches_per_duel)
        create_tournament.default_permissions = discord.Permissions(permissions=0)

        @self.tree.command(name="start_tournament", description="Start tournament")
        @discord.app_commands.describe(
            tournament_id="Id of the tournament",
            active_until="Date until which matches for first round are accepted, in the isoformat. Ex: 2021-07-27T16:02:08.070557")
        async def start_tournament(interaction, tournament_name: str, active_until: str):
            await self._start_tournament(interaction, tournament_name, active_until)
        start_tournament.default_permissions = discord.Permissions(permissions=0)

        @self.tree.command(name="start_tournament_round", description="Start tournament's next round")
        @discord.app_commands.describe(
            tournament_name="Name of the tournament",
            active_until="Date until which matches are accepted in the isoformat. Ex: 2021-07-27T16:02:08.070557")
        async def start_tournament_round(interaction, tournament_name: str, active_until: str):
            await self._start_tournament_round(interaction, tournament_name, active_until)
        start_tournament_round.default_permissions = discord.Permissions(permissions=0)

        @self.tree.command(name="join_tournament",
                           description="Join currently active tournament with specified account")
        @discord.app_commands.describe(
            username="The username to add as participant",
            required_matches_per_duel="Total valid matches that are needed to proceed in tournament")
        async def join_tournament(interaction, username: str, required_matches_per_duel: int):
            await self._join_tournament(interaction, username)

        @self.tree.command(name="leave_tournament",
                           description="Leave currently active tournament with specified account")
        @discord.app_commands.describe(username="The username to remove as participant")
        async def leave_tournament(interaction, username: str):
            await self._leave_tournament(interaction, username)

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
            discord_user_id=str(interaction.user.id),
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
            discord_user_id=str(interaction.user.id),
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
        user_account_list = await self.connector.get_users_by_discord_id(str(interaction.user.id))
        user_accounts = {user.username: user for user in user_account_list}

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
            discord_user_id=str(discord_user_id))
        if not allowed_to_register:
            return (False, error_message)

        return (True, "")

    async def _send_user_notification(self, message: str) -> None:
        # Send a message to the user notifications channel
        if not self.user_notifications_channel_id:
            return

        channel = self.client.get_channel(int(self.user_notifications_channel_id))
        allowed_channels = (discord.VoiceChannel, discord.StageChannel, discord.TextChannel, discord.Thread)
        if isinstance(channel, allowed_channels):
            log.debug(f"Sending user notification: {repr(message)}")
            await channel.send(message)
        else:
            log.warning(
                'User notifications channel not found or not accepting messages: ' +
                self.user_notifications_channel_id)

    async def _create_tournament(self, interaction, tournament_name: str, tournament_msg_dc_id: str,
                                 required_matches_per_duel: int) -> None:
        """
            Creates an empty tournament tied to specific owner and registration message.
            The message can be used for interactions registration, but is not at the moment.

            The command may fail if the tournament_name is already in use.
        """
        result = await self.connector.create_tournament(tournament_name, interaction.user.id,
                                                        tournament_msg_dc_id, required_matches_per_duel)
        if not result:
            await interaction.response.send_message(
                "Tournament creation failed. Ensure that the tournament name is unique.",
                ephemeral=True)
            return
        else:
            await interaction.response.send_message(
                f"Tournament created. ID: {result}",
                ephemeral=True)
        # TODO should we send tournament_created notification?

    async def _join_tournament(self, interaction, username: str) -> None:
        """
            Allows discord user with a valid QR account to join the tournament (if it did not already start).
            The username is Quadradius account username, since one Discord user may have many QR usernames.

            The command may fail if the tournamend_name is invalid,
            the username does not belong to the callee (or is banned/invalid),
            if it was already registered, or the tournament has already began.
        """
        user = await self.connector.get_user_by_username(username)
        # TODO include bans here as well
        if not user or user.discord_user_id != interaction.user.id:  # Do not disclose whether account exists or not
            await interaction.response.send_message(
                "Failed to authorize the user account - The username is invalid (incorrect or banned)",
                ephemeral=True)
            return

        tournaments = await self.connector.list_tournaments()
        active_tournament = None
        for tournament in tournaments:
            if not tournament.started_at:
                active_tournament = active_tournament

        if not active_tournament:
            await interaction.response.send_message(
                "No tournaments are currently accepting registration",
                ephemeral=True)
            return

        result = await self.connector.add_participant(tournament_id=active_tournament.tournament_id,
                                                      user_id=user.user_id)
        if not result:
            await interaction.response.send_message(
                "Failed to join the tournament - Already Joined",
                ephemeral=True)
            return
        await interaction.response.send_message(
                f"Joined the tournament: {active_tournament.name}. Await the tournament start.",
                ephemeral=True)

    async def _leave_tournament(self, interaction, username: str) -> None:
        """
            Allows discord user with a valid QR account to leave the tournament (if it did not already start).
            The username is Quadradius account username, since one Discord user may have many QR usernames.

            The command may fail if the tournamend_name is invalid, the username does not belong to the callee (or is banned/invalid),
            if it was not registered, or the tournament has already began.
        """
        user = await self.connector.get_user_by_username(username)
        # TODO include bans here as well
        if not user or user.discord_user_id != interaction.user.id:  # Do not disclose whether account exists or not
            await interaction.response.send_message(
                "Failed to authorize the user account - The username is invalid (incorrect or banned)",
                ephemeral=True)
            return

        tournaments = await self.connector.list_tournaments()
        active_tournament = None
        for tournament in tournaments:
            if not tournament.started_at:
                active_tournament = active_tournament

        if not active_tournament:
            await interaction.response.send_message(
                "There are no tournaments which you could leave right now",
                ephemeral=True)
            return

        result = await self.connector.remove_participant(tournament_id=active_tournament.tournament_id,
                                                         user_id=user.user_id)
        if not result:
            await interaction.response.send_message(
                "Failed to leave the tournament - Already not present",
                ephemeral=True)
            return
        await interaction.response.send_message(
                f"Left the tournament: {active_tournament.name}.",
                ephemeral=True)

    async def _start_tournament(self, interaction, tournament_name: str, active_until: str) -> None:
        """
            Allows the creator of the tournament to start it.
            The creator still needs to start round to create random duels between the participants.
            After the tournament is started no changes in participants are allowed.
        """
        try:
            active_until = datetime.fromisoformat(active_until)
        except ValueError as e:
            await interaction.response.send_message(
                f"Failed to start the tournament - active_until date could not be parsed: {e}",
                ephemeral=True)
            return
        
        tournament = await self.connector.get_tournament_by_name(tournament_name)
        if not tournament or tournament.created_by_dc_id != interaction.user.id:
            await interaction.response.send_message(
                "Failed to start the tournament - tournament with given ID is not valid for given user",
                ephemeral=True)
            return

        result = await self.connector.start_tournament(tournament_id=tournament.tournament_id)
        if not result:
            await interaction.response.send_message(
                "Failed to start the tournament - Already started",
                ephemeral=True)
            return

        # Generate the initial pairings        
        tournament_participants = await self.connector.list_participants(tournament.tournament_id)
        shuffle(tournament_participants)
        participant_pairs = utils.pairwise(tournament_participants)
        
        # Generate empty duels
        indexer = FullBinaryTreeIndexer(len(tournament_participants))
        for i in range(indexer.get_node_count()):
            await self.connector.add_duel(tournament.tournament_id, i, active_until=None, user1_id=None, user2_id=None)
        
        # Populate the duels
        await self._start_round_from_participants(tournament.tournament_id, indexer.levels, participant_pairs, active_until,
            tournament.required_matches_per_duel)
        
        await interaction.response.send_message(
            "Tournament was successfully started",
            ephemeral=True)

    async def _start_tournament_round(self, interaction, tournament_name: str, active_until: str) -> None:
        """
            After the tournament is started, initially the first round of duels is pre-generated.
            This command allows the owner (or admins) to start the next round with the given deadline.

            This command **will close any pending rounds and start a new one**,
            even if the previous round is still pending.
            The unfinished duels will be ignored.
        """
        try:
            active_until = datetime.fromisoformat(active_until)
        except ValueError as e:
            await interaction.response.send_message(
                f"Failed to start the round - active_until date could not be parsed: {e}",
                ephemeral=True)
            return
    
        tournament = await self.connector.get_tournament_by_name(tournament_name)
        if not tournament or tournament.created_by_dc_id != interaction.user.id:
            await interaction.response.send_message(
                "Failed to start the round - tournament with given ID is not valid for given user",
                ephemeral=True)
            return
        
        tournament_participants_count = len(await self.connector.list_participants(tournament.tournament_id))
        
        indexer = FullBinaryTreeIndexer(tournament_participants_count)
        
        first_nodes = [nodes[0] for level in range(indexer.levels) for nodes in indexer[level]]

        # Get all existing duels - they are filled from lower to higher idx

        # Figure out their level (keep in mind that some may have been empty!) -
        #  for example get participants, and compare first node idx from each level with the ones in db
        #  if active_until is set, that level was active
        duels = await self.connector.list_duels(tournament.tournament_id)
        current_level_nodes = []
        for idx, node_idx in enumerate(first_nodes):
            if duels[node_idx].active_until is not None:
                current_level_nodes = indexer.get_nodes_at_level(idx)

        # Get the winners from each duel (if someone had None as opponent, then they advance for free)
        # TODO

        # Generate new duels (update the next level)
        for idx, participants in enumerate(participant_pairs):
            participant1 = participants[0]
            participant2 = participants[1]
            await self.connector.update_duel(
                tournament.tournament_id, initial_duels[idx], active_until, participant1.user_id, participant2.user_id)
                # TODO (if we want to) we can DM users to let them know that the round has began, who is their opponent
                # (probably in-game username + discord id or smth) and how much time they have to play how many matches
                # ex:
                # user = await bot.fetch_user(user_id) # get user via user_id, and then their discord user id and use it here
                # await user.send("hello")
        
        await interaction.response.send_message(
            "Tournament was successfully started",
            ephemeral=True)
        
        # Older comments 1:
        # This command assumes that the previous round has ended, if it did not, it will fail.
        # If it succeeded, then new pairings (duels) will be generated by it and broadcasted to players.

        # TODO:
        # assuming the tree goes left -> right:
        # get all winners from the order left -> right (or replace them with None if no winner)
        #
        # If the player from new bracket got non-None opponent, notify that they need to play with them to advance
        # otherwise tell them that they got a free pass to next round
        # (their opponent was None - no matches, no valid matches etc. tldr opponent did not qualify to advance)

        # Get tournament participants (list[DbUser])
        # tournament_participants = await self.connector.list_tournament_users(tournament.tournament_id)
        # ...
        # Shuffle the list
        # ...
        # Create the duels
        # ...
        # if someone has no pair, notify them that they got lucky and they got a free pass
        # notify everyone else who is their opponent and how much time they have

        pass

    async def _start_round_from_participants(self, tournament_id: str, level:int, new_participant_pairs: list,
        active_until: datetime, required_matches_per_duel: int) -> None:
        """
            Populates given level of tournament duels tree using the provided participant pairs list.
            Does not re-order the participants in any way, inserts them from lower tree index to higher in the provided order.
        """
        tournament_participants_count = len(await self.connector.list_participants(tournament_id))
        
        indexer = FullBinaryTreeIndexer(tournament_participants_count)
        
        # Fill out the duels
        duels_to_update = indexer.get_nodes_at_level(level - 1)
        for idx, participants in enumerate(new_participant_pairs):
            participant1 = participants[0]
            participant2 = participants[1]
            await self.connector.update_duel(
                tournament_id, duels_to_update[idx], active_until, participant1.user_id, participant2.user_id)
            
            # Notify users about new duel
            user1 = await self.connector.get_user(participant1.user_id)
            user2 = await self.connector.get_user(participant2.user_id)

            try:
                dc_user1 = await self.client.fetch_user(user1.discord_user_id)
                await dc_user1.send(
                    "### Tournament Duel"
                    "- You have new duel!"
                    f"- Your opponent is: <@{user2.discord_user_id}>"
                    f"- Valid matches required: **{required_matches_per_duel}"
                    f"- Deadline: **{active_until}**"
                )
            except Exception as e:
                log.warning(f'Failed to send duel notification for user "{user1.username}". Error: {e}')

            try:
                dc_user2 = await self.client.fetch_user(user2.discord_user_id)
                await dc_user2.send(
                    "### Tournament Duel"
                    "- You have new duel!"
                    f"- Your opponent is: <@{user1.discord_user_id}>"
                    f"- Valid matches required: **{required_matches_per_duel}"
                    f"- Deadline: **{active_until}**"
                )
            except Exception as e:
                log.warning(f'Failed to send duel notification for "{user2.username}". Error: {e}')