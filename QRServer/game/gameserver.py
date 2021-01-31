from threading import Lock


class GameServer:
    def __init__(self):
        self._lock = Lock()

        self.clients = {}

    def register_client(self, client):
        with self._lock:
            if not frozenset({client.own_username, client.opponent_username}) in self.clients:
                self.clients[frozenset({client.own_username, client.opponent_username})] = [client]
            else:
                present_client = self.clients[frozenset({client.own_username, client.opponent_username})][0]
                present_client.out_socket = client.cs
                client.out_socket = present_client.cs
                self.clients[frozenset({client.own_username, client.opponent_username})].append(client)

    def get_client_socket(self, opponent_username):  # should I check all other parameters as well?
        with self._lock:
            if self.clients.get(opponent_username):
                return self.clients.get(opponent_username).get_socket()
            return None

    def get_player_count(self, user1, user2):
        if frozenset({user1, user2}) in self.clients:
            return len(self.clients[frozenset({user1, user2})])

    def remove_client(self, client):
        with self._lock:
            if frozenset({client.own_username, client.opponent_username}) in self.clients:
                try:
                    self.clients[frozenset({client.own_username, client.opponent_username})].remove(client)
                    # FIXME if last client, delete key
                except Exception:
                    pass
                # TODO possibly should tell the other player that opponent left
