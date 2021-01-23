from queue import Queue
from threading import Thread

from QRServer.game import lg


class GameClient:
    def __init__(self, client_socket, game_server):
        self.cs = client_socket
        self.in_queue = Queue()
        self.out_socket = None
        self.game_server = game_server

        self.own_username = None
        self.opponent_username = None
        self.own_auth = None
        self.opponent_auth = None
        self.password = None

        self._reader_thread = Thread(target=self._socket_reader, daemon=True)
        self._reader_thread.start()
        self._run()

    def get_queue(self):
        return self.in_queue

    def get_socket(self):
        return self.cs

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
                 b'<QR_G>': self._case_QRG,
                 b'<L>': self._case_L,
                 b'<S>': self._case_S,
                 b'<DISCONNECTED>': self._case_DISCONNECTED}  # TODO add default handler if no key found,

        while self.cs:
            data = self.in_queue.get(block=True)
            lg.debug('<Queue get> ' + str(data))
            values = data.split(b'~')

            cases[values[0]](values)

    def _case_policy(self, values):
        lg.debug('policy file requested')
        self.cs.send(b'<cross-domain-policy><allow-access-from domain="*" to-ports="*" /></cross-domain-policy>\x00')

    def _case_QRG(self, values):
        pass

    def _case_L(self, values):
        self.game_server.register_client(self)
        self.cs.send(b'<S>~<SERVER>~<PLAYERS_COUNT>~' +
                     str(self.game_server.get_player_count(self.own_username, self.opponent_username)).encode('utf8')
                     + b'\x00')

    def _case_S(self, values):
        if self.out_socket:
            self.out_socket.send(b'~'.join(values) + b'\x00')

    def _case_DISCONNECTED(self, values):
        lg.debug('Connection closed by client')
        self.game_server.remove_client(self)
        self.exit()

    def exit(self):
        if self.cs:
            try:
                self.cs.shutdown(1)
            except OSError:
                pass
            self.cs.close()
            self.cs = None
