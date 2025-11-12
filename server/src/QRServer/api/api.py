import asyncio
from enum import Enum
import logging

from QRServer.config import Config
from QRServer.db.connector import DbConnector
from QRServer.game.gameserver import GameServer
from QRServer.lobby.lobbyserver import LobbyServer
from QRServer.api.api_v1 import create_v1_app
from aiohttp import web

log = logging.getLogger('qr.api')

_routes = web.RouteTableDef()


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"


class ApiServer:
    app: web.Application
    connector: DbConnector
    runner: web.AppRunner
    site: web.TCPSite
    config: Config
    lobby_server: LobbyServer
    game_server: GameServer

    def __init__(self, config: Config, connector: DbConnector, lobby_server: LobbyServer, game_server: GameServer):
        self.config = config
        self.connector = connector
        self.app = web.Application()
        self.lobby_server = lobby_server
        self.game_server = game_server
        self.runner = web.AppRunner(self.app)

    def api_socks(self):
        if self.site:
            return self.site._server.sockets
        else:
            return None

    async def run(self):
        self._add_routes()

        await self.runner.setup()

        host = self.config.address.get()
        port = self.config.api_port.get()
        log.info(f'Serving API on {host}:{port}')
        self.site = web.TCPSite(self.runner, host, port)
        await self.site.start()

        try:
            while True:
                await asyncio.sleep(3600)
        finally:
            await self.runner.cleanup()

    def _add_routes(self):
        self.app.add_subapp('/api/v1', create_v1_app(self.game_server, self.lobby_server))
