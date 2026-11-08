import asyncio
import logging
from datetime import datetime, timezone

from QRServer.common.classes import PairingId, Match, MatchStats
from QRServer.common.messages import GameChatMessage, Message
from QRServer.db.connector import DbConnector
from QRServer.db.models import DbMatchReport, DbRecordedMessage
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
        self._finishing_tasks: set[asyncio.Task] = set()

    def register_client(self, client_handler: GameClientHandler):
        pairing_id = client_handler.pairing_id()
        if pairing_id not in self.matches:
            self.matches[pairing_id] = Match(pairing_id)

        match = self.matches[pairing_id]
        if match.created:
            # Do not allow reconnects to an already-started match
            raise Exception(
                f'Player {client_handler.username} tried to join, but the match has already started'
            )

        if client_handler.invite_id:
            match.invite_id = client_handler.invite_id
            log.debug(f'Player {client_handler.username} joins an invited {match.invite_id} match {pairing_id}')
        else:
            log.debug(f'Player {client_handler.username} joins a match {pairing_id}')
        match.add_party(client_handler)

    async def set_ready(self, client_handler: GameClientHandler, ready: bool):
        pairing_id = client_handler.pairing_id()
        if pairing_id not in self.matches:
            return
        match = self.matches[pairing_id]

        if ready:
            match.set_ready(client_handler.user_id)
            if match.all_ready() and not match.created:
                match.created = True
                await self.connector.create_match(
                    match.id_, match.start_time,
                    match.parties[0].user_id, match.parties[1].user_id, match.ranked,
                )
                if match.invite_id:
                    await self.connector.use_match_invite(match.invite_id, match.id_)
        else:
            match.set_not_ready(client_handler.user_id)

    def get_player_count(self):
        return len(self.matches) * 2

    def record_message(self, client_handler: GameClientHandler, message: Message):
        try:
            match = self.matches.get(client_handler.pairing_id())
            if match is None or not self._should_record(match, message):
                return

            match.recording.append(DbRecordedMessage(
                timestamp=datetime.now(timezone.utc),
                sender_id=client_handler.user_id,
                receiver_id=client_handler.opponent_id,
                message_type=message.message_type_id,
                message=message.to_data()[:-1],  # strip the trailing null byte
            ))
        except Exception:
            log.exception(f'Failed to record message {message}')

    def _should_record(self, match: Match, message: Message) -> bool:
        if not self.config.recordings_enabled.get():
            return False

        if self.config.recordings_members_only.get() and not match.ranked:
            return False

        if isinstance(message, GameChatMessage) and not self.config.recordings_include_chat.get():
            return False

        return True

    async def _save_recording(self, match: Match):
        if not match.recording:
            return

        try:
            await self.connector.add_match_recording(match.id_, match.recording)
            log.debug(f'Saved recording of match {match.id_} with {len(match.recording)} messages')
        except Exception:
            log.exception(f'Failed to save recording of match {match.id_}')

    async def add_match_stats(self, client_handler: GameClientHandler, stats: MatchStats):
        pairing_id = client_handler.pairing_id()
        if pairing_id not in self.matches:
            return

        match: Match = self.matches[pairing_id]
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
            except Exception:
                log.exception(f'Failed to generate report from results {match.match_stats}')
                return

            if not report:
                log.error('Failed to generate report')
                return

            self.matches.pop(pairing_id, None)

            postmatch_task = asyncio.create_task(self._finish_match(match, report))
            self._finishing_tasks.add(postmatch_task)
            postmatch_task.add_done_callback(self._finishing_tasks.discard)
            # ensure that if client disconnects it doesn't cancel the task mid-run
            await asyncio.shield(postmatch_task)

    async def _finish_match(self, match: Match, report: DbMatchReport):
        try:
            await self.connector.add_match_result(report)
            log.debug(f'Added match report {report}')
            await self._save_recording(match)

            result = await self.connector.get_match_result(report.match_id)
            if result:
                log.info(f'A match has ended; '
                         f'{result.player_won} beat {result.player_lost} '
                         f'{result.won_score}-{result.lost_score}')
                await self.webhook.invoke_webhook_game_ended(result)
        except Exception:
            log.exception(f'Failed to finish match from results {match.match_stats}')

    async def remove_client(self, client: GameClientHandler):
        pairing_id = client.pairing_id()
        if pairing_id not in self.matches:
            return

        match = self.matches[pairing_id]
        if client not in match.parties:
            return  # already cleaned up

        match.remove_party(client)

        if not match.created or match.empty():
            del self.matches[pairing_id]
            return
