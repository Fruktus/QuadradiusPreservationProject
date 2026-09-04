from datetime import datetime, timezone
import unittest
from unittest.mock import patch

from QRServer.common.classes import MatchStats, PairingId
from QRServer.config import Config
from QRServer.db.connector import DbConnector
from QRServer.game.gameserver import GameServer


class MockedParty:
    def __init__(self, user_id, username, opponent_id):
        self.user_id = user_id
        self.username = username
        self.opponent_id = opponent_id
        self.is_guest = False
        self.is_void_score = False

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
            await self.game_server.register_client(user_1)
            await self.game_server.register_client(user_2)

        self.assertEqual(len(self.game_server.matches), 1)
        match = next(iter(self.game_server.matches.values()))
        self.assertTrue(match.full())

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
