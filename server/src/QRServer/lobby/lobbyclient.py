import asyncio
import logging
from datetime import datetime

from QRServer.common import utils
from QRServer.common.classes import LobbyPlayer
from QRServer.common.clienthandler import ClientHandler
from QRServer.common.messages import BroadcastCommentResponse, OldSwfResponse, LobbyDuplicateResponse, \
    ServerAliveResponse, LobbyBadMemberResponse, LastPlayedResponse, ServerRankingThisMonthResponse, \
    HelloLobbyRequest, JoinLobbyRequest, ServerRecentRequest, ServerRankingRequest, ServerAliveRequest, \
    LobbyStateResponse, LobbyChatMessage, SetCommentRequest, ChallengeMessage, ChallengeAuthMessage, \
    DisconnectRequest, PolicyFileRequest, CrossDomainPolicyAllowAllResponse, NameTakenRequest, \
    NameTakenResponseYes, NameTakenResponseNo, ChangePasswordRequest, ChangePasswordResponseOk
from QRServer.discord.webhook import Webhook

log = logging.getLogger('qr.lobby_client_handler')


class LobbyClientHandler(ClientHandler):
    player: LobbyPlayer

    def __init__(self, config, connector, reader, writer, lobby_server):
        super().__init__(config, connector, reader, writer)
        self.webhook = Webhook(config)
        self.lobby_server = lobby_server

        self.player = LobbyPlayer()

        self.register_message_handler(PolicyFileRequest, self._handle_policy)
        self.register_message_handler(HelloLobbyRequest, self._handle_hello_lobby)
        self.register_message_handler(JoinLobbyRequest, self._handle_join_lobby)
        self.register_message_handler(ServerRecentRequest, self._handle_server_recent)
        self.register_message_handler(ServerRankingRequest, self._handle_server_ranking)
        self.register_message_handler(ServerAliveRequest, self._handle_server_alive)
        self.register_message_handler(SetCommentRequest, self._handle_set_comment)
        self.register_message_handler(LobbyChatMessage, self._handle_chat_message)
        self.register_message_handler(ChallengeMessage, self._handle_challenge)
        self.register_message_handler(ChallengeAuthMessage, self._handle_challenge_auth)
        self.register_message_handler(DisconnectRequest, self._handle_disconnect)
        self.register_message_handler(NameTakenRequest, self._handle_name_taken)
        self.register_message_handler(ChangePasswordRequest, self._handle_change_password)

    def get_joined_at(self) -> datetime:
        return self.player.joined_at

    def get_player(self) -> LobbyPlayer:
        return self.player

    async def _handle_policy(self, _: PolicyFileRequest):
        log.debug('policy file requested')
        await self.send_msg(CrossDomainPolicyAllowAllResponse.new())

    async def _handle_hello_lobby(self, message: HelloLobbyRequest):
        swf_version = message.get_swf_version()
        if swf_version != 5:
            await self.send_msg(OldSwfResponse.new())
            log.debug(f'Client with invalid version tried to connect, version: {swf_version}')
            self.close_and_stop()

    async def _handle_join_lobby(self, message: JoinLobbyRequest):
        username = message.get_username()
        password = message.get_password()
        self.player.is_guest = utils.is_guest(username, password)
        if not password:
            # Password is always mandatory, if it is missing, then
            # someone might be sending raw or damaged packets
            log.debug(f'Player {username} did not provide any password')
            await self._error_bad_member()
            self.close_and_stop()
            return

        db_user = await self.authenticate_user(username, password)
        if not db_user:
            log.debug(f'Player {username} tried to connect, but failed to authenticate')
            await self._error_bad_member()
            self.close_and_stop()
            return

        if self.lobby_server.username_exists(username):
            log.debug('Client duplicate in lobby: ' + username)
            await self.send_msg(LobbyDuplicateResponse.new())
            self.close_and_stop()  # FIXME it seems that the connection shouldnt be completely closed
            return

        # user authenticated successfully, register with lobbyserver
        self.player.user_id = db_user.user_id
        self.player.username = username
        self.player.joined_at = datetime.now()
        self.player.idx = await self.lobby_server.add_client(self)
        await self.send_msg(LobbyStateResponse.new(self.lobby_server.get_players()))

        if self.player.is_guest:
            log.info('Guest joined lobby: ' + username)
        else:
            log.info('Member joined lobby: ' + username)

        total_players = self.lobby_server.get_player_count()
        await self.webhook.invoke_webhook_lobby_joined(username, total_players)

        if self.config.lobby_motd.get():
            await self.send_msg(LobbyChatMessage.new('', self.config.lobby_motd.get()))

    async def _handle_challenge(self, message: ChallengeMessage):
        challenger_idx = message.get_challenger_idx()
        challenged_idx = message.get_challenged_idx()
        log.debug('Challenge issued')
        await self.lobby_server.challenge_user(challenger_idx, challenged_idx)

    async def _handle_challenge_auth(self, message: ChallengeAuthMessage):
        challenger_idx = message.get_challenger_idx()
        challenged_idx = message.get_challenged_idx()
        challenger_auth = message.get_auth()
        await self.lobby_server.setup_challenge(challenger_idx, challenged_idx, challenger_auth)

    async def _handle_server_recent(self, _: ServerRecentRequest):
        recent_matches = await self.connector.get_recent_matches()
        await self.send_msg(self.lobby_server.get_last_logged())
        await self.send_msg(LastPlayedResponse.new(recent_matches))

    async def _handle_server_ranking(self, request: ServerRankingRequest):
        start_date, end_date = utils.make_month_dates(request.get_month(), request.get_year())

        rankings = await self.connector.get_ranking(
            start_date=start_date,
            end_date=end_date,
            ranked_only=self.config.leaderboards_ranked_only.get(),
            include_void=self.config.leaderboards_include_void.get()
        )
        await self.send_msg(ServerRankingThisMonthResponse.new(rankings))

    async def _handle_server_alive(self, _: ServerAliveRequest):
        await self.send_msg(ServerAliveResponse.new())

    async def _handle_set_comment(self, message: SetCommentRequest):
        who = message.get_idx()
        comment = message.get_comment()
        if who != self.player.idx:
            log.debug(f'Error while setting comment: wrong idx, expected {self.player.idx} was {who}')
            return
        self.player.comment = comment
        await self.lobby_server.broadcast_msg(BroadcastCommentResponse.new(who, comment))
        await self.webhook.invoke_webhook_lobby_set_comment(self.player.username, comment)

    async def _handle_chat_message(self, message: LobbyChatMessage):
        await self.lobby_server.broadcast_msg(message)
        text = message.get_text()
        message = text.split(':', 1)[1].strip()
        if message.startswith('(COMMUNIQUE)'):
            return
        await self.webhook.invoke_webhook_lobby_message(self.player.username, message)

    async def _handle_disconnect(self, _: DisconnectRequest):
        log.debug('Connection closed by client')
        if self.player.idx is not None:
            log.info(f'Player left lobby: {self.player.username}')
            await self.lobby_server.remove_client(self.player.idx)
            total_players = self.lobby_server.get_player_count()
            await self.webhook.invoke_webhook_lobby_left(self.player.username, total_players)

        self.close_and_stop()

    async def _handle_name_taken(self, message: NameTakenRequest):
        username = message.get_name_to_check()
        log.debug(f'Checking whether a name is taken: {username}')

        # Prevent users from spamming such requests
        await asyncio.sleep(1)

        user = await self.connector.get_user_by_username(username)

        if user:
            await self.send_msg(NameTakenResponseYes.new())
        else:
            await self.send_msg(NameTakenResponseNo.new())

    async def _handle_change_password(self, message: ChangePasswordRequest):
        if self.player.is_guest:
            log.warning(f'A guest {self.player.username}:{self.player.user_id} has tried to change their password')
            return

        if self.config.auth_disable.get():
            log.warning(f'Cannot change any password when auth is disabled ({self.player.username})')
            return

        new_password = message.get_new_password()
        if not new_password:
            log.warning(f'Member {self.player.username} tried to change their password to an empty one')
            return

        await self.connector.change_user_password(self.player.user_id, new_password.encode('ascii'))

        log.info(f'Member {self.player.username} has changed their password')

        await self.send_msg(ChangePasswordResponseOk.new())

    async def _error_bad_member(self):
        await self.send_msg(LobbyBadMemberResponse.new())
