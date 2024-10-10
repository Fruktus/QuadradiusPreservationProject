import logging
import re

from QRServer.common import utils
import discord

log = logging.getLogger('qr.bot')


class DiscordBot:
    def __init__(self, config, connector):
        self.config = config
        self.connector = connector
        self.max_aliases = self.config.discord_bot_max_aliases.get()
        self.token = self.config.discord_bot_token.get()
        self.username_regex = re.compile(r'^\w+[\w\s]*$')

        if not self.token:
            log.warning('Discord bot token is not set. Bot will not be started.')
            return

        intents = discord.Intents.default()
        intents.messages = True  # Listen to messages in general (includes DMs)
        intents.message_content = True  # Enable reading message content

        self.client = discord.Client(intents=intents)
        self.tree = discord.app_commands.CommandTree(self.client)

    async def run_bot(self):
        if not self.token:
            log.warning('Discord bot token is not set. Bot will not be started.')
            return

        @self.tree.command(
            name="register",
            description="Register a new member",
        )
        async def register(interaction):
            log.debug(f"Register command received from {interaction.user}")

            await interaction.response.send_message(
                "Hi! Please type the username that you wish to register."
                " It should be under 10 characters."
                f" You can only register {self.max_aliases} username{'s' if self.max_aliases > 1 else ''}."
                " If the username is available, you will receive a temporary password, which you should change."
                " By registering, you agree that your discord's user_id will be stored for verification purposes."
                " If you wish to close the account, please contact the admin."
            )

        @self.client.event
        async def on_ready():
            await self.client.change_presence(
                activity=discord.Activity(
                    type=discord.ActivityType.watching, name="Observing QR battles"
                )
            )
            await self.tree.sync()
            log.info("Discord bot is ready")

        # Event listener for messages
        @self.client.event
        async def on_message(message):
            # Ignore the bot's own messages
            if message.user == self.client.user:
                return

            log.debug(f"Message received from {message.author}: {message.content}")

            # check if the client can register new username, otherwise send error with notif
            user_accounts = self.connector.get_users_by_discord_id(message.author.id)
            if len(user_accounts) >= self.max_aliases:
                await message.channel.send(f"You have reached the maximum number of aliases ({self.max_aliases}).")
                return

            # check if content matches reges
            username = message.content.strip()
            if not self.username_regex.match(username) or len(username) > 10:
                await message.channel.send("Username should be no more than 10 characters.")
                return

            # check if the username is available
            if self.connector.get_user_by_username(message.content):
                await message.channel.send("Username is taken.")
                return

            # if it is register the user and send temp password
            log.debug(f"Registering user {message.author.id} with username {message.content}")
            self.connector.authenticate_user(
                username=username,
                password=utils.generate_random_password(10).encode(),
                auto_create=True,
                verify_password=True,
            )

        log.debug('Starting discord bot')
        await self.client.start(self.token)
