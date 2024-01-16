import logging
import socket
from threading import Thread

from QRServer.lobby.lobbyclient import LobbyClientHandler
from QRServer.lobby.lobbyserver import LobbyServer

log = logging.getLogger('lobby_listener')


def lobby_listener(conn_host, conn_port):
    log.info('Lobby starting on ' + conn_host + ':' + str(conn_port))
    lm_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lm_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    lm_s.bind((conn_host, conn_port))
    lm_s.listen(5)
    log.info('Lobby started on ' + conn_host + ':' + str(conn_port))

    ls = LobbyServer()
    try:
        while True:
            (client_socket, address) = lm_s.accept()
            client = LobbyClientHandler(client_socket, ls)
            ct = Thread(target=client.run, daemon=True)
            ct.start()
    except KeyboardInterrupt:
        lm_s.shutdown(1)
        lm_s.close()
