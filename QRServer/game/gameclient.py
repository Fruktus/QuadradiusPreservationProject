import logging
import socket

from QRServer.common.classes import MatchId, MatchParty
from QRServer.common.clienthandler import ClientHandler

log = logging.getLogger('game_client_handler')


class GameClientHandler(ClientHandler, MatchParty):
    out_socket: socket

    def __init__(self, client_socket, game_server):
        super().__init__(client_socket)
        self.out_socket = None
        self.game_server = game_server

        self.username = None
        self.opponent_username = None
        self.own_auth = None
        self.opponent_auth = None
        self.password = None

        self.register_handler(b'<policy-file-request/>', self._handle_policy)
        self.register_handler(b'<QR_G>', self._handle_qrg)
        self.register_handler(b'<L>', self._handle_l)
        self.register_handler(b'<S>', self._handle_s)
        self.register_handler(b'<SERVER>', self._handle_server)
        self.register_handler(b'<DISCONNECTED>', self._handle_disconnect)

    def match_id(self) -> MatchId:
        return MatchId(self.username, self.opponent_username)

    def match_opponent(self, opponent: 'MatchParty'):
        if not isinstance(opponent, GameClientHandler):
            raise Exception('Wrong opponent')
        self.out_socket = opponent.cs

    def unmatch_opponent(self):
        self.out_socket = None

    def _handle_policy(self, values):
        log.debug('policy file requested')
        self.send(b'<cross-domain-policy><allow-access-from domain="*" to-ports="*" /></cross-domain-policy>\x00')

    def _handle_qrg(self, values):
        pass

    def _handle_l(self, values):
        self.game_server.register_client(self)
        self.send(
            b'<S>~<SERVER>~<PLAYERS_COUNT>~' +
            str(self.game_server.get_player_count(self.match_id())).encode('utf8') +
            b'\x00')

    def _handle_s(self, values):
        if self.out_socket:
            self.out_socket.send(b'~'.join(values) + b'\x00')

    def _handle_server(self, values):
        pass
        # if values[1] == b'<PING>':
        #     self.cs.send(b'<SERVER>~<ALIVE>\x00')

    def _handle_disconnect(self, values):
        log.debug('Connection closed by client')
        self.game_server.remove_client(self)
        self.close()
