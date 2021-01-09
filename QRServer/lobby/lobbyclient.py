from queue import Queue

from QRServer import lg
from QRServer.dbconnector import DBConnector


class LobbyClient:
    def __init__(self, client_socket, lobby_server):
        self.cs = client_socket
        self.lobby_server = lobby_server
        self.in_queue = Queue()  # owner only reads, others only write

        self.username = ''
        self.communique = ' '
        self.score = 0
        self.awards = [0] * 10

        # TODO set socket timeout!

        self._run()

    def get_queue(self):
        return self.in_queue

    def get_repr(self):
        return '~' + self.username + '~' + self.communique + '~' + str(self.score) + '~' +\
               '~'.join([str(x) for x in self.awards])

    @staticmethod
    def get_empty_repr():
        return '~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0'

    def _run(self):
        cases = {b'<QR_L>': self.case_QRL,
                 b'<L>': self.case_L,
                 b'<S>': self.case_S,
                 b'<SERVER>': self.case_SERVER}  # TODO add default handler if no key found

        while True:  # TODO need check for pipe broken :D -> if recv = '' then consider pipe closed
            data = self.cs.recv(2048)
            if not data:
                lg.debug('Connection closed by client')
                break
            lg.debug(data)

            data = data.split(b'\x00')[:-1]  # FIXME technically may fail if not done reading from socket

            for p in data:  # TODO rewrite it as a proper loop with the stages needed for auth
                values = p.split(b'~')

                cases[values[0]](values)
        # accept <QR_L>

        # check swf version
        # check login data -> authenticate or deny
        # enter loop:
        #   wait for requests, reply appropriately

    def case_QRL(self, values):
        lg.debug('SWF Version: ' + str(values[1]))
        if values[1] != b'5':
            self.cs.send(b'<S><SERVER><OLD_SWF>')
            lg.warning('Client with low version connected, version: ' + str(values[1]))
            # TODO close connection i think

    def case_L(self, values):
        if not DBConnector().user_exists(values[1], values[2]):  # FIXME this is VERY temporary
            self.cs.send(b'<L><BAD_MEMBER>')
            # TODO possibly break connection or at least prevent from proceeding
        # elif values[1] in lobby:
        #   self.cs.send(b'<L><DUPLICATE>')
        else:
            # user authenticated successfully, register yourself with lobbyserver
            # TODO send formatted lobby string etc.
            lg.debug('sending test string')
            test_string = b'<L>~DBG~ comm test~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0\x00'
            self.cs.send(test_string)

    def case_S(self, values):
        pass

    def case_SERVER(self, values):
        if values[1] == b'<ALIVE?>':
            self.cs.send(b'<S>~<SERVER>~<ALIVE>\x00')
