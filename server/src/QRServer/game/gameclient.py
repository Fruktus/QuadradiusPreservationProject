import logging
from typing import Optional

from QRServer import config
from QRServer.common.classes import MatchId, MatchParty
from QRServer.common.clienthandler import ClientHandler
from QRServer.common.messages import PlayerCountResponse, HelloGameRequest, JoinGameRequest, UsePowerMessage, \
    RequestMessage, ResponseMessage, GameChatMessage, GrabPieceMessage, ReleasePieceMessage, SwitchPlayerMessage, \
    RecursiveDoneMessage, RemovePlayerMessage, PowerNoEffectMessage, NukeMessage, JumpOnPieceMessage, \
    GetPowerSquareMessage, SettingsLoadedMessage, AssignPowerSquareMessage, AssignNextPowerCountMessage, \
    NewGridCoordMessage, ResignMessage, ServerPingRequest, SettingsArenaSizeMessage, \
    SettingsReadyOffMessage, SettingsSquadronSizeMessage, SettingsTimerMessage, SettingsTopBottomMessage, \
    SettingsColorMessage, DisconnectRequest, SettingsReadyOnMessage, SettingsReadyOnAgainMessage, PolicyFileRequest, \
    CrossDomainPolicyAllowAllResponse, OpponentDeadResponse, VoidScoreRequest, VoidScoreResponse, AddStatsRequest
from QRServer.db.connector import connector
from QRServer.discord.webhook import invoke_webhook_game_started
from QRServer.listener import listen_for_connections

log = logging.getLogger('game_client_handler')


async def game_listener(conn_host, conn_port, game_server):
    async def handler(client_socket):
        client = GameClientHandler(client_socket, game_server)
        await client.run()

    await listen_for_connections(conn_host, conn_port, handler, 'Game')


class GameClientHandler(ClientHandler, MatchParty):
    opponent_handler: Optional['GameClientHandler']

    def __init__(self, client_socket, game_server):
        super().__init__(client_socket)
        self.opponent_handler = None
        self.game_server = game_server

        self.user_id = None
        self.opponent_id = None
        self.username = None
        self.opponent_username = None
        self.own_auth = None
        self.opponent_auth = None
        self.password = None
        self.is_guest = True
        self.void_score = False

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
    def client_id(self) -> str:
        return self.username if config.auth_disable.get() else self.user_id

    def match_id(self) -> MatchId:
        if not config.auto_register.get() or config.auth_disable.get():
            return MatchId(self.username, self.opponent_username)
        return MatchId(self.user_id, self.opponent_id)

    def match_opponent(self, opponent: 'MatchParty'):
        if not isinstance(opponent, GameClientHandler):
            raise Exception('Wrong opponent')
        self.opponent_handler = opponent

    def unmatch_opponent(self):
        self.opponent_handler = None

    async def _handle_policy(self, message: PolicyFileRequest):
        log.debug('policy file requested')
        await self.send_msg(CrossDomainPolicyAllowAllResponse())

    async def _handle_hello_game(self, message: HelloGameRequest):
        pass

    async def _handle_join_game(self, message: JoinGameRequest):
        self.username = message.get_username()
        self.own_auth = message.get_auth()
        self.opponent_username = message.get_opponent_username()
        self.opponent_auth = message.get_opponent_auth()
        self.password = message.get_password()

        if not config.auth_disable.get():
            db_user = await (await connector()).get_user_by_username(self.username)
            self.user_id = db_user.user_id
            self.is_guest = db_user.is_guest

            db_opponent = await (await connector()).get_user_by_username(self.opponent_username)
            self.opponent_id = db_opponent.user_id

        self.game_server.register_client(self)
        player_count = self.game_server.get_player_count()
        await self.send_msg(PlayerCountResponse(player_count))

        if self.username < self.opponent_username:
            await invoke_webhook_game_started(self.username, self.opponent_username)

    async def _handle_s(self, values):
        if self.opponent_handler:
            await self.opponent_handler.send(b'~'.join(values) + b'\x00')

    async def _handle_forward(self, message: RequestMessage):
        if not isinstance(message, ResponseMessage):
            raise Exception('Trying to send a non-response message')
        if self.opponent_handler:
            await self.opponent_handler.send_msg(message)

    async def _handle_ping(self, message: ServerPingRequest):
        # we have to ignore this message, responding to it
        # causes synchronization problems
        pass

    async def _handle_void_score(self, message: VoidScoreRequest):
        self.void_score = True
        if self.opponent_handler:
            await self.opponent_handler.send_msg(VoidScoreResponse())

    async def _handle_add_stats(self, message: AddStatsRequest):
        await self.game_server.add_match_stats(self, message.to_stats())

    async def _handle_disconnect(self, message: DisconnectRequest):
        log.debug('Connection closed by client')
        if self.opponent_handler is not None:
            await self.opponent_handler.send_msg(OpponentDeadResponse())

        await self.game_server.remove_client(self)
        self.close()
