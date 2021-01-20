from QRServer.game import lg


class GameClient:
    def __init__(self, client_socket):
        self.cs = client_socket
        self._run()

    def _run(self):
        while True:
            data = self.cs.recv(2048)
            if not data:
                break
            lg.debug(data)
