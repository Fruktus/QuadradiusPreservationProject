import logging

from QRServer.common.classes import PairingId, Match, MatchStats
from QRServer.db.connector import DbConnector
from QRServer.discord.webhook import Webhook
from QRServer.game.gameclient import GameClientHandler

log = logging.getLogger('qr.game_server')


class GameServer:
    matches: dict[PairingId, Match]

    def __init__(self, config, connector: DbConnector):
        self.config = config
        self.connector: DbConnector = connector
        self.webhook = Webhook(config)
        self.matches = {}

    async def register_client(self, client_handler: GameClientHandler):
        pairing_id = client_handler.pairing_id()
        if pairing_id not in self.matches:
            self.matches[pairing_id] = Match(pairing_id)

        match = self.matches[pairing_id]

        log.debug(f'Player {client_handler.username} joins a match {pairing_id}')
        match.add_party(client_handler)
        if len(match.parties) == 2:
            await self.connector.create_match(
                match.id_, match.start_time, match.parties[0].user_id, match.parties[1].user_id, match.ranked
            )

    def get_player_count(self):
        return len(self.matches) * 2

    async def add_match_stats(self, client_handler: GameClientHandler, stats: MatchStats):
        pairing_id = client_handler.pairing_id()
        if pairing_id not in self.matches:
            return

        match = self.matches[pairing_id]
        if client_handler.user_id in match.match_stats:
            log.warning(f'User {client_handler.username} already sent results for match {pairing_id}')
            return

        match.add_match_stats(client_handler.user_id, stats)

        if len(self.matches[pairing_id].match_stats) == 2 or not self.matches[pairing_id].full():
            # If there are two stats, they can be submitted without problems.
            # If the match is not full, it means the opponent has left
            # and there won't be a second stat, so we should only send this one.
            # It can occur due do disconnect (when players closes window without clicking quit).
            try:
                report = match.generate_match_report()
                if report:
                    await self.connector.add_match_result(report)
                    log.debug(f'Added match report {report}')
                    result = await self.connector.get_match_result(report.match_id)
                    if result:
                        log.info(f'A match has ended; '
                                 f'{result.player_won} beat {result.player_lost} '
                                 f'{result.won_score}-{result.lost_score}')
                        await self.webhook.invoke_webhook_game_ended(result)
                else:
                    log.error('Failed to generate report')
            except Exception:
                log.exception(f'Failed to generate report from results {match.match_stats}')

    async def remove_client(self, client: GameClientHandler):
        pairing_id = client.pairing_id()
        if pairing_id in self.matches:
            match = self.matches[pairing_id]
            match.remove_party(client)
            if match.empty():
                del self.matches[pairing_id]
