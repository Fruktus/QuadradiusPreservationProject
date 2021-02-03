from threading import Lock
from time import time
from typing import Optional, List

from QRServer.lobby.lobbyclient import LobbyClientHandler


class LobbyServer:
    clients: List[Optional[LobbyClientHandler]]

    def __init__(self):
        self.clients = [None] * 13  # The lobby allows only 13 people at once, last one is kicked
        self._lock = Lock()
        self.last_logged = None

    def add_client(self, client: LobbyClientHandler):
        with self._lock:
            for idx in range(13):
                if not self.clients[idx]:
                    self.clients[idx] = client
                    # possibly increment total_clients counter
                    self.broadcast_lobby_state(idx)
                    return idx
            return -1
        # if no free space either kick someone or deal with it differently

    def remove_client(self, idx):
        self.last_logged = self.clients[idx]
        self.clients[idx] = None
        self.broadcast_lobby_state(idx)

    def username_exists(self, username):
        for i in self.clients:
            if i and i.username == username:
                return True
        return False

    def get_clients_string(self):
        """returns byte string describing current lobby state"""
        return b'<L>' + (''.join([x.get_repr() if x else LobbyClientHandler.get_empty_repr()
                                  for x in self.clients])).encode('utf8') + b'\x00'

    def get_last_logged(self):
        if self.last_logged:
            return b'<S>~<SERVER>~<LAST_LOGGED>~' + \
                   self.last_logged.username.encode('utf8') + \
                   b'~' + \
                   str(int((time() - self.last_logged.joined_at)/60)).encode('utf8') + \
                   b'~\x00'
        else:
            return b'<S>~<SERVER>~<LAST_LOGGED>~<>~0~\x00'

    def broadcast_lobby_state(self, excluded_idx):
        # send the current lobby state to all the connected clients (forces refresh) (i hope it does...)
        for i in range(13):
            if i == excluded_idx:
                continue
            if self.clients[i]:
                # self.clients[i].get_queue().put(self.get_clients_string())
                self.clients[i].send(self.get_clients_string())
        pass

    def challenge_user(self, challenger_idx, challenged_idx):
        if self.clients[challenger_idx] and self.clients[challenged_idx]:
            self.clients[challenger_idx].send(
                b'<S>~' + str(challenger_idx).encode('utf8') +
                b'~' + str(challenged_idx).encode('utf8') +
                b'~<SHALLWEPLAYAGAME?>\x00')

    def setup_challenge(self, challenger_idx, challenged_idx, challenger_auth):
        if self.clients[challenger_idx] and self.clients[challenged_idx]:
            self.clients[challenger_idx].send(
                b'<S>~' + str(challenger_idx).encode('utf8') +
                b'~' + str(challenged_idx).encode('utf8') +
                b'~<AUTHENTICATION>~' + str(challenger_auth).encode('utf8') +
                b'\x00')

    def broadcast_chat(self, message):
        for client in self.clients:
            if client:
                client.cs.send(message)

# compare with screenshot
# <S>~<SERVER>~<LAST_LOGGED>~turing guest~33~
# <SERVER>~<RANKING>~1977~3  # idk what this is
# <S>~<SERVER>~<RANKING>~<PRE>
