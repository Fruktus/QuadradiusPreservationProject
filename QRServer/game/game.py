import logging
import socket
from threading import Thread

from QRServer.game.gameclient import GameClientHandler
from QRServer.game.gameserver import GameServer

log = logging.getLogger('game_listener')


def game_listener(conn_host, conn_port):
    log.info('Game starting on ' + conn_host + ':' + str(conn_port))
    gm_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    gm_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    gm_s.bind((conn_host, conn_port))
    gm_s.listen(5)

    gs = GameServer()

    try:
        while True:
            (client_socket, address) = gm_s.accept()
            log.debug('Client connected from {}'.format(address))
            client = GameClientHandler(client_socket, gs)
            ct = Thread(target=client.run, daemon=True)
            ct.start()
    except KeyboardInterrupt:
        gm_s.shutdown(1)
        gm_s.close()
