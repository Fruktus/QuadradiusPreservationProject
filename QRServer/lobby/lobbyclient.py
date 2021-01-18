from queue import Queue
from threading import Thread
from time import time

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

        self.idx = None
        self.joined_at = None

        # TODO set socket timeout!

        self._reader_thread = Thread(target=self._socket_reader, daemon=True)
        self._reader_thread.start()
        self._run()

    def get_queue(self):
        return self.in_queue

    def get_repr(self):
        return '~' + self.username + '~' + self.communique + '~' + str(self.score) + '~' +\
               '~'.join([str(x) for x in self.awards])

    @staticmethod
    def get_empty_repr():
        return '~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0'

    def _socket_reader(self):
        data = b''
        while True:
            data += self.cs.recv(2048)
            if not data:
                lg.debug('Connection closed by client')
                self.in_queue.put(b'<DICONNECTED>')
                break
            if data[-1] == 0:  # idk why b'\x00' does not work
                data = data.split(b'\x00')[:-1]  # FIXME technically may fail if not done reading from socket
                for i in data:
                    self.in_queue.put(i)
                data = b''

    def _run(self):
        cases = {b'<QR_L>': self.case_QRL,
                 b'<L>': self.case_L,
                 b'<S>': self.case_S,
                 b'<SERVER>': self.case_SERVER,
                 b'<DISCONNECTED>': self.case_DISCONNECTED}  # TODO add default handler if no key found,

        while True:  # TODO need check for pipe broken :D -> if recv = '' then consider pipe closed

            data = self.in_queue.get(block=True)
            lg.debug(data)
            values = data.split(b'~')

            cases[values[0]](values)
        # accept <QR_L>

        # check swf version
        # check login data -> authenticate or deny
        # enter loop:
        #   wait for requests, reply appropriately

    def send_data(self, data):
        self.cs.send(data)

    def case_QRL(self, values):
        lg.debug('SWF Version: ' + str(values[1]))
        if values[1] != b'5':
            self.cs.send(b'<S><SERVER><OLD_SWF>')
            lg.warning('Client with low version connected, version: ' + str(values[1]))
            # TODO close connection i Sthink

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
            self.username = values[1].decode('utf8')
            self.idx = self.lobby_server.add_client(self)
            self.joined_at = time()

            # test_string = b'<L>~DBG~ comm test~12~88~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0\x00'
            test_string = self.lobby_server.get_clients_string()
            self.cs.send(test_string)

    def case_S(self, values):
        lg.debug('challenge issued')
        self.lobby_server.challenge_user(int(values[1].decode('utf8')), int(values[2].decode('utf8')))

    def case_SERVER(self, values):
        if values[1] == b'<ALIVE?>':
            self.cs.send(b'<S>~<SERVER>~<ALIVE>\x00')
        if values[1] == b'<RECENT>':
            self.cs.send(b'<S>~<SERVER>~<LAST_LOGGED>~DBGX~999~\x00')
            self.cs.send(b'<S>~<SERVER>~<LAST_PLAYED>~imt beat sifl#7-0#13:38~imt beat sifl#12-9#07:19~sifl beat imt#3-0#11:46~imt beat dan ddm#15-0#14:49~sifl beat imt#4-1#10:04~dan ddm beat sifl#13-0#10:41~sifl beat imt#12-6#13:54~sifl beat imt#19-0#09:26~slug800 beat imt#14-3#11:52~imt beat slug800#19-2#12:06~sifl beat imt#13-6#13:08~sifl beat imt#9-3#13:21~sifl beat imt#5-1#09:18~sifl beat imt#19-14#09:22~sifl beat hoyvinmayvin#20-5#13:28\x00')
            self.cs.send(b'<S>~<SERVER>~<RANKING(thisMonth)>~sifl~1~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0\x00')

    def case_DISCONNECTED(self, values):
        # if client was added to lobby, remove
        # stop the thread
        # TODO
        pass
