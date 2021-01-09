from threading import Lock

from QRServer.lobby.lobbyclient import LobbyClient


class LobbyServer:
    def __init__(self):
        self.clients = [None] * 13  # The lobby allows only 13 people at once, last one is kicked
        self.client_lock = Lock()  # TODO check if this will actually work

    def add_client(self, client: LobbyClient):
        with self.client_lock:
            for idx in range(13):
                if not self.clients[idx]:
                    self.clients[idx] = client
                    # possibly increment total_clients counter
                    break
        # if no free space either kick someone or deal with it differently

    def remove_client(self):
        pass

    def get_clients_string(self):
        return b'<L>' + (''.join([x if x else LobbyClient.get_empty_repr() for x in self.clients])).encode('utf8') + b'\x00'

    def broadcast_chat(self, sender_id):
        pass

    def invite_to_match(self, sender_id, receiver_id):
        pass