from asyncio import Task, sleep as aiosleep, create_task
from datetime import datetime, timezone
import logging
from typing import Optional

from QRServer.common.classes import PairingId, MatchParty
from QRServer.common.clienthandler import ClientHandler
from QRServer.common.messages import PlayerCountResponse, HelloGameRequest, JoinGameRequest, UsePowerMessage, \
    RequestMessage, ResponseMessage, GameChatMessage, GrabPieceMessage, ReleasePieceMessage, SwitchPlayerMessage, \
    RecursiveDoneMessage, RemovePlayerMessage, PowerNoEffectMessage, NukeMessage, JumpOnPieceMessage, \
    GetPowerSquareMessage, SettingsLoadedMessage, AssignPowerSquareMessage, AssignNextPowerCountMessage, \
    NewGridCoordMessage, ResignMessage, ServerPingRequest, SettingsArenaSizeMessage, \
    SettingsReadyOffMessage, SettingsSquadronSizeMessage, SettingsTimerMessage, SettingsTopBottomMessage, \
    SettingsColorMessage, DisconnectRequest, SettingsReadyOnMessage, SettingsReadyOnAgainMessage, PolicyFileRequest, \
    CrossDomainPolicyAllowAllResponse, OpponentDeadResponse, VoidScoreRequest, VoidScoreResponse, AddStatsRequest, \
    SwitcherooMessage, RemoveOneWayWallMessage, BankruptActionMessage, ServerAliveResponse
from QRServer.discord.webhook import Webhook

log = logging.getLogger('qr.game_client_handler')


