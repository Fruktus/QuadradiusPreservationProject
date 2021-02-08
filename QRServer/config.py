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


def load_toml(file):
    global _config
    _config = toml.load(file)


def get_key(name: str):
    by_name = keys_by_name()
    if name not in by_name:
        raise Exception('Config not found: {}'.format(name))
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
    return conf


def set(name: str, value: object):
    key = get_key(name)
    value_type = key.get_type()

    if value_type == bool:
        if value in ['true', 'True', 'Y', 'T', True]:
            value = True
        elif value in ['false', 'False', 'N', 'F', False]:
            value = False
        else:
            raise Exception('Invalid value: {}'.format(value))
    elif value_type == int:
        value = int(value)
    elif value_type == str:
        value = str(value)
    else:
        raise Exception('Unsupported config type: {}'.format(value_type))

    name_parts = name.split('.')
    conf = _config
    while len(name_parts) > 1:
        k = name_parts[0]
        if k not in conf:
            conf[k] = {}
        conf = conf[k]
        name_parts = name_parts[1:]
    k = name_parts[0]
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
            raise Exception('Unsupported config type: {}'.format(value_type))

        parser.add_argument(
            *key.cli_args,
            help=key.description,
            default=key.default_value,
            dest=key.name,
            **kwargs)


def load_from_args(args, set_dirty=False):
    for key in all_keys():
        set(key.name, vars(args)[key.name])
        if not set_dirty:
            key.dirty = False


def print_help():
    for key in all_keys():
        print('{:20} - {}'.format(key.name, key.description))
