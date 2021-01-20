import socket
from threading import Thread

from QRServer.game import lg
from QRServer.game.gameclient import GameClient


def game_listener(conn_host, conn_port):
    lg.info('Game starting on ' + conn_host + ':' + str(conn_port))
    gm_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    gm_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    gm_s.bind((conn_host, conn_port))
    gm_s.listen(5)

    # ls = LobbyServer()
    try:
        while True:
            lg.debug('waiting for clients')
            (clientsocket, address) = gm_s.accept()
            lg.debug('client connected')
            ct = Thread(target=GameClient, args=(clientsocket, ), daemon=True)
            ct.start()
    except KeyboardInterrupt:
        gm_s.shutdown(1)
        gm_s.close()
