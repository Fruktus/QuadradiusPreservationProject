import sys
from argparse import ArgumentParser
from dataclasses import dataclass, field
from typing import Any, Callable

import toml

from QRServer import config_handlers


@dataclass
class ConfigKey:
    config: 'Config'
    name: str
    description: str
    default_value: object
    cli_args: list[str] = field(default_factory=list)
    onchange: Callable[['Config'], None] | None = None

    def get(self):
        return self.config.get(self.name)

    def get_type(self):
        return type(self.default_value)


class Config:
    def __init__(self):
        self._data = {}

        self.address = ConfigKey(
            config=self,
            name='address',
            cli_args=['-b', '--bind'],
            description='address to bind',
            default_value='127.0.0.1')
        self.lobby_port = ConfigKey(
            config=self,
            name='port.lobby',
            cli_args=['-p', '--lobby-port'],
            description='port used for lobby',
            default_value=3000)
        self.game_port = ConfigKey(
            config=self,
            name='port.game',
            cli_args=['-q', '--game-port'],
            description='port used for playing the game',
            default_value=3001)
        self.data_dir = ConfigKey(
            config=self,
            name='data.dir',
            cli_args=['--data'],
            description='directory to store data',
            default_value='data',
            onchange=config_handlers.create_data_dir)

        self.log_long = ConfigKey(
            config=self,
            name='log.long',
            cli_args=['-l', '--long'],
            description='enable long log format',
            default_value=False,
            onchange=config_handlers.refresh_logger_configuration)
        self.log_verbose = ConfigKey(
            config=self,
            name='log.verbose',
            cli_args=['-v', '--verbose'],
            description='log debug messages',
            default_value=False,
            onchange=config_handlers.refresh_logger_configuration)
        self.log_cron_delay = ConfigKey(
            config=self,
            name='log.cron_delay',
            cli_args=[],
            description='enable periodic state logging and set the delay in seconds (set to 0 to disable)',
            default_value=5 * 60)
        self.auth_disable = ConfigKey(
            config=self,
            name='auth.disable',
            cli_args=['--disable-auth'],
            description='disable authentication, allow any password',
            default_value=False)
        self.auto_register = ConfigKey(
            config=self,
            name='auth.auto_register',
            cli_args=['--auto-register'],
            description='automatically register a user upon first login attempt',
            default_value=False)
        self.leaderboards_ranked_only = ConfigKey(
            config=self,
            name='leaderboards.ranked_only',
            cli_args=[],
            description='whether to only show ranked games on leaderboards',
            default_value=True)
        self.leaderboards_include_void = ConfigKey(
            config=self,
            name='leaderboards.include_void',
            cli_args=[],
            description='whether to include void games on leaderboards',
            default_value=False)
        self.lobby_motd = ConfigKey(
            config=self,
            name='lobby.motd',
            cli_args=[],
            description='welcome message sent after joining the lobby',
            default_value='')

        self.discord_webhook_lobby_joined_url = ConfigKey(
            config=self,
            name='discord.webhook.lobby_joined.url',
            cli_args=[],
            description='',
            default_value='')
        self.discord_webhook_lobby_left_url = ConfigKey(
            config=self,
            name='discord.webhook.lobby_left.url',
            cli_args=[],
            description='',
            default_value='')
        self.discord_webhook_lobby_set_comment_url = ConfigKey(
            config=self,
            name='discord.webhook.lobby_set_comment.url',
            cli_args=[],
            description='',
            default_value='')
        self.discord_webhook_lobby_message_url = ConfigKey(
            config=self,
            name='discord.webhook.lobby_message.url',
            cli_args=[],
            description='',
            default_value='')
        self.discord_webhook_game_started_url = ConfigKey(
            config=self,
            name='discord.webhook.game_started.url',
            cli_args=[],
            description='',
            default_value='')
        self.discord_webhook_game_ended_url = ConfigKey(
            config=self,
            name='discord.webhook.game_ended.url',
            cli_args=[],
            description='',
            default_value='')
        self.discord_webhook_logger_url = ConfigKey(
            config=self,
            name='discord.webhook.logger.url',
            cli_args=[],
            description='',
            default_value='',
            onchange=config_handlers.refresh_logger_configuration)
        self.discord_webhook_logger_level = ConfigKey(
            config=self,
            name='discord.webhook.logger.level',
            cli_args=[],
            description='',
            default_value='INFO',
            onchange=config_handlers.refresh_logger_configuration)
        self.discord_webhook_logger_flush_delay_s = ConfigKey(
            config=self,
            name='discord.webhook.logger.flush_delay_s',
            cli_args=[],
            description='',
            default_value=5,
            onchange=config_handlers.refresh_logger_configuration)
        self.discord_bot_enabled = ConfigKey(
            config=self,
            name='discord.bot.enabled',
            cli_args=[],
            description='Whether to enable the discord bot.'
                        ' Requires discord.bot.token and discord.bot.guild_id to be set.',
            default_value=False)
        self.discord_bot_token = ConfigKey(
            config=self,
            name='discord.bot.token',
            cli_args=[],
            description='Discord bot token. See https://discordpy.readthedocs.io/en/stable/discord.html for tutorial',
            default_value='')
        self.guild_id = ConfigKey(
            config=self,
            name='discord.bot.guild_id',
            cli_args=[],
            description='ID of the server where the bot is allowed to operate. Bot will ignore other interactions.',
            default_value='')
        self.discord_bot_channel_user_notifications_id = ConfigKey(
            config=self,
            name='discord.bot.channel_user_notifications.id',
            cli_args=[],
            description='Discord Channel ID for user notifications such as registration, claiming of account or bans',
            default_value='')
        self.discord_bot_max_aliases = ConfigKey(
            config=self,
            name='discord.bot.max_aliases',
            cli_args=[],
            description='Maximum number of aliases per user',
            default_value=1)

    def get_key(self, name: str):
        by_name = self.keys_by_name()
        if name not in by_name:
            raise Exception(f'Config not found: {name}')
        return by_name[name]

    def get(self, name: str):
        key = self.get_key(name)
        name_parts = name.split('.')
        conf = self._data
        while name_parts:
            k = name_parts[0]
            if k not in conf:
                return key.default_value
            conf = conf[k]
            name_parts = name_parts[1:]
        if conf is None:
            return key.default_value
        return conf

    def set(self, name: str, value: str | int):
        key = self.get_key(name)
        value_type = key.get_type()

        if value is None:
            pass
        elif value_type == bool:
            if value in ['true', 'True', 'Y', 'T', True]:
                value = True
            elif value in ['false', 'False', 'N', 'F', False]:
                value = False
            else:
                raise Exception(f'Invalid value: {value}')
        elif value_type == int:
            value = int(value)
        elif value_type == str:
            value = str(value)
        else:
            raise Exception(f'Unsupported config type: {value_type}')

        name_parts = name.split('.')
        conf = self._data
        while len(name_parts) > 1:
            k = name_parts[0]
            if k not in conf:
                conf[k] = {}
            conf = conf[k]
            name_parts = name_parts[1:]
        k = name_parts[0]

        if value is None and k in conf:
            del conf[k]
        else:
            conf[k] = value

        if key.onchange is not None:
            key.onchange(self)

    def all_keys(self) -> list[ConfigKey]:
        keys = self.keys_by_name().values()
        return sorted(keys, key=lambda k: k.name)

    def keys_by_name(self) -> dict[str, ConfigKey]:
        keys = {}
        for name, value in vars(self).items():
            if isinstance(value, ConfigKey):
                keys[value.name] = value
        return keys

    def setup_argparse(self, parser: ArgumentParser):
        parser.add_argument(
            '-c', '--config',
            help='load config from toml file',
            default=None, dest='__config')
        for key in self.all_keys():
            value_type = key.get_type()

            kwargs: dict[Any, Any] = {}
            if value_type == bool:
                kwargs['action'] = 'store_true'
            elif value_type == int:
                kwargs['type'] = int
            elif value_type == str:
                kwargs['type'] = str
            else:
                raise Exception(f'Unsupported config type: {value_type}')

            if len(key.cli_args) > 0:
                parser.add_argument(
                    *key.cli_args,
                    help=key.description,
                    default=None,
                    dest=key.name,
                    **kwargs)

    def load_from_args(self, args):
        args = vars(args)
        if '__config' in args and args['__config']:
            conf = args['__config']
            print(f'Loading config from file: {conf}', file=sys.stderr)
            self.load_from_toml(conf)
        for key in self.all_keys():
            if key.name in args and args[key.name]:
                self.set(key.name, args[key.name])

    def __load_dict(self, d, prefix: str):
        for key, value in d.items():
            if isinstance(value, dict):
                self.__load_dict(value, prefix + key + '.')
            else:
                self.set(prefix + key, value)

    def load_from_toml(self, file):
        d = toml.load(file)
        self.__load_dict(d, '')
