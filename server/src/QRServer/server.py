import asyncio
import logging
import signal
from asyncio import Task, Server, StreamReader, StreamWriter, CancelledError
from typing import Coroutine

from QRServer.common.clienthandler import ClientHandler
from QRServer.config import Config
from QRServer.db.connector import create_connector, DbConnector
from QRServer.discord import logger as discord_logger
from QRServer.discord.bot import DiscordBot
from QRServer.game.gameclient import GameClientHandler
from QRServer.game.gameserver import GameServer
from QRServer.lobby.lobbyclient import LobbyClientHandler
from QRServer.lobby.lobbyserver import LobbyServer

log = logging.getLogger('qr.server')


class QRServer:
    config: Config
    connector: DbConnector | None
    _tasks: list[Task]

    # servers
    _lobby_sock_server: Server
    _game_sock_server: Server
    _game_server: GameServer
    _lobby_server: LobbyServer

    # events
    _lobby_ready: asyncio.Event
    _game_ready: asyncio.Event
    _server_stopped: asyncio.Event

    # extensions
    _discord_bot: DiscordBot | None

    def __init__(self, config):
        self.config = config
        self.connector = None
        self.loop = asyncio.get_event_loop()
        self._tasks = []
        self._lobby_ready = asyncio.Event()
        self._game_ready = asyncio.Event()
        self._lobby_port = None
        self._game_port = None
        self._server_stopped = asyncio.Event()

    @property
    def tasks(self):
        return self._tasks

    @property
    def lobby_socks(self):
        return self._lobby_sock_server.sockets

    @property
    def game_socks(self):
        return self._game_sock_server.sockets

    @property
    def game_server(self):
        return self._game_server

    @property
    def lobby_server(self):
        return self._lobby_server

    async def start(self):
        try:
            self.loop.add_signal_handler(signal.SIGINT, self.stop_sync)
            self.loop.add_signal_handler(signal.SIGTERM, self.stop_sync)
        except NotImplementedError:
            # Windows
            signal.signal(signal.SIGINT, self.stop_sync)
            signal.signal(signal.SIGTERM, self.stop_sync)

        await self.setup_connector()
        await self.start_tasks()
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
            try:
                await task
            except CancelledError:
                pass
            except Exception as e:
                log.exception(f'Error while canceling task "{task.get_name()}": {e}')
        self._lobby_sock_server.close()
        self._game_sock_server.close()
        await self._lobby_sock_server.wait_closed()
        await self._game_sock_server.wait_closed()
        await self.connector.close()
        self._server_stopped.set()

    def stop_sync(self, *args):
        self.loop.create_task(self.stop())

    def start_task(self, name: str, task: Coroutine):
        task = self.loop.create_task(task, name=name)
        self._tasks.append(task)

        async def task_remover():
            await task
            log.debug(f'Task "{task.get_name()}" finished')
            self._tasks.remove(task)

        self.loop.create_task(task_remover())
        log.debug(f'Task "{task.get_name()}" started')

    async def start_tasks(self):
        self.start_task("Discord Logger", discord_logger.get_daemon_task(self.config))
        self.start_task("Cron Logger", self._cron_logger())

        if self.config.discord_bot_enabled.get():
            self._discord_bot = DiscordBot(self.config, self.connector)
            self.start_task("Discord Bot", self._discord_bot.run_bot())

        self._game_server = GameServer(self.config, self.connector)
        self._lobby_server = LobbyServer()
        await self._game_listener_task(self.config, self.connector, self._game_server)
        await self._lobby_listener_task(self.config, self.connector, self._lobby_server)

    async def _lobby_listener_task(self, config, connector, lobby_server):
        def handler_factory(reader, writer):
            return LobbyClientHandler(config, connector, reader, writer, lobby_server)

        try:
            await self._listen_for_connections(config.lobby_port.get(), handler_factory, True)
        except Exception:
            log.exception('Failed setting up the server')
            await self.stop()

    async def _game_listener_task(self, config, connector, game_server):
        def handler_factory(reader, writer):
            return GameClientHandler(config, connector, reader, writer, game_server)

        try:
            await self._listen_for_connections(config.game_port.get(), handler_factory, False)
        except Exception:
            log.exception('Failed setting up the server')
            await self.stop()

    async def _listen_for_connections(self, conn_port, handler_factory, is_lobby):
        conn_host = self.config.address.get()

        if is_lobby:
            log.info(f'Lobby starting on {conn_host}:{conn_port}')
        else:
            log.info(f'Game starting on {conn_host}:{conn_port}')

        def handle_client(reader: StreamReader, writer: StreamWriter):
            handler: ClientHandler = handler_factory(reader, writer)
            addr = writer.get_extra_info('peername')
            name = f'Lobby client {addr}' if is_lobby else f'Game client {addr}'
            self.start_task(name, handler.run())

        server = await asyncio.start_server(handle_client, conn_host, conn_port)
        if is_lobby:
            self._lobby_sock_server = server
        else:
            self._game_sock_server = server

        for sock in server.sockets:
            host, port, *_ = sock.getsockname()
            if is_lobby:
                log.info(f'Lobby started on {host}:{port}')
                self._lobby_ready.set()
            else:
                log.info(f'Game started on {host}:{port}')
                self._game_ready.set()

        await server.start_serving()

    async def _cron_logger(self):
        delay = self.config.log_cron_delay.get()
        if delay == 0:
            log.debug('Cron logger disabled')
            return
        log.debug(f'Running cron logger with delay of {delay} seconds')
        while True:
            await asyncio.sleep(delay)
            lobby_count = self.lobby_server.get_player_count()
            game_count = self.game_server.get_player_count()
            if lobby_count > 0 or game_count > 0:
                log.info(f'There are currently {lobby_count} players in the lobby, '
                         f'and {game_count} players playing')
