import asyncio
from enum import Enum
import logging

from typing import Callable
from QRServer.config import Config
from QRServer.game.gameserver import GameServer
from QRServer.lobby.lobbyserver import LobbyServer
from aiohttp import web

log = logging.getLogger('qr.api')


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"


class QrApi:
    app: web.Application
    config: Config
    lobby_server: LobbyServer
    game_server: GameServer

    # TODO we may want to keep audit log of api accesses
    def __init__(self, config: Config, lobby_server: LobbyServer, game_server: GameServer):
        self.config = config
        self.app = web.Application()
        self.lobby_server = lobby_server
        self.game_server = game_server

    async def run(self):
        self._add_routes()

        runner = web.AppRunner(self.app)
        await runner.setup()

        log.info(f'Serving API on {self.config.api_host.get()}:{self.config.api_port.get()}')
        site = web.TCPSite(runner, self.config.api_host.get(), self.config.api_port.get())
        await site.start()

        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            await runner.cleanup()
            raise

    def _add_routes(self):
        self._register_route('/lobby/players', 'GET', self._get_lobby_players)

    def _register_route(self, route: str, method: HTTPMethod, handler: Callable):
        try:
            match method:
                case HTTPMethod.GET:
                    self.app.router.add_get(route, handler)
                case HTTPMethod.POST:
                    self.app.router.add_post(route, handler)
                case _:
                    log.warning(f'Unsupported API method: {method} for route {route} - skipping')
        except RuntimeError:
            log.error(f'Redefinition of route: {route} for method: {method} - skipping')

    def _get_lobby_players(self, _request: web.Request):
        player_username_list = []

        for player in self.lobby_server.get_players():
            if player:
                player_username_list.append(player.username)

        return web.json_response(player_username_list)


# async def handle_hello(request):
#     return web.json_response({"message": "Hello from API"})


# async def start_api_server(config: Config):
    
#     app.router.add_get("/hello", handle_hello)

#     runner = web.AppRunner(app)
#     await runner.setup()

#     site = web.TCPSite(runner, config.host, config.port)
#     await site.start()

#     # Keep this coroutine running until cancelled
#     try:
#         while True:
#             await asyncio.sleep(3600)  # keep alive
#     except asyncio.CancelledError:
#         await runner.cleanup()
#         raise
