import asyncio
import socket
import unittest
from asyncio import CancelledError
from tempfile import TemporaryDirectory
from typing import Optional, List

from QRServer.__main__ import QRServer
from QRServer.common.messages import Message, RequestMessage, JoinLobbyRequest, LobbyStateResponse, DisconnectRequest
from QRServer.config import Config


class TestClientConnection:
    sock: socket.socket
    messages: asyncio.Queue

    def __init__(self, sock):
        self.sock = sock
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self._receive_messages())
        self.messages = asyncio.Queue()

    def close(self):
        self.sock.close()

    async def send_data(self, data):
        await self.loop.sock_sendall(self.sock, data)

    async def send_message(self, message):
        await self.send_data(message.to_data())

    async def _receive_messages(self):
        loop = asyncio.get_event_loop()
        while self.sock:
            try:
                data = await loop.sock_recv(self.sock, 2048)
            except (ConnectionResetError, CancelledError):
                data = None

            if not data:
                return
            elif data[-1] == 0:
                data = data.split(b'\x00')[:-1]
                for i in data:
                    await self.messages.put(RequestMessage.from_data(i))

    async def receive_message(self) -> Message:
        try:
            return await asyncio.wait_for(self.messages.get(), 1)
        except TimeoutError:
            raise AssertionError('Did not receive a message')

    async def assert_received_message(self, message):
        received = await self.receive_message()
        if message != received:
            raise AssertionError(
                f'Assertion failed\n'
                f'  Expected: {message}\n'
                f'  Received: {received}')

    async def assert_received_message_type(self, type):
        received = await self.receive_message()
        if type != received.__class__:
            raise AssertionError(
                f'Assertion failed\n'
                f'  Expected: {type}\n'
                f'  Received: {received.__class__}')

    async def join_lobby(self, username, password):
        await self.send_message(JoinLobbyRequest.new(username, password))
        await self.assert_received_message_type(LobbyStateResponse)

    async def disconnect(self):
        await self.send_message(DisconnectRequest.new())
        self.close()


class QuadradiusIntegrationTestCase(unittest.IsolatedAsyncioTestCase):
    _data_dir: Optional[TemporaryDirectory]
    _config: Optional[Config]
    _server: Optional[QRServer]
    _clients: List[TestClientConnection]

    def __init__(self, method_name='runTest'):
        super().__init__(method_name)
        self._data_dir = None
        self._config = None
        self._server = None
        self._clients = []

    @property
    def server(self) -> QRServer:
        return self._server

    @property
    def config(self) -> Config:
        return self._config

    async def itSetUpConfig(self, config):
        pass

    async def itSetUp(self):
        pass

    async def itTearDown(self):
        pass

    async def asyncSetUp(self):
        self._data_dir = TemporaryDirectory()

        config = Config()
        config.set('address', '127.0.0.1')
        config.set('port.lobby', 0)
        config.set('port.game', 0)
        config.set('data.dir', self._data_dir.name)
        await self.itSetUpConfig(config)
        self._config = config
        self._server = QRServer(config)
        await self._server.start()
        await self.itSetUp()

    async def asyncTearDown(self):
        try:
            await self.itTearDown()
        finally:
            for client in self._clients:
                client.close()
            await self._server.stop()
            self._data_dir.cleanup()

    async def new_lobby_client(self) -> TestClientConnection:
        client = await self._new_client(self._server.lobby_port)
        self._clients.append(client)
        return client

    async def new_game_client(self) -> TestClientConnection:
        client = await self._new_client(self._server.game_port)
        self._clients.append(client)
        return client

    async def wait_for_empty_lobby(self):
        # TODO maybe there's a nicer way to wait for a given player?
        async def run_until_lobby_not_empty():
            while True:
                clients = self.server.lobby_server.clients
                empty = True
                for i in range(13):
                    if clients[i]:
                        empty = False
                        break

                if empty:
                    return
                else:
                    await asyncio.sleep(0.01)

        await asyncio.wait_for(run_until_lobby_not_empty(), 1)

    async def _new_client(self, port) -> TestClientConnection:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setblocking(False)
        await asyncio.get_event_loop().sock_connect(sock, ('127.0.0.1', port))
        return TestClientConnection(sock)
