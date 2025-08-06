import asyncio
import unittest
from asyncio import CancelledError, QueueEmpty, StreamWriter, StreamReader, IncompleteReadError
from tempfile import TemporaryDirectory

from QRServer.__main__ import QRServer
from QRServer.common.messages import Message, JoinLobbyRequest, LobbyStateResponse, DisconnectRequest
from QRServer.config import Config
from QRServer.db import password as db_password

# this significantly improves performance
# we do not need to worry about security
db_password._iterations = 100


class TestClientConnection:
    reader: StreamReader
    writer: StreamWriter
    messages: asyncio.Queue
    connection_closed: asyncio.Event

    def __init__(self, server, reader, writer):
        self.server = server
        self.reader = reader
        self.writer = writer
        self.username = None
        self.loop = asyncio.get_event_loop()
        self.loop.create_task(self._receive_messages())
        self.messages = asyncio.Queue()
        self.connection_closed = asyncio.Event()

    async def close(self):
        self.writer.close()
        await self.writer.wait_closed()

    async def send_data(self, data):
        self.writer.write(data)
        await self.writer.drain()

    async def send_message(self, message):
        await self.send_data(message.to_data())

    async def _receive_messages(self):
        while True:
            try:
                data = await self.reader.readuntil(b'\x00')
            except (ConnectionResetError, CancelledError, IncompleteReadError):
                data = None

            if not data:
                self.connection_closed.set()
                return
            elif data[-1] == 0:
                data = data.split(b'\x00')[:-1]
                for i in data:
                    await self.messages.put(Message.from_data(i))

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

    async def assert_no_more_messages(self):
        try:
            message = self.messages.get_nowait()
            raise AssertionError(f'Expected no more message, but there is one: {message}')
        except QueueEmpty:
            return

    async def assert_connection_closed(self):
        try:
            return await asyncio.wait_for(self.connection_closed.wait(), 1)
        except TimeoutError:
            raise AssertionError('Connection was not closed')

    async def join_lobby_guest(self, username):
        username += ' GUEST'
        self.username = username
        await self.send_message(JoinLobbyRequest.new(username, '24f380279d84e2e715f80ed14b1db063'))
        await self.assert_received_message_type(LobbyStateResponse)

    async def join_lobby(self, username, password):
        self.username = username
        await self.send_message(JoinLobbyRequest.new(username, password))
        await self.assert_received_message_type(LobbyStateResponse)

    async def disconnect(self):
        await self.send_message(DisconnectRequest.new())
        await self.close()

    async def wait_for_disconnect(self):
        async def run():
            while True:
                clients = self.server.lobby_server.clients
                exists = False
                for i in range(13):
                    if clients[i] and clients[i].username == self.username:
                        exists = True
                        break

                if not exists:
                    return
                else:
                    await asyncio.sleep(0.01)

        await asyncio.wait_for(run(), 1)

    async def disconnect_and_wait(self):
        await self.disconnect()
        await self.wait_for_disconnect()


class QuadradiusIntegrationTestCase(unittest.IsolatedAsyncioTestCase):
    _data_dir: TemporaryDirectory | None
    _config: Config | None
    _server: QRServer | None
    _clients: list[TestClientConnection]

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
                await client.close()
            await self._server.stop()
            self._data_dir.cleanup()

    async def new_lobby_client(self) -> TestClientConnection:
        host, port, *_ = self._server.lobby_socks[0].getsockname()
        client = await self._new_client(host, port)
        self._clients.append(client)
        return client

    async def new_game_client(self) -> TestClientConnection:
        host, port, *_ = self._server.game_socks[0].getsockname()
        client = await self._new_client(host, port)
        self._clients.append(client)
        return client

    async def _new_client(self, host, port) -> TestClientConnection:
        reader, writer = await asyncio.open_connection(host, port)
        return TestClientConnection(self.server, reader, writer)
