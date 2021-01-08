from threading import Lock

from QRServer import lg
from QRServer.dbconnector import DBConnector


class LobbyServer:
    def __init__(self):
        self.clients = [None] * 13  # The lobby allows only 13 people at once, last one is kicked
        self.client_lock = Lock()  # TODO check if this will actually work
        pass

    def add_client(self, client_id):
        with self.client_lock:
            pass

    def remove_client(self):
        pass

    def get_clients_string(self):
        pass

    def broadcast_chat(self, sender_id):
        pass

    def invite_to_match(self, sender_id, receiver_id):
        pass


class LobbyClient:
    def __init__(self, client_socket, var_manager):
        self.cs = client_socket
        self.manager = var_manager

        # TODO set socket timeout!

        self._run()

    def _run(self):
        while True:  # TODO need check for pipe broken :D
            data = self.cs.recv(2048)
            if not data:
                lg.debug('Connection closed by client')
                break
            lg.debug(data)

            data = data.split(b'\x00')[:-1]  # FIXME technically may fail if not done reading from socket

            for p in data:  # TODO rewrite it as a proper loop with the stages needed for auth
                values = p.split(b'~')
                if values[0] == b'<QR_L>':
                    lg.debug('SWF Version: ' + str(values[1]))
                    if values[1] != b'5':
                        self.cs.send(b'<S><SERVER><OLD_SWF>')
                        lg.warning('Client with low version connected, version: ' + str(values[1]))
                        # TODO close connection i think
                elif values[0] == b'<L>':
                    if not DBConnector().user_exists(values[1], values[2]):  # FIXME this is VERY temporary
                        self.cs.send(b'<L><BAD_MEMBER>')
                        # TODO possibly break connection or at least prevent from proceeding
                    # elif values[1] in lobby:
                    #   self.cs.send(b'<L><DUPLICATE>')
                    else:
                        # TODO send formatted lobby string etc.
                        lg.debug('sending test string')
                        test_string = b'<L>~DBG~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0\x00'
                        self.cs.send(test_string)
                elif values[0] == b'<Server>':
                    if values[1] == b'<ALIVE?>':
                        self.cs.send(b'<S>~<SERVER>~<ALIVE>\x00')
        # accept <QR_L>

        # check swf version
        # check login data -> authenticate or deny
        # enter loop:
        #   wait for requests, reply appropriately


def login(username, hashed_password):
    pass


def get_present_people():
    pass
