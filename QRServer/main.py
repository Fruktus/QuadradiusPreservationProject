import socket
from multiprocessing import Process

from QRServer.lobby.lobby import lobby_listener
from config import Config
from QRServer import lg

# TODO
# what server needs to store:
# list of people in lobby right now
# list of people who were online recently (like last one or smth)
# ranking for the month(s), retrieved by client based on date


if __name__ == '__main__':
    lg.info('Server starting')
    lobby_process = Process(target=lobby_listener, args=(Config.HOST, Config.LOBBY_PORT,))
    lobby_process.start()

    # game_process = Process(target=game_listener, args=(Config.HOST, Config.GAME_PORT, game_handler))
    # game_process.start()

    lobby_process.join()
    # game_process.join()
