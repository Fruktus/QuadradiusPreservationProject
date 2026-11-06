import asyncio
from datetime import datetime, timezone
import unittest
from unittest.mock import patch

from QRServer.common.classes import MatchStats, PairingId
from QRServer.common.messages import GameChatMessage, GrabPieceMessage, SettingsReadyOnMessage, SwitchPlayerMessage, \
    VoidScoreResponse
from QRServer.config import Config
from QRServer.db.connector import DbConnector
from QRServer.db.models import DbRecordedMessage
from QRServer.game.gameserver import GameServer


class MockedParty:
    def __init__(self, user_id, username, opponent_id, invite_id=None, is_guest=False):
        self.user_id = user_id
        self.username = username
        self.opponent_id = opponent_id
        self.is_guest = is_guest
        self.is_void_score = False
        self.invite_id = invite_id

    def pairing_id(self):
        return PairingId(self.user_id, self.opponent_id)

    def match_opponent(self, opponent):
        pass

    def unmatch_opponent(self):
        pass


class GameServerTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.conn = DbConnector(':memory:', Config())
        await self.conn.connect()
        self.game_server = GameServer(Config(), self.conn)

    async def asyncTearDown(self):
        await self.conn.close()

    async def test_two_players_match_and_submit_stats(self):
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = '1'
            winner = await self.conn.authenticate_user('test_user_1', b'password', auto_create=True)

            mock_uuid.return_value = '2'
            loser = await self.conn.authenticate_user('test_user_2', b'password', auto_create=True)

        # ensure that there are no recorded matches at this point
        async with self.conn._transaction('r') as c:
            await c.execute('select * from matches')
            rows = await c.fetchall()
            self.assertEqual(len(rows), 0)

            await c.execute('select * from match_results')
            rows = await c.fetchall()
            self.assertEqual(len(rows), 0)

        user_1 = MockedParty(user_id=winner.user_id, username='test_user_1', opponent_id=loser.user_id)
        user_2 = MockedParty(user_id=loser.user_id, username='test_user_2', opponent_id=winner.user_id)

        with patch('uuid.uuid4') as mock_uuid, \
             patch('QRServer.common.classes.datetime') as mock_datetime:
            mock_uuid.return_value = '1234'
            mock_datetime.now.return_value = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
            self.game_server.register_client(user_1)
            self.game_server.register_client(user_2)

        self.assertEqual(len(self.game_server.matches), 1)
        match = next(iter(self.game_server.matches.values()))
        self.assertTrue(match.full())

        self.assertFalse(match.all_ready())
        await self.game_server.set_ready(user_1, True)
        await self.game_server.set_ready(user_2, True)
        self.assertTrue(match.all_ready())

        async with self.conn._transaction('r') as c:
            await c.execute(
                'select id, user_1_id, user_2_id, is_ranked, started_at from matches')
            rows = await c.fetchall()
            self.assertEqual(len(rows), 1)
            row = rows[0]
            self.assertEqual(row[0], '1234')
            self.assertEqual(row[1], '1')
            self.assertEqual(row[2], '2')
            self.assertEqual(row[3], True)
            self.assertEqual(row[4], int(datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp()))

            await c.execute('select * from match_results')
            rows = await c.fetchall()
            self.assertEqual(len(rows), 0)

        await self.game_server.add_match_stats(
            user_1, MatchStats(own_piece_count=6, opponent_piece_count=2,
                               cycle_counter=40, grid_size='medium', squadron_size='medium'))
        await self.game_server.add_match_stats(
            user_2, MatchStats(own_piece_count=2, opponent_piece_count=6,
                               cycle_counter=35, grid_size='medium', squadron_size='medium'))

        result = await self.conn.get_match_result(match.id_)

        self.assertEqual(result.player_won, 'test_user_1')
        self.assertEqual(result.player_lost, 'test_user_2')
        self.assertEqual(result.won_score, 6)
        self.assertEqual(result.lost_score, 2)
        self.assertEqual(result.moves, 40)

    async def test_invite_match_marks_invite_as_used_on_ready(self):
        challenger = await self.conn.authenticate_user('challenger', b'password', auto_create=True)
        challenged = await self.conn.authenticate_user('challenged', b'password', auto_create=True)

        invite_id = '52b750dd-eeb4-45f8-a922-66d7359be987'
        tmp_pass_1 = 'fe97cf3f-0160-41b2-88e4-4952727b8efd'
        tmp_pass_2 = '88b14654-9d5b-4df0-a9d7-26ab59586f4f'

        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.side_effect = [invite_id, tmp_pass_1, tmp_pass_2]
            created = await self.conn.create_match_invite(challenger.user_id, challenged.user_id)
            self.assertTrue(created)

        invite = await self.conn.get_match_invite(invite_id)
        self.assertIsNotNone(invite)
        self.assertFalse(invite.is_used)
        self.assertIsNone(invite.match_id)

        party_1 = MockedParty(user_id=challenger.user_id, username='challenger',
                              opponent_id=challenged.user_id, invite_id=invite.invite_id)
        party_2 = MockedParty(user_id=challenged.user_id, username='challenged',
                              opponent_id=challenger.user_id, invite_id=invite.invite_id)

        self.game_server.register_client(party_1)
        self.game_server.register_client(party_2)

        match = next(iter(self.game_server.matches.values()))
        self.assertEqual(match.invite_id, invite.invite_id)

        await self.game_server.set_ready(party_1, True)
        # Only one party ready: invite must still be untouched.
        still_unused = await self.conn.get_match_invite(invite.invite_id)
        self.assertFalse(still_unused.is_used)

        await self.game_server.set_ready(party_2, True)

        used_invite = await self.conn.get_match_invite(invite.invite_id)
        self.assertTrue(used_invite.is_used)
        self.assertEqual(used_invite.match_id, match.id_)


