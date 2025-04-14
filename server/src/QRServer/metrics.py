from dataclasses import dataclass


# Global variables for the shared instances
_storage_instance = None


@dataclass
class MetricsStorage:
    active_games: int = 0
    lobby_clients: int = 0
    game_clients: int = 0


def get_storage_instance() -> MetricsStorage:
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = MetricsStorage()
    return _storage_instance


class MetricsReporter:
    def __init__(self):
        self.storage = get_storage_instance()

    def active_games_inc(self):
        self.storage.active_games += 1

    def active_games_dec(self):
        self.storage.active_games -= 1

    def lobby_clients_inc(self):
        self.storage.lobby_clients += 1

    def lobby_clients_dec(self):
        self.storage.lobby_clients -= 1

    def game_clients_inc(self):
        self.storage.game_clients += 1

    def game_clients_dec(self):
        self.storage.game_clients -= 1
