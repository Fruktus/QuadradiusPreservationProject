import logging
from datetime import datetime

from QRServer import config
from QRServer.common import utils
from QRServer.common.classes import RankingEntry, LobbyPlayer
from QRServer.common.clienthandler import ClientHandler
from QRServer.common.messages import BroadcastCommentResponse, OldSwfResponse, LobbyDuplicateResponse, \
    ServerAliveResponse, LobbyBadMemberResponse, LastPlayedResponse, ServerRankingResponse, HelloLobbyRequest, \
    JoinLobbyRequest, ServerRecentRequest, ServerRankingRequest, ServerAliveRequest, LobbyStateResponse, \
    ResponseMessage, LobbyChatMessage, SetCommentRequest, ChallengeMessage, ChallengeAuthMessage, DisconnectRequest, \
    PolicyFileRequest, CrossDomainPolicyAllowAllResponse
from QRServer.db.connector import connector
from QRServer.discord.webhook import send_webhook_joined_lobby, send_webhook_left_lobby

log = logging.getLogger('lobby_client_handler')


class LobbyClientHandler(ClientHandler):
    player: LobbyPlayer

    def __init__(self, client_socket, lobby_server):
        super().__init__(client_socket)
        self.lobby_server = lobby_server

        self.player = LobbyPlayer()

        self.register_message_handler(PolicyFileRequest, self._handle_policy)
        self.register_message_handler(HelloLobbyRequest, self._handle_hello_lobby)
        self.register_message_handler(JoinLobbyRequest, self._handle_join_lobby)
        self.register_message_handler(ServerRecentRequest, self._handle_server_recent)
        self.register_message_handler(ServerRankingRequest, self._handle_server_ranking)
        self.register_message_handler(ServerAliveRequest, self._handle_server_alive)
        self.register_message_handler(SetCommentRequest, self._handle_set_comment)
        self.register_message_handler(LobbyChatMessage, self._handle_broadcast)
        self.register_message_handler(ChallengeMessage, self._handle_challenge)
        self.register_message_handler(ChallengeAuthMessage, self._handle_challenge_auth)
        self.register_message_handler(DisconnectRequest, self._handle_disconnect)

    def get_username(self) -> str:
        return self.player.username

    def get_joined_at(self) -> datetime:
        return self.player.joined_at

    def get_player(self) -> LobbyPlayer:
        return self.player

    def _handle_policy(self, message: PolicyFileRequest):
        log.debug('policy file requested')
        self.send_msg(CrossDomainPolicyAllowAllResponse())

    def _handle_hello_lobby(self, message: HelloLobbyRequest):
        swf_version = message.get_swf_version()
        if swf_version != 5:
            self.send_msg(OldSwfResponse())
            log.debug(f'Client with invalid version tried to connect, version: {swf_version}')
            self.close()

    def _handle_join_lobby(self, message: JoinLobbyRequest):
        username = message.get_username()
        password = message.get_password()
        is_guest = utils.is_guest(username, password)

        self.player.user_id = connector().authenticate_member(username, password.encode('ascii'))
        if not is_guest and not config.auth_disable.get():
            if self.player.user_id is None:
                log.debug(f'Player {username} tried to connect, but failed to authenticate')
                self._error_bad_member()
                self.close()
                return

        if self.lobby_server.username_exists(username):
            log.debug('Client duplicate in lobby: ' + username)
            self.send_msg(LobbyDuplicateResponse())
            self.close()  # FIXME it seems that the connection shouldnt be completely closed
            return

        # user authenticated successfully, register with lobbyserver
        self.player.username = username
        self.player.joined_at = datetime.now()
        self.player.communique = connector().get_comment(self.player.user_id) or ' '
        self.player.idx = self.lobby_server.add_client(self)
        self.send_msg(LobbyStateResponse(self.lobby_server.get_players()))

        if is_guest:
            log.info('Guest joined lobby: ' + username)
        else:
            log.info('Member joined lobby: ' + username)

        send_webhook_joined_lobby(username, sum(player is not None for player in self.lobby_server.get_players()))

    def _handle_challenge(self, message: ChallengeMessage):
        challenger_idx = message.get_challenger_idx()
        challenged_idx = message.get_challenged_idx()
        log.debug('Challenge issued')
        self.lobby_server.challenge_user(challenger_idx, challenged_idx)

    def _handle_challenge_auth(self, message: ChallengeAuthMessage):
        challenger_idx = message.get_challenger_idx()
        challenged_idx = message.get_challenged_idx()
        challenger_auth = message.get_auth()
        self.lobby_server.setup_challenge(challenger_idx, challenged_idx, challenger_auth)

    def _handle_server_recent(self, message: ServerRecentRequest):
        recent_matches = connector().get_recent_matches()
        self.send_msg(self.lobby_server.get_last_logged())
        self.send_msg(LastPlayedResponse(recent_games=recent_matches))

    def _handle_server_ranking(self, message: ServerRankingRequest):
        self.send_msg(ServerRankingResponse(True, [
            RankingEntry(player='test', wins=12, games=30),
            RankingEntry(player='test2', wins=2, games=2),
        ]))

    def _handle_server_alive(self, message: ServerAliveRequest):
        self.send_msg(ServerAliveResponse())

    def _handle_set_comment(self, message: SetCommentRequest):
        who = message.get_idx()
        comment = message.get_comment()
        if who != self.player.idx:
            log.debug(f'Error while setting comment: wrong idx, expected {self.player.idx} was {who}')
            return
        if self.player.user_id:
            connector().set_comment(self.player.user_id, comment)
        self.player.comment = comment
        self.lobby_server.broadcast_msg(BroadcastCommentResponse(who, comment))

    def _handle_broadcast(self, message):
        if not isinstance(message, ResponseMessage):
            raise Exception('Trying to send a non-response message')
        self.lobby_server.broadcast_msg(message)

    def _handle_disconnect(self, message: DisconnectRequest):
        log.debug('Connection closed by client')
        if self.player.idx is not None:
            log.info(f'Player left lobby: {self.player.username}')
            self.lobby_server.remove_client(self.player.idx)
            total_players = sum(player is not None for player in self.lobby_server.get_players())
            send_webhook_left_lobby(self.player.username, total_players)

        self.close()

    def _error_bad_member(self):
        self.send_msg(LobbyBadMemberResponse())