class GameServerRecordingTest(unittest.IsolatedAsyncioTestCase):
    STATS_WINNER = MatchStats(own_piece_count=6, opponent_piece_count=2,
                              cycle_counter=40, grid_size='medium', squadron_size='medium')
    STATS_LOSER = MatchStats(own_piece_count=2, opponent_piece_count=6,
                             cycle_counter=35, grid_size='medium', squadron_size='medium')

    async def asyncSetUp(self):
        self.conn = DbConnector(':memory:', Config())
        await self.conn.connect()
        self.game_server = GameServer(Config(), self.conn)

        user_1 = await self.conn.authenticate_user('test_user_1', b'password', auto_create=True)
        user_2 = await self.conn.authenticate_user('test_user_2', b'password', auto_create=True)
        self.user_1_id = user_1.user_id
        self.user_2_id = user_2.user_id

    async def asyncTearDown(self):
        await self.conn.close()

    async def _start_match(self, user_2_is_guest=False):
        party_1 = MockedParty(user_id=self.user_1_id, username='test_user_1', opponent_id=self.user_2_id)
        party_2 = MockedParty(user_id=self.user_2_id, username='test_user_2', opponent_id=self.user_1_id,
                              is_guest=user_2_is_guest)
        self.game_server.register_client(party_1)
        self.game_server.register_client(party_2)
        await self.game_server.set_ready(party_1, True)
        await self.game_server.set_ready(party_2, True)
        match = next(iter(self.game_server.matches.values()))
        return party_1, party_2, match

    async def _finish_match(self, party_1, party_2):
        await self.game_server.add_match_stats(party_1, self.STATS_WINNER)
        await self.game_server.add_match_stats(party_2, self.STATS_LOSER)

    async def test_recording_is_saved_with_match_result(self):
        party_1, party_2, match = await self._start_match()

        with patch('QRServer.game.gameserver.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2020, 1, 1, 0, 0, 1, tzinfo=timezone.utc)
            self.game_server.record_message(party_1, SettingsReadyOnMessage.new(10, 2, 1, '0000FF'))
            mock_datetime.now.return_value = datetime(2020, 1, 1, 0, 0, 2, tzinfo=timezone.utc)
            self.game_server.record_message(party_1, GrabPieceMessage.new(3))
            mock_datetime.now.return_value = datetime(2020, 1, 1, 0, 0, 3, tzinfo=timezone.utc)
            self.game_server.record_message(party_2, SwitchPlayerMessage.new(3))

        # nothing is persisted until the match result is
        self.assertEqual(await self.conn.get_match_recording(match.id_), [])

        await self._finish_match(party_1, party_2)

        self.assertEqual(await self.conn.get_match_recording(match.id_), [
            DbRecordedMessage(
                timestamp=datetime(2020, 1, 1, 0, 0, 1, tzinfo=timezone.utc),
                sender_id=self.user_1_id,
                receiver_id=self.user_2_id,
                message_type=SettingsReadyOnMessage.message_type_id,
                message=b'<S>~<SETTINGS>~<READY_ON>~10~2~1~0000FF',
            ),
            DbRecordedMessage(
                timestamp=datetime(2020, 1, 1, 0, 0, 2, tzinfo=timezone.utc),
                sender_id=self.user_1_id,
                receiver_id=self.user_2_id,
                message_type=GrabPieceMessage.message_type_id,
                message=b'<S>~<GRAB_PIECE>~3',
            ),
            DbRecordedMessage(
                timestamp=datetime(2020, 1, 1, 0, 0, 3, tzinfo=timezone.utc),
                sender_id=self.user_2_id,
                receiver_id=self.user_1_id,
                message_type=SwitchPlayerMessage.message_type_id,
                message=b'<S>~<SWITCH_PLAYER>~3',
            ),
        ])

    async def test_nothing_is_recorded_when_recordings_disabled(self):
        self.game_server.config.set('recordings.enabled', False)
        party_1, party_2, match = await self._start_match()

        self.game_server.record_message(party_1, GrabPieceMessage.new(3))
        self.assertEqual(match.recording, [])

        await self._finish_match(party_1, party_2)

        self.assertIsNotNone(await self.conn.get_match(match.id_))
        self.assertEqual(await self.conn.get_match_recording(match.id_), [])

    async def test_one_sided_void_is_recorded(self):
        party_1, party_2, match = await self._start_match()

        self.game_server.record_message(party_1, GrabPieceMessage.new(3))
        self.game_server.record_message(party_2, VoidScoreResponse.new())
        party_2.is_void_score = True
        await self._finish_match(party_1, party_2)

        recording = await self.conn.get_match_recording(match.id_)
        self.assertEqual(
            [m.message_type for m in recording],
            [GrabPieceMessage.message_type_id, VoidScoreResponse.message_type_id])
        self.assertEqual(recording[1].sender_id, self.user_2_id)
        self.assertEqual(recording[1].receiver_id, self.user_1_id)

    async def test_void_match_recording_is_saved(self):
        party_1, party_2, match = await self._start_match()

        self.game_server.record_message(party_1, GrabPieceMessage.new(3))
        party_1.is_void_score = True
        party_2.is_void_score = True
        await self._finish_match(party_1, party_2)

        result = await self.conn.get_match(match.id_)
        self.assertTrue(result.is_void)
        recording = await self.conn.get_match_recording(match.id_)
        self.assertEqual(len(recording), 1)
        self.assertEqual(recording[0].message, b'<S>~<GRAB_PIECE>~3')

    async def test_recording_is_not_saved_without_messages(self):
        party_1, party_2, match = await self._start_match()

        await self._finish_match(party_1, party_2)

        self.assertIsNotNone(await self.conn.get_match(match.id_))
        async with self.conn._transaction('r') as c:
            await c.execute('select * from match_recordings')
            self.assertEqual(len(await c.fetchall()), 0)

    async def test_chat_is_not_recorded_by_default(self):
        party_1, party_2, match = await self._start_match()

        self.game_server.record_message(party_1, GrabPieceMessage.new(3))
        self.game_server.record_message(party_1, GameChatMessage.new('hello'))
        self.game_server.record_message(party_2, SwitchPlayerMessage.new(3))
        await self._finish_match(party_1, party_2)

        recording = await self.conn.get_match_recording(match.id_)
        self.assertEqual(
            [m.message_type for m in recording],
            [GrabPieceMessage.message_type_id, SwitchPlayerMessage.message_type_id])

    async def test_chat_is_recorded_when_enabled(self):
        self.game_server.config.set('recordings.include_chat', True)
        party_1, party_2, match = await self._start_match()

        self.game_server.record_message(party_1, GrabPieceMessage.new(3))
        self.game_server.record_message(party_1, GameChatMessage.new('hello'))
        await self._finish_match(party_1, party_2)

        recording = await self.conn.get_match_recording(match.id_)
        self.assertEqual(
            [m.message_type for m in recording],
            [GrabPieceMessage.message_type_id, GameChatMessage.message_type_id])
        self.assertEqual(recording[1].message, b'<S>~<CHAT>~hello')

    async def test_match_with_guest_is_not_recorded_by_default(self):
        party_1, party_2, match = await self._start_match(user_2_is_guest=True)
        self.assertFalse(match.ranked)

        self.game_server.record_message(party_1, GrabPieceMessage.new(3))
        await self._finish_match(party_1, party_2)

        self.assertIsNotNone(await self.conn.get_match(match.id_))
        self.assertEqual(await self.conn.get_match_recording(match.id_), [])

    async def test_match_with_guest_is_recorded_when_members_only_disabled(self):
        self.game_server.config.set('recordings.members_only', False)
        party_1, party_2, match = await self._start_match(user_2_is_guest=True)
        self.assertFalse(match.ranked)

        self.game_server.record_message(party_1, GrabPieceMessage.new(3))
        await self._finish_match(party_1, party_2)

        recording = await self.conn.get_match_recording(match.id_)
        self.assertEqual(len(recording), 1)
        self.assertEqual(recording[0].message, b'<S>~<GRAB_PIECE>~3')

    async def test_member_match_is_recorded_when_members_only_disabled(self):
        self.game_server.config.set('recordings.members_only', False)
        party_1, party_2, match = await self._start_match()

        self.game_server.record_message(party_1, GrabPieceMessage.new(3))
        await self._finish_match(party_1, party_2)

        self.assertEqual(len(await self.conn.get_match_recording(match.id_)), 1)

    async def test_recording_is_saved_when_opponent_left_before_stats(self):
        party_1, party_2, match = await self._start_match()

        self.game_server.record_message(party_1, GrabPieceMessage.new(3))
        await self.game_server.remove_client(party_2)
        await self.game_server.add_match_stats(party_1, self.STATS_WINNER)

        self.assertEqual(len(await self.conn.get_match_recording(match.id_)), 1)

    async def test_recording_failure_does_not_break_match_result(self):
        party_1, party_2, match = await self._start_match()

        self.game_server.record_message(party_1, GrabPieceMessage.new(3))
        with patch.object(self.conn, 'add_match_recording', side_effect=Exception('boom')):
            await self._finish_match(party_1, party_2)

        result = await self.conn.get_match_result(match.id_)
        self.assertEqual(result.player_won, 'test_user_1')
        self.assertEqual(await self.conn.get_match_recording(match.id_), [])
        self.assertNotIn(match.pairing_id, self.game_server.matches)

    async def test_record_message_failure_does_not_raise(self):
        party_1, party_2, match = await self._start_match()

        with patch.object(self.game_server, '_should_record', side_effect=Exception('boom')):
            self.game_server.record_message(party_1, GrabPieceMessage.new(3))

        self.assertEqual(match.recording, [])

    async def test_record_message_for_unknown_match_is_ignored(self):
        party_1 = MockedParty(user_id=self.user_1_id, username='test_user_1', opponent_id=self.user_2_id)

        self.game_server.record_message(party_1, GrabPieceMessage.new(3))

        self.assertEqual(len(self.game_server.matches), 0)

    async def test_match_is_finished_when_handler_cancelled(self):
        party_1, party_2, match = await self._start_match()
        self.game_server.record_message(party_1, GrabPieceMessage.new(3))
        await self.game_server.add_match_stats(party_1, self.STATS_WINNER)

        handler = asyncio.create_task(self.game_server.add_match_stats(party_2, self.STATS_LOSER))
        await asyncio.sleep(0)  # handler runs up to the shield
        handler.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await handler
        await asyncio.gather(*self.game_server._finishing_tasks)

        self.assertIsNotNone(await self.conn.get_match_result(match.id_))
        self.assertEqual(len(await self.conn.get_match_recording(match.id_)), 1)
        self.assertNotIn(match.pairing_id, self.game_server.matches)
