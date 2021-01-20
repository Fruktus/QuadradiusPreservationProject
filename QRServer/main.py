from multiprocessing import Process

from QRServer.lobby.lobby import lobby_listener
from QRServer.game.game import game_listener
from config import Config
from QRServer import lg


if __name__ == '__main__':
    lg.info('Quadradius server starting')
    # TODO handle sigint
    lobby_process = Process(target=lobby_listener, args=(Config.HOST, Config.LOBBY_PORT,))
    lobby_process.start()

    game_process = Process(target=game_listener, args=(Config.HOST, Config.GAME_PORT))
    game_process.start()

    try:
        lobby_process.join()
        game_process.join()
    except KeyboardInterrupt:
        lg.info('Server stopping, bye')
