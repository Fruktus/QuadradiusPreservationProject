import logging
from datetime import datetime

from QRServer import config
from QRServer.common import utils
from QRServer.common.classes import RankingEntry
from QRServer.common.clienthandler import ClientHandler
from QRServer.common.messages import BroadcastCommentResponse, OldSwfResponse, LobbyDuplicateResponse, \
    ServerAliveResponse, LobbyBadMemberResponse, LastPlayedResponse, ServerRankingResponse
from QRServer.db.connector import connector

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
            self.send_msg(OldSwfResponse())
            log.debug('Client with invalid version tried to connect, version: {}'.format(swf_version))
            self.close()

    def _handle_join_lobby(self, values):
        username = values[1].decode('utf8')
        password = values[2]
        is_guest = utils.is_guest(username, password)

        if not is_guest and not config.auth_disable.get():
            user_id = connector().authenticate_member(username, password)
            if user_id is None:
                log.debug('Player {} tried to connect, but failed to authenticate'.format(username))
                self._error_bad_member()
                self.close()
                return

        if self.lobby_server.username_exists(username):
            log.debug('Client duplicate in lobby: ' + username)
            self.send_msg(LobbyDuplicateResponse())
            self.close()  # FIXME it seems that the connection shouldnt be completely closed
            return

        # user authenticated successfully, register with lobbyserver
        self.username = username
        self.idx = self.lobby_server.add_client(self)
        self.joined_at = datetime.now()
        self.send(self.lobby_server.get_clients_string())

        if is_guest:
            log.info('Guest joined: ' + username)
        else:
            log.info('Member joined: ' + username)

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
            self.send_msg(ServerAliveResponse())
        elif query == '<RECENT>':
            self.send_msg(self.lobby_server.get_last_logged())
            self.send_msg(LastPlayedResponse([]))
            self.send_msg(ServerRankingResponse(True, [
                RankingEntry(player='test', wins=12, games=30),
                RankingEntry(player='test2', wins=2, games=2),
            ]))
        elif query == '<COMMENT>':
            # TODO if user is a member, update the database
            self.lobby_server.broadcast_chat_msg(BroadcastCommentResponse(values[2], values[3]))
        elif query == '<RANKING>':
            # TODO implement ranking
            pass
        else:
            # unknown query
            pass

    def _handle_b(self, values):
        if values[1] == b'<CHAT>':
            self.lobby_server.broadcast_chat(b'~'.join(values) + b'\x00')

    def _handle_disconnect(self, values):
        log.debug('Connection closed by client')
        if self.idx is not None:
            log.info('Player left: ' + self.username)
            self.lobby_server.remove_client(self.idx)

        self.close()

    def _error_bad_member(self):
        self.send_msg(LobbyBadMemberResponse())
