from threading import Lock
from typing import Dict

from QRServer.common.classes import MatchId, Match
from QRServer.game.gameclient import GameClientHandler


class GameServer:
    matches: Dict[MatchId, Match]
    _lock: Lock

    def __init__(self):
        self._lock = Lock()
        self.matches = {}

    def register_client(self, client_handler: GameClientHandler):
        match_id = client_handler.match_id()
        with self._lock:
            if match_id not in self.matches:
                self.matches[match_id] = Match(match_id)

            self.matches[match_id].add_party(client_handler)

    def get_player_count(self):
        return len(self.matches) * 2

    def remove_client(self, client: GameClientHandler):
        match_id = client.match_id()
        with self._lock:
            if match_id in self.matches:
                match = self.matches[match_id]
                match.remove_party(client)
                if match.empty():
                    del self.matches[match_id]
