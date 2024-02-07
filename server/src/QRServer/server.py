import asyncio
import logging
import signal
import socket
from asyncio import CancelledError
from typing import Coroutine, Optional

from QRServer.config import Config
from QRServer.db.connector import create_connector, DbConnector
from QRServer.discord import logger as discord_logger
from QRServer.game.gameclient import GameClientHandler
from QRServer.game.gameserver import GameServer
from QRServer.lobby.lobbyclient import LobbyClientHandler
from QRServer.lobby.lobbyserver import LobbyServer

log = logging.getLogger('qr.server')


class QRServer:
    config: Config
    connector: Optional[DbConnector] = None
    _tasks = []
    _lobby_clients = []
    _game_clients = []
    _lobby_ready = asyncio.Event()
    _game_ready = asyncio.Event()
    _lobby_port = None
    _game_port = None
    _server_stopped = asyncio.Event()

    def __init__(self, config):
        self.config = config
        self.loop = asyncio.get_event_loop()

    @property
    def tasks(self):
        return self._tasks

    @property
    def lobby_clients(self):
        return self._lobby_clients

    @property
    def game_clients(self):
        return self._game_clients

    @property
    def lobby_port(self):
        return self._lobby_port

    @property
    def game_port(self):
        return self._game_port

    async def start(self):
        self.loop.add_signal_handler(signal.SIGINT, self.stop_sync)
        self.loop.add_signal_handler(signal.SIGTERM, self.stop_sync)

        await self.setup_connector()
        self.start_tasks()
        await asyncio.gather(
            self._lobby_ready.wait(),
            self._game_ready.wait())

    async def run(self):
        await self.start()
        await self._server_stopped.wait()

    async def setup_connector(self):
        self.connector = await create_connector(self.config)

    async def stop(self):
        log.info('Terminating...')
        # stop in reversed order
        for task in reversed(self._tasks):
            log.debug(f'Canceling task "{task.get_name()}"...')
            task.cancel()
            await task
        await self.connector.close()
        self._server_stopped.set()

    def stop_sync(self):
        self.loop.create_task(self.stop())

    def start_task(self, name: str, task: Coroutine):
        self._tasks.append(self.loop.create_task(task, name=name))

    def start_tasks(self):
        self.start_task("Discord Logger", discord_logger.get_daemon_task(self.config))
        game_server = GameServer(self.config, self.connector)
        lobby_server = LobbyServer()
        self.start_task("Game Listener", self._game_listener_task(self.config, self.connector, game_server))
        self.start_task("Lobby Listener", self._lobby_listener_task(self.config, self.connector, lobby_server))

    async def _lobby_listener_task(self, config, connector, lobby_server):
        async def handler(client_socket):
            client = LobbyClientHandler(config, connector, client_socket, lobby_server)
            await client.run()

        await self._listen_for_connections(config.lobby_port.get(), handler, True)

    async def _game_listener_task(self, config, connector, game_server):
        async def handler(client_socket):
            client = GameClientHandler(config, connector, client_socket, game_server)
            await client.run()

        await self._listen_for_connections(config.game_port.get(), handler, False)

    async def _listen_for_connections(self, conn_port, handler, is_lobby):
        conn_host = self.config.address.get()

        if is_lobby:
            log.info(f'Lobby starting on {conn_host}:{conn_port}')
        else:
            log.info(f'Game starting on {conn_host}:{conn_port}')

        clients = self._lobby_clients if is_lobby else self._game_clients
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((conn_host, conn_port))
            server.listen(5)
            server.setblocking(False)
            host, port = server.getsockname()

            if is_lobby:
                self._lobby_port = port
                log.info(f'Lobby started on {host}:{port}')
                self._lobby_ready.set()
            else:
                self._game_port = port
                log.info(f'Game started on {host}:{port}')
                self._game_ready.set()

            loop = asyncio.get_event_loop()
            try:
                while True:
                    client_socket, _ = await loop.sock_accept(server)
                    clients.append(loop.create_task(handler(client_socket)))
            except (KeyboardInterrupt, CancelledError):
                for client in clients:
                    client.cancel()
                server.shutdown(1)
                server.close()
        await asyncio.gather(*clients)
