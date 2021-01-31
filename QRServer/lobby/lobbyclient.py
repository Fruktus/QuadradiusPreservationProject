import logging
from time import time

from QRServer.common.clienthandler import ClientHandler
from QRServer.dbconnector import DBConnector

log = logging.getLogger('lobby_client_handler')


class LobbyClientHandler(ClientHandler):
    def __init__(self, client_socket, lobby_server):
        super().__init__(client_socket)
        self.lobby_server = lobby_server

        self.username = ''
        self.communique = ' '
        self.score = 0
        self.awards = [0] * 10

        self.idx = None
        self.joined_at = None

        self.register_handler(b'<policy-file-request/>', self._handle_policy)
        self.register_handler(b'<QR_L>', self._handle_qrl)
        self.register_handler(b'<L>', self._handle_join_lobby)
        self.register_handler(b'<S>', self._handle_challenge)
        self.register_handler(b'<SERVER>', self._handle_server_query)
        self.register_handler(b'<B>', self._handle_b)
        self.register_handler(b'<DISCONNECTED>', self._handle_disconnect)

    def get_repr(self):
        return '~' + self.username + '~' + self.communique + '~' + str(self.score) + '~' + \
               '~'.join([str(x) for x in self.awards])

    @staticmethod
    def get_empty_repr():
        return '~<EMPTY>~ ~0~0~0~0~0~0~0~0~0~0~0'

    def _handle_policy(self, values):
        log.debug('policy file requested')
        self.send(b'<cross-domain-policy><allow-access-from domain="*" to-ports="*" /></cross-domain-policy>\x00')

    def _handle_qrl(self, values):
        swf_version = int(values[1])
        log.debug('SWF Version: {}'.format(swf_version))
        if swf_version != 5:
            self.cs.send(b'<S><SERVER><OLD_SWF>\x00')
            log.info('Client with invalid version tried to connect, version: {}'.format(swf_version))
            self.close()

    def _handle_join_lobby(self, values):
        username = values[1].decode('utf8')
        password = values[2].decode('utf8')
        if not DBConnector().user_exists(username, password):  # FIXME implement dbconnector
            self.send(b'<L>~<BAD_MEMBER>\x00')
            self.close()
        elif self.lobby_server.username_exists(username):
            log.info('Client duplicate in lobby: ' + username)
            self.send(b'<L>~<DUPLICATE>\x00')
            self.close()  # FIXME it seems that the connection shouldnt be completely closed
        else:
            # user authenticated successfully, register with lobbyserver
            log.info('Client joining: ' + username)
            self.username = username
            self.idx = self.lobby_server.add_client(self)
            self.joined_at = time()
            self.send(self.lobby_server.get_clients_string())

    def _handle_challenge(self, values):
        challenger_idx = int(values[1].decode('utf8'))
        challenged_idx = int(values[2].decode('utf8'))
        if values[3] == b'<SHALLWEPLAYAGAME?>':
            log.debug('challenge issued')
            self.lobby_server.challenge_user(challenger_idx, challenged_idx)
        elif values[3] == b'<AUTHENTICATION>':
            challenger_auth = int(values[4].decode('utf8'))
            self.lobby_server.setup_challenge(challenger_idx, challenged_idx, challenger_auth)

    def _handle_server_query(self, values):
        query = values[1].decode('utf-8')
        if query == '<ALIVE?>':
            self.send(b'<S>~<SERVER>~<ALIVE>\x00')
        if query == '<RECENT>':
            self.send(b'<S>~<SERVER>~<LAST_LOGGED>~DBGX~999~\x00')
            self.send(
                b'<S>~<SERVER>~<LAST_PLAYED>~imt beat sifl#7-0#13:38~imt beat sifl#12-9#07:19~sifl beat imt#3-0#11:46~imt beat dan ddm#15-0#14:49~sifl beat imt#4-1#10:04~dan ddm beat sifl#13-0#10:41~sifl beat imt#12-6#13:54~sifl beat imt#19-0#09:26~slug800 beat imt#14-3#11:52~imt beat slug800#19-2#12:06~sifl beat imt#13-6#13:08~sifl beat imt#9-3#13:21~sifl beat imt#5-1#09:18~sifl beat imt#19-14#09:22~sifl beat hoyvinmayvin#20-5#13:28\x00')
            self.send(
                b'<S>~<SERVER>~<RANKING(thisMonth)>~sifl~1~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~...............~0~1~\x00')

    def _handle_b(self, values):
        pass

    def _handle_disconnect(self, values):
        log.debug('Connection closed by client')
        if self.idx is not None:
            log.debug('removing client idx: ' + str(self.idx))
            self.lobby_server.remove_client(self.idx)
        # stop the thread
        # TODO
        self.close()
