import logging
from typing import Dict

from QRServer.common.classes import MatchId, Match, MatchStats
from QRServer.db.connector import connector
from QRServer.game.gameclient import GameClientHandler

log = logging.getLogger('game_server')


class GameServer:
    matches: Dict[MatchId, Match]

    def __init__(self):
        self.matches = {}

    def register_client(self, client_handler: GameClientHandler):
        match_id = client_handler.match_id()
        if match_id not in self.matches:
            self.matches[match_id] = Match(match_id)

        self.matches[match_id].add_party(client_handler)

    def get_player_count(self):
        return len(self.matches) * 2

    async def add_match_stats(self, client_handler: GameClientHandler, stats: MatchStats):
        match_id = client_handler.match_id()
        if match_id not in self.matches:
            return

        match = self.matches[match_id]
        if client_handler.client_id in match.match_stats:
            log.warning(f'User {client_handler.client_id} already sent results for match {match_id}')
            return

        match.add_match_stats(client_handler.client_id, stats)

        if len(self.matches[match_id].match_stats) == 2:
            try:
                report = match.generate_match_report()
                if report:
                    await (await connector()).add_match_result(report)
                    log.debug(f'Added match report {report}')
                else:
                    log.error('Failed to generate report')
            except Exception:
                log.exception(f'Failed to generate report from results {match.match_stats}')

    async def remove_client(self, client: GameClientHandler):
        match_id = client.match_id()
        if match_id in self.matches:
            match = self.matches[match_id]
            match.remove_party(client)
            if match.empty():
                del self.matches[match_id]
