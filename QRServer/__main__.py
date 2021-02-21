import argparse
import logging
import sys
import time
from threading import Thread

from QRServer import config, config_handlers
from QRServer.cli import QRCmd
from QRServer.game.game import game_listener
from QRServer.lobby.lobby import lobby_listener

log = logging.getLogger('main')


def main():
    config_handlers.refresh_logger_configuration()
    parser = argparse.ArgumentParser()
    config.setup_argparse(parser)
    args = parser.parse_args()
    config.load_from_args(args)

    log.info('Quadradius server starting')

    address = config.address.get()
    game_port = config.game_port.get()
    lobby_port = config.lobby_port.get()

    game_thread = Thread(target=game_listener, args=(address, game_port), daemon=True)
    game_thread.start()

    lobby_thread = Thread(target=lobby_listener, args=(address, lobby_port), daemon=True)
    lobby_thread.start()

    try:
        if sys.stdout.isatty():
            cmd = QRCmd()
            cmd.cmdloop_with_interrupt()
        else:
            while True:
                time.sleep(1000)
    except (KeyboardInterrupt, EOFError):
        log.info('Terminating...')

    log.info('Server stopping, bye')


if __name__ == '__main__':
    main()
