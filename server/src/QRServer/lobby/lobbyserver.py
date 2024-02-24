import logging
from datetime import datetime
from typing import Optional, List

from QRServer.common.classes import LobbyPlayer
from QRServer.common.messages import ResponseMessage, LastLoggedResponse, LobbyStateResponse, ChallengeMessage, \
    ChallengeAuthMessage
from QRServer.lobby.lobbyclient import LobbyClientHandler

log = logging.getLogger('qr.lobby_server')


class LobbyServer:
    __server_boot_time = datetime.now()
    last_logged: Optional[LobbyClientHandler]
    clients: List[Optional[LobbyClientHandler]]

    def __init__(self):
        self.clients = [None] * 13  # The lobby allows only 13 people at once, last one is kicked
        self.last_logged = None

    async def add_client(self, client: LobbyClientHandler):
        for idx in range(13):
            if not self.clients[idx]:
                self.clients[idx] = client
                # possibly increment total_clients counter
                await self.broadcast_lobby_state(idx)
                return idx
        return -1
        # if no free space either kick someone or deal with it differently

    async def remove_client(self, idx):
        self.last_logged = self.clients[idx]
        self.clients[idx] = None
        await self.broadcast_lobby_state(idx)

    def username_exists(self, username):
        for i in self.clients:
            if i and i.username == username:
                return True
        return False

    def get_players(self) -> List[LobbyPlayer]:
        players = []
        for c in self.clients:
            if c is None:
                players.append(None)
            else:
                players.append(c.get_player())
        return players

    def get_player_count(self) -> int:
        return sum(player is not None for player in self.get_players())

    def get_last_logged(self) -> LastLoggedResponse:
        if self.last_logged:
            return LastLoggedResponse.new(self.last_logged.username, self.last_logged.get_joined_at(), '')
        else:
            return LastLoggedResponse.new('<>', datetime.now(), '')

    async def broadcast_lobby_state(self, excluded_idx):
        # send the current lobby state to all the connected clients (forces refresh) (i hope it does...)
        message = LobbyStateResponse.new(self.get_players())
        for i in range(13):
            if i == excluded_idx:
                continue
            if self.clients[i]:
                await self.clients[i].send_msg(message)
        pass

    async def challenge_user(self, challenger_idx, challenged_idx):
        if self.clients[challenger_idx] and self.clients[challenged_idx]:
            await self.clients[challenged_idx].send_msg(ChallengeMessage.new(challenged_idx, challenger_idx))

    async def setup_challenge(self, challenger_idx, challenged_idx, challenger_auth):
        if self.clients[challenger_idx] and self.clients[challenged_idx]:
            msg = ChallengeAuthMessage.new(challenged_idx, challenger_idx, challenger_auth)
            await self.clients[challenged_idx].send_msg(msg)

    async def broadcast_msg(self, message: ResponseMessage):
        log.debug(f'Broadcasting {message}')
        for client in self.clients:
            if client:
                await client.send_msg(message)

# compare with screenshot
# <S>~<SERVER>~<LAST_LOGGED>~turing guest~33~
# <SERVER>~<RANKING>~1977~3  # idk what this is
# <S>~<SERVER>~<RANKING>~<PRE>