class GameClientHandler(ClientHandler, MatchParty):
    opponent_handler: Optional['GameClientHandler']
    _invite_sentinel_task: None | Task

    def __init__(self, config, connector, reader, writer, game_server):
        super().__init__(config, connector, reader, writer)
        self.webhook = Webhook(config)
        self.opponent_handler = None
        self.game_server = game_server

        self._user_id = None
        self.opponent_id = None
        self._username = None
        self.opponent_username = None
        self.own_auth = None
        self.opponent_auth = None
        self._is_guest = True
        self._is_void_score = False
        self.invite_id = None
        self._invite_sentinel_task = None

        self.register_message_handler(PolicyFileRequest, self._handle_policy)
        self.register_message_handler(HelloGameRequest, self._handle_hello_game)
        self.register_message_handler(JoinGameRequest, self._handle_join_game)
        self.register_message_handler(ServerPingRequest, self._handle_ping)
        self.register_message_handler(DisconnectRequest, self._handle_disconnect)
        self.register_message_handler(AddStatsRequest, self._handle_add_stats)
        self.register_message_handler(VoidScoreRequest, self._handle_void_score)
        self.register_handler(b'<S>', self._handle_s)

        # forwarding messages
        self.register_message_handler(UsePowerMessage, self._handle_forward)
        self.register_message_handler(SwitcherooMessage, self._handle_forward)
        self.register_message_handler(RemoveOneWayWallMessage, self._handle_forward)
        self.register_message_handler(BankruptActionMessage, self._handle_forward)
        self.register_message_handler(GameChatMessage, self._handle_forward)
        self.register_message_handler(GrabPieceMessage, self._handle_forward)
        self.register_message_handler(ReleasePieceMessage, self._handle_forward)
        self.register_message_handler(SwitchPlayerMessage, self._handle_forward)
        self.register_message_handler(RecursiveDoneMessage, self._handle_forward)
        self.register_message_handler(RemovePlayerMessage, self._handle_forward)
        self.register_message_handler(PowerNoEffectMessage, self._handle_forward)
        self.register_message_handler(NukeMessage, self._handle_forward)
        self.register_message_handler(JumpOnPieceMessage, self._handle_forward)
        self.register_message_handler(GetPowerSquareMessage, self._handle_forward)
        self.register_message_handler(SettingsLoadedMessage, self._handle_forward)
        self.register_message_handler(AssignPowerSquareMessage, self._handle_forward)
        self.register_message_handler(AssignNextPowerCountMessage, self._handle_forward)
        self.register_message_handler(NewGridCoordMessage, self._handle_forward)
        self.register_message_handler(ResignMessage, self._handle_forward)
        self.register_message_handler(SettingsReadyOnMessage, self._handle_forward)
        self.register_message_handler(SettingsReadyOnAgainMessage, self._handle_forward)
        self.register_message_handler(SettingsReadyOffMessage, self._handle_forward)
        self.register_message_handler(SettingsArenaSizeMessage, self._handle_forward)
        self.register_message_handler(SettingsSquadronSizeMessage, self._handle_forward)
        self.register_message_handler(SettingsTimerMessage, self._handle_forward)
        self.register_message_handler(SettingsTopBottomMessage, self._handle_forward)
        self.register_message_handler(SettingsColorMessage, self._handle_forward)

    @property
    def is_void_score(self):
        return self._is_void_score

    @property
    def is_guest(self):
        return self._is_guest

    @property
    def user_id(self) -> str:
        return self._user_id

    def pairing_id(self) -> PairingId:
        if not self.config.auto_register.get() or self.config.auth_disable.get():
            return PairingId(self.username, self.opponent_username)
        return PairingId(self.user_id, self.opponent_id)

    def match_opponent(self, opponent: 'MatchParty'):
        if not isinstance(opponent, GameClientHandler):
            raise Exception('Wrong opponent')
        self.opponent_handler = opponent

        # If opponent connected, early quit the sentinel
        if self._invite_sentinel_task:
            self._invite_sentinel_task.cancel()

    def unmatch_opponent(self):
        self.opponent_handler = None

    async def _handle_policy(self, _: PolicyFileRequest):
        log.debug('Policy file requested')
        await self.send_msg(CrossDomainPolicyAllowAllResponse.new())

    async def _handle_hello_game(self, message: HelloGameRequest):
        pass

    async def _handle_join_game(self, message: JoinGameRequest):
        self.own_auth = message.get_auth()
        self.opponent_username = message.get_opponent_username()
        self.opponent_auth = message.get_opponent_auth()

        username = message.get_username()
        password = message.get_password()

        # if both auths are negative then its likely an invite match with temp passwords,
        # run a separate auth flow where we check if username + temp password submitted matches the invite
        if int(self.own_auth) < 0 and int(self.opponent_auth) < 0:
            match_invite = await self.connector.get_match_invite_by_tmp_pass(password)
            if not match_invite:
                log.debug(f'Player {username} attempted joining nonexistent invite')
                self.close_and_stop()
                return

            if not match_invite.is_active:
                log.debug(f'Player {username} attempted joining inactive invite')
                self.close_and_stop()
                return

            self.invite_id = match_invite.invite_id
            if password == match_invite.challenger_tmp_pass:
                my_id = match_invite.challenger_id
                opp_id = match_invite.challenged_id
            else:
                my_id = match_invite.challenged_id
                opp_id = match_invite.challenger_id

            my_db_user = await self.connector.get_user(my_id)
            opp_db_user = await self.connector.get_user(opp_id)
            self._username = username

            if my_db_user.username != self.username or opp_db_user.username != self.opponent_username:
                log.warning(f'Players do not match the invite: id: {self.invite_id},'
                            f' my_username: {self.username}, opp_username: {self.opponent_username},'
                            f" my_user: {my_db_user}, opp_user: {opp_db_user}")
                self.close_and_stop()
                return

            timeout = (match_invite.active_until - datetime.now(timezone.utc)).total_seconds()
            # TODO check if this starts the task in bg and lets the code continue
            self._invite_sentinel_task = create_task(self._invite_sentinel(timeout))
            db_user = my_db_user
        else:
            db_user = await self.authenticate_user(username, password)

        if not db_user:
            log.debug(f'Player {username} tried to connect to a game, but failed to authenticate')
            # according to my analysis, there's no way to tell the client
            # it failed to authenticate, so just close the connection
            self.close_and_stop()
            return

        self._user_id = db_user.user_id
        self._is_guest = db_user.is_guest

        db_opponent = await self.connector.get_user_by_username(self.opponent_username)
        if not db_opponent:
            log.error(
                f'Player {username} tried to connect to a game with a ' +
                'non existing opponent {self.opponent_username}')
            self.close_and_stop()
            return

        self.opponent_id = db_opponent.user_id

        await self.game_server.register_client(self)
        player_count = self.game_server.get_player_count()
        await self.send_msg(PlayerCountResponse.new(player_count))

        if self.username < self.opponent_username:
            log.info(f'A match has started between {self.username} and {self.opponent_username}')
            await self.webhook.invoke_webhook_game_started(self.username, self.opponent_username)

    async def _handle_s(self, values):
        if self.opponent_handler:
            await self.opponent_handler.send(b'~'.join(values) + b'\x00')

    async def _handle_forward(self, message: RequestMessage):
        if not isinstance(message, ResponseMessage):
            raise Exception('Trying to send a non-response message')
        if self.opponent_handler:
            await self.opponent_handler.send_msg(message)

    async def _handle_ping(self, message: ServerPingRequest):
        await self.send_msg(ServerAliveResponse.new())

    async def _handle_void_score(self, _: VoidScoreRequest):
        self._is_void_score = True
        if self.opponent_handler:
            await self.opponent_handler.send_msg(VoidScoreResponse.new())

    async def _handle_add_stats(self, message: AddStatsRequest):
        await self.game_server.add_match_stats(self, message.to_stats())

    async def _handle_disconnect(self, _: DisconnectRequest):
        log.debug('Connection closed by client')
        if self.opponent_handler is not None:
            await self.opponent_handler.send_msg(OpponentDeadResponse.new())

        await self.game_server.remove_client(self)
        self.close_and_stop()

    async def _invite_sentinel(self, timeout_s: float):
        await aiosleep(timeout_s)
        if not self.opponent_handler:
            log.debug(
                f'Opponent: {self.opponent_username} did not join {self.username} for the invite-only match in time'
            )
            await self.game_server.remove_client(self)
            self.close_and_stop()
            return
