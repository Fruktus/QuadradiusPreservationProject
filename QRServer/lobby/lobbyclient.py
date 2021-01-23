from queue import Queue
from threading import Thread
from time import time

from QRServer.lobby import lg
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
        while self.cs:
            data += self.cs.recv(2048)
            if not data:
                self.in_queue.put(b'<DISCONNECTED>')
                break
            elif data[-1] == 0:  # idk why b'\x00' does not work
                data = data.split(b'\x00')[:-1]
                for i in data:
                    self.in_queue.put(i)
                data = b''

    def _run(self):
        cases = {b'<policy-file-request/>': self._case_policy,
                 b'<QR_L>': self._case_QRL,
                 b'<L>': self._case_L,
                 b'<S>': self._case_S,
                 b'<SERVER>': self._case_SERVER,
                 b'<B>': self._case_B,
                 b'<DISCONNECTED>': self._case_DISCONNECTED}  # TODO add default handler if no key found,

        while self.cs:

            data = self.in_queue.get(block=True)
            lg.debug('<Queue get> ' + str(data))
            values = data.split(b'~')

            cases[values[0]](values)

    def send_data(self, data):
        if self.cs:
            self.cs.send(data)
        else:
            lg.warning('attempt to send using closed socket')

    def _case_policy(self, values):
        lg.debug('policy file requested')
        self.cs.send(b'<cross-domain-policy><allow-access-from domain="*" to-ports="*" /></cross-domain-policy>\x00')

    def _case_QRL(self, values):
        lg.debug('SWF Version: ' + str(values[1]))
        if values[1] != b'5':
            self.cs.send(b'<S><SERVER><OLD_SWF>\x00')
            lg.warning('Client with low version connected, version: ' + str(values[1]))
            self.exit()

    def _case_L(self, values):
        if not DBConnector().user_exists(values[1], values[2]):  # FIXME implement dbconnector
            self.cs.send(b'<L>~<BAD_MEMBER>\x00')
            self.exit()
        elif self.lobby_server.username_exists(values[1].decode('utf8')):
            lg.warning('Client duplicate in lobby: ' + values[1].decode('utf8'))
            self.cs.send(b'<L>~<DUPLICATE>\x00')
            self.exit()  # FIXME it seems that the connection shouldnt be completely closed
        else:
            # user authenticated successfully, register with lobbyserver
            lg.debug('Client joining: ' + values[1].decode('utf8'))
            self.username = values[1].decode('utf8')
            self.idx = self.lobby_server.add_client(self)
            self.joined_at = time()
            self.cs.send(self.lobby_server.get_clients_string())

    def _case_S(self, values):
        if values[3] == b'<SHALLWEPLAYAGAME?>':
            lg.debug('challenge issued')
            self.lobby_server.challenge_user(int(values[1].decode('utf8')), int(values[2].decode('utf8')))
        elif values[3] == b'<AUTHENTICATION>':
            self.lobby_server.setup_challenge(int(values[1].decode('utf8')), int(values[2].decode('utf8')), int(values[4].decode('utf8')))

    def _case_SERVER(self, values):
        if values[1] == b'<ALIVE?>':
            self.cs.send(b'<S>~<SERVER>~<ALIVE>\x00')
        if values[1] == b'<RECENT>':
            self.cs.send(b'<S>~<SERVER>~<LAST_LOGGED>~DBGX~999~\x00')
            self.cs.send(b'<S>~<SERVER>~<LAST_PLAYED>~imt beat sifl#7-0#13:38~imt beat sifl#12-9#07:19~sifl beat imt#3-0#11:46~imt beat dan ddm#15-0#14:49~sifl beat imt#4-1#10:04~dan ddm beat sifl#13-0#10:41~sifl beat imt#12-6#13:54~sifl beat imt#19-0#09:26~slug800 beat imt#14-3#11:52~imt beat slug800#19-2#12:06~sifl beat imt#13-6#13:08~sifl beat imt#9-3#13:21~sifl beat imt#5-1#09:18~sifl beat imt#19-14#09:22~sifl beat hoyvinmayvin#20-5#13:28\x00')
            self.cs.send(b'<S>~<SERVER>~<RANKING(thisMonth)>~sifl~1~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~\x00')

    def _case_B(self, values):
        pass

    def _case_DISCONNECTED(self, values):
        lg.debug('Connection closed by client')
        if self.idx is not None:
            lg.debug('removing client idx: ' + str(self.idx))
            self.lobby_server.remove_client(self.idx)
        # stop the thread
        # TODO
        self.exit()

    def exit(self):
        if self.cs:
            try:
                self.cs.shutdown(1)
            except OSError:
                pass
            self.cs.close()
            self.cs = None
