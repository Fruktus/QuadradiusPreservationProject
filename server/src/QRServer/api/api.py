import asyncio
from collections import defaultdict
from enum import Enum
import logging

from QRServer.config import Config
from QRServer.db.connector import DbConnector
from QRServer.db.models import DbUser, Tournament, TournamentDuel, TournamentMatch
from QRServer.game.gameserver import GameServer
from QRServer.lobby.lobbyserver import LobbyServer
from aiohttp import web

log = logging.getLogger('qr.api')

_routes = web.RouteTableDef()


class HttpMethod(str, Enum):
    GET = "GET"
    POST = "POST"


class ApiServer:
    app: web.Application
    runner: web.AppRunner
    site: web.TCPSite
    config: Config
    connector: DbConnector
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
        self.app.add_routes([
            web.get('/api/v1/game/stats', self._v1_game_stats),
            web.get('/api/v1/health', self._v1_health),
            web.get('/api/v1/lobby/stats', self._v1_lobby_stats),
            web.get('/api/v1/tournaments/{id}', self._v1_tournaments),
            web.get('/api/v1/tournaments/{id}/duels', self._v1_tournament_duels),
            web.get('/api/v1/tournaments/{id}/matches', self._v1_tournament_matches),
            web.get('/api/v1/tournaments/{id}/users', self._v1_tournament_users),
        ])

    async def _v1_game_stats(self, _request: web.Request) -> web.Response:
        player_count = self.game_server.get_player_count()
        return web.json_response({
            'player_count': player_count,
        })

    async def _v1_health(self, _request: web.Request) -> web.Response:
        return web.json_response({})

    async def _v1_lobby_stats(self, _request: web.Request):
        player_count = self.lobby_server.get_player_count()
        return web.json_response({
            'player_count': player_count,
        })

    async def _v1_tournament_users(self, request) -> web.Response:
        tournament_id = request.match_info['id']
        users: list[DbUser] | None = await self.connector.list_tournament_users(tournament_id)

        if users is None:
            return web.json_response(data=None, status=404)

        users_view: list[object] = []

        for user in users:
            user_view = {
                'id': user.user_id,
                'username': user.username,
            }
            users_view.append(user_view)
        return web.json_response(data={'users': users_view}, status=200)

    async def _v1_tournaments(self, request) -> web.Response:
        tournament_id = request.match_info['id']
        tournament: Tournament | None = await self.connector.get_tournament(tournament_id)
        if not tournament:
            return web.json_response(data=None, status=404)

        tournament_view = {
            'id': tournament.tournament_id,
            'name': tournament.name,
            'required_matches_per_duel': tournament.required_matches_per_duel,
            'created_at': tournament.created_at.isoformat(),
            'started_at': tournament.started_at.isoformat() if tournament.started_at else None,
            'finished_at': tournament.finished_at.isoformat() if tournament.finished_at else None,
        }
        return web.json_response(data={'tournament': tournament_view}, status=200)

    async def _v1_tournament_duels(self, request) -> web.Response:
        tournament_id = request.match_info['id']
        duels: list[TournamentDuel] | None = await self.connector.list_duels(tournament_id)

        if duels is None:
            return web.json_response(data=None, status=404)

        duels_view: list[object] = []
        for duel in duels:
            duel_view = {
                'idx': duel.duel_idx,
                'active_until': duel.active_until.isoformat(),
                'user1_id': duel.user1_id,
                'user2_id': duel.user2_id,
            }
            duels_view.append(duel_view)

        return web.json_response(data={'duels': duels_view}, status=200)

    async def _v1_tournament_matches(self, request) -> web.Response:
        tournament_id = request.match_info['id']
        tournament_matches: list[TournamentMatch] | None = await self.connector.list_tournament_matches(tournament_id)

        if tournament_matches is None:
            return web.json_response(data=None, status=404)

        duel_matches_view: dict[int, list] = defaultdict(list)
        for tournament_match in tournament_matches:
            duel_match_view = {
                'match': {
                    'id': tournament_match.match.match_id,
                    'winner_id': tournament_match.match.winner_id,
                    'loser_id': tournament_match.match.loser_id,
                    'winner_pieces_left': tournament_match.match.winner_pieces_left,
                    'loser_pieces_left': tournament_match.match.loser_pieces_left,
                    'started_at': tournament_match.match.started_at.isoformat(),
                    'finished_at': tournament_match.match.finished_at.isoformat(),
                    'is_ranked': tournament_match.match.is_ranked,
                    'is_void': tournament_match.match.is_void,
                },
                'duel_idx': tournament_match.duel_idx
            }
            duel_matches_view[tournament_match.duel_idx].append(duel_match_view)

        return web.json_response(data={'matches': duel_matches_view}, status=200)
