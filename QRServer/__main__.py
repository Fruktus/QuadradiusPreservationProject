import argparse
import logging
from multiprocessing import Process

from QRServer.game.game import game_listener
from QRServer.lobby.lobby import lobby_listener

log = logging.getLogger('main')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--bind', help='address to bind', default='127.0.0.1')
    parser.add_argument('-p', '--lobby-port', type=int, help='lobby port', default=3000)
    parser.add_argument('-q', '--game-port', type=int, help='game port', default=3001)
    parser.add_argument('-v', '--verbose', action='store_true', help='log debug messages', default=False)
    args = parser.parse_args()

    logging.getLogger().setLevel(logging.DEBUG if args.verbose else logging.INFO)

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
