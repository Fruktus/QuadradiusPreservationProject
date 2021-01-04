import socket
from threading import Thread
# TODO
# create class for handling client sockets, something for sending, receiving etc
# create loop1 for server socket that will accept incoming connections (to lobby)
# create separate loop2 (in another thread or proces, idc) that will handle the matches themselves
# use locks to synchronize access to shared variables

# TODO
# what server needs to store:
# list of people in lobby right now
# list of people who were online recently (like last one or smth)
# ranking for the month(s), retrieved by client based on date


def conn_listener(conn_host, conn_port, client_func):
    gm_s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    gm_s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    gm_s.bind((conn_host, conn_port))
    gm_s.listen(5)

    while True:
        (clientsocket, address) = gm_s.accept()
        ct = Thread(target=client_func, args=(clientsocket,))
        ct.run()


if __name__ == '__main__':
    lobby_thread = Thread(target=conn_listener, args=('localhost', 3000, lobby_handler,))
    lobby_thread.start()

    game_thread = Thread(target=conn_listener, args=('localhost', 3001, game_handler))
    game_thread.start()

    lobby_thread.join()
    game_thread.join()
