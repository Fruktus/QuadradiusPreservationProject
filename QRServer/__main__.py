import argparse
import os

import logging
from multiprocessing import Process

from QRServer import config
from QRServer.game.game import game_listener
from QRServer.lobby.lobby import lobby_listener

log = logging.getLogger('main')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--bind', help='address to bind', default='127.0.0.1')
    parser.add_argument('-p', '--lobby-port', type=int, help='lobby port', default=3000)
    parser.add_argument('-q', '--game-port', type=int, help='game port', default=3001)
    parser.add_argument('-v', '--verbose', action='store_true', help='log debug messages', default=False)
    parser.add_argument('-l', '--long', action='store_true', help='enable long log format', default=False)
    parser.add_argument(
        '--data',
        default='data',
        help='directory to store data')
    parser.add_argument(
        '--disable-auth',
        action='store_true',
        default=False,
        help='disable authentication, allow any password')
    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    if args.long:
        log_formatter = logging.Formatter(
            '{asctime} {threadName:10} [{name:24}] {levelname:7} {message}',
            style='{')
    else:
        log_formatter = logging.Formatter(
            '[{asctime}.{msecs:3.0f}] {levelname} {message}',
            style='{',
            datefmt='%H:%M:%S')

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    ch = logging.StreamHandler()
    ch.setLevel(log_level)
    ch.setFormatter(log_formatter)
    root_logger.addHandler(ch)

    data_dir = args.data
    os.makedirs(data_dir, exist_ok=True)
    config.data_dir = data_dir
    config.auth_enabled = not args.disable_auth

    log.info('Quadradius server starting')

    lobby_process = Process(target=lobby_listener, args=(args.bind, args.lobby_port))
    lobby_process.start()

    game_process = Process(target=game_listener, args=(args.bind, args.game_port))
    game_process.start()

    try:
        lobby_process.join()
        game_process.join()
    except KeyboardInterrupt:
        log.info('Server stopping, bye')


if __name__ == '__main__':
    main()
