from argparse import ArgumentParser
from dataclasses import dataclass, field
from typing import List, Callable, Dict

import toml

from QRServer import config_handlers


@dataclass
class ConfigKey:
    name: str
    description: str
    default_value: object
    cli_args: List[str] = field(default_factory=list)
    requires_restart: bool = True
    onchange: Callable[[], None] = None
    dirty: bool = False

    def get(self):
        return get(self.name)

    def get_type(self):
        return type(self.default_value)


_config = {}

address = ConfigKey(
    name='address',
    cli_args=['-b', '--bind'],
    description='address to bind',
    default_value='127.0.0.1')
lobby_port = ConfigKey(
    name='port.lobby',
    cli_args=['-p', '--lobby-port'],
    description='port used for lobby',
    default_value=3000)
game_port = ConfigKey(
    name='port.game',
    cli_args=['-q', '--game-port'],
    description='port used for playing the game',
    default_value=3001)
data_dir = ConfigKey(
    name='data.dir',
    cli_args=['--data'],
    description='directory to store data',
    default_value='data',
    onchange=config_handlers.create_data_dir)

log_long = ConfigKey(
    name='log.long',
    cli_args=['-l', '--long'],
    description='enable long log format',
    default_value=False,
    requires_restart=False,
    onchange=config_handlers.refresh_logger_configuration)
log_verbose = ConfigKey(
    name='log.verbose',
    cli_args=['-v', '--verbose'],
    description='log debug messages',
    default_value=False,
    requires_restart=False,
    onchange=config_handlers.refresh_logger_configuration)
auth_disable = ConfigKey(
    name='auth.disable',
    cli_args=['--disable-auth'],
    description='disable authentication, allow any password',
    default_value=False,
    requires_restart=False)
auto_register = ConfigKey(
    name='auth.auto_register',
    cli_args=['--auto-register'],
    description='automatically register a user upon first login attempt',
    default_value=False,
    requires_restart=False)

discord_webhook_lobby_url = ConfigKey(
    name='discord.webhook.lobby.url',
    cli_args=None,
    description='send notifications related to lobby using this Discord webhook',
    default_value='',
    requires_restart=False)


def get_key(name: str):
    by_name = keys_by_name()
    if name not in by_name:
        raise Exception(f'Config not found: {name}')
    return by_name[name]


def get(name: str):
    key = get_key(name)
    name_parts = name.split('.')
    conf = _config
    while name_parts:
        k = name_parts[0]
        if k not in conf:
            return key.default_value
        conf = conf[k]
        name_parts = name_parts[1:]
    if conf is None:
        return key.default_value
    return conf


def set(name: str, value: object):
    key = get_key(name)
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
    conf = _config
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
        key.onchange()
    if key.requires_restart:
        key.dirty = True


def all_keys() -> List[ConfigKey]:
    keys = keys_by_name().values()
    return sorted(keys, key=lambda k: k.name)


def keys_by_name() -> Dict[str, ConfigKey]:
    keys = {}
    for name, value in globals().items():
        if isinstance(value, ConfigKey):
            keys[value.name] = value
    return keys


def setup_argparse(parser: ArgumentParser):
    parser.add_argument(
        '-c', '--config',
        help='load config from toml file',
        default=None, dest='__config')
    for key in all_keys():
        value_type = key.get_type()

        kwargs = {}
        if value_type == bool:
            kwargs['action'] = 'store_true'
        elif value_type == int:
            kwargs['type'] = int
        elif value_type == str:
            kwargs['type'] = str
        else:
            raise Exception(f'Unsupported config type: {value_type}')

        if key.cli_args is not None:
            parser.add_argument(
                *key.cli_args,
                help=key.description,
                default=None,
                dest=key.name,
                **kwargs)


def load_from_args(args, set_dirty=False):
    args = vars(args)
    if '__config' in args and args['__config']:
        conf = args['__config']
        print(f'Loading config from file: {conf}')
        load_from_toml(conf)
    for key in all_keys():
        if key.name in args and args[key.name]:
            set(key.name, args[key.name])
        if not set_dirty:
            key.dirty = False


def __load_dict(d, prefix: str):
    for key, value in d.items():
        if isinstance(value, dict):
            __load_dict(value, prefix + key + '.')
        else:
            set(prefix + key, value)


def load_from_toml(file):
    d = toml.load(file)
    __load_dict(d, '')


def print_help():
    for key in all_keys():
        print(f'{key.name:20} - {key.description}')
