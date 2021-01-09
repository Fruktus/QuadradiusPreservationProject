import socket
from threading import Thread

from QRServer.lobby.lobbyclient import LobbyClient
from QRServer.lobby.lobbyserver import LobbyServer


def lobby_listener(conn_host, conn_port):
    gm_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    gm_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    gm_s.bind((conn_host, conn_port))
    gm_s.listen(5)

    ls = LobbyServer()

    while True:
        (clientsocket, address) = gm_s.accept()
        ct = Thread(target=LobbyClient, args=(clientsocket, ls, ))
        ct.run()
