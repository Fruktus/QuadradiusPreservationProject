import socket
from threading import Thread

from QRServer.lobby import lg
from QRServer.lobby.lobbyclient import LobbyClient
from QRServer.lobby.lobbyserver import LobbyServer


def lobby_listener(conn_host, conn_port):
    lg.info('Lobby starting on ' + conn_host + ':' + str(conn_port))
    lm_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    lm_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    lm_s.bind((conn_host, conn_port))
    lm_s.listen(5)

    ls = LobbyServer()
    try:
        while True:
            (clientsocket, address) = lm_s.accept()
            ct = Thread(target=LobbyClient, args=(clientsocket, ls, ), daemon=True)
            ct.start()
    except KeyboardInterrupt:
        lm_s.shutdown(1)
        lm_s.close()
