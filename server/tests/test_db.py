import unittest
from datetime import datetime
from unittest.mock import patch
from QRServer.common.classes import GameResultHistory
from QRServer.db.connector import DbConnector
from QRServer.db.models import DbMatchReport
from QRServer.db.password import password_hash


class DbTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.conn = DbConnector(':memory:')
        await self.conn.connect()

    async def asyncTearDown(self):
        await self.conn.close()

    async def test_add_member(self):
        with patch('uuid.uuid4') as mock_uuid, \
             patch('QRServer.db.connector.datetime') as mock_datetime, \
             patch('QRServer.db.password.os.urandom') as mock_urandom:
            mock_urandom.return_value = b'1234'
            mock_uuid.return_value = '1234'
            mock_datetime.now.return_value = datetime(2020, 1, 1, 0, 0, 0)

            user_id = await self.conn.add_member('test', b'password')
            user = await self.conn.get_user(user_id)
            self.assertEqual(user.user_id, '1234')
            self.assertEqual(user.username, 'test')
            self.assertEqual(user.password, password_hash(b'password'))
            self.assertEqual(user.created_at, datetime(2020, 1, 1, 0, 0, 0).timestamp())
            self.assertFalse(user.is_guest)

    async def test_add_guest(self):
        with patch('uuid.uuid4') as mock_uuid, \
             patch('QRServer.db.connector.datetime') as mock_datetime:
            mock_uuid.return_value = '1234'
            mock_datetime.now.return_value = datetime(2020, 1, 1, 0, 0, 0)

            user_id = await self.conn.add_guest('test GUEST')
            user = await self.conn.get_user(user_id)
            self.assertEqual(user.user_id, '1234')
            self.assertEqual(user.username, 'test GUEST')
            self.assertEqual(user.created_at, datetime(2020, 1, 1, 0, 0, 0).timestamp())
            self.assertTrue(user.is_guest)

    async def test_get_nonexistent_user(self):
        user = await self.conn.get_user('1234')
        self.assertIsNone(user)

    async def test_get_user_by_username(self):
        with patch('uuid.uuid4') as mock_uuid, \
             patch('QRServer.db.connector.datetime') as mock_datetime:
            mock_uuid.return_value = '1234'
            mock_datetime.now.return_value = datetime(2020, 1, 1, 0, 0, 0)

            await self.conn.add_guest('test GUEST')
            user = await self.conn.get_user_by_username('test GUEST')
            self.assertEqual(user.user_id, '1234')
            self.assertEqual(user.username, 'test GUEST')
            self.assertEqual(user.created_at, datetime(2020, 1, 1, 0, 0, 0).timestamp())
            self.assertTrue(user.is_guest)

    async def test_add_match_results(self):
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = '1'
            winner_id = await self.conn.add_member('test_user_1', b'password')

            mock_uuid.return_value = '2'
            loser_id = await self.conn.add_member('test_user_2', b'password')

            mock_uuid.return_value = '1234'
            test_match = DbMatchReport(
                winner_id=winner_id,
                loser_id=loser_id,
                winner_pieces_left=10,
                loser_pieces_left=5,
                move_counter=20,
                grid_size='small',
                squadron_size='medium',
                started_at=datetime(2020, 1, 1, 0, 0, 0),
                finished_at=datetime(2020, 1, 1, 1, 0, 0),
                is_ranked=True,
                is_void=False,
            )

            await self.conn.add_match_result(test_match)
            match = await self.conn.get_match(test_match.match_id)

            self.assertEqual(match.match_id, '1234')
            self.assertEqual(match.winner_id, winner_id)
            self.assertEqual(match.loser_id, loser_id)
            self.assertEqual(match.winner_pieces_left, 10)
            self.assertEqual(match.loser_pieces_left, 5)
            self.assertEqual(match.move_counter, 20)
            self.assertEqual(match.grid_size, 'small')
            self.assertEqual(match.squadron_size, 'medium')
            self.assertEqual(match.started_at, datetime(2020, 1, 1, 0, 0, 0))
            self.assertEqual(match.finished_at, datetime(2020, 1, 1, 1, 0, 0))
            self.assertTrue(match.is_ranked)
            self.assertFalse(match.is_void)

            winner = await self.conn.get_user(winner_id)
            self.assertEqual(winner.user_id, winner_id)
            self.assertEqual(winner.username, 'test_user_1')

            loser = await self.conn.get_user(loser_id)
            self.assertEqual(loser.user_id, loser_id)
            self.assertEqual(loser.username, 'test_user_2')

    async def test_get_nonexistent_match(self):
        match = await self.conn.get_match('1234')
        self.assertIsNone(match)

    async def test_get_recent_matches(self):
        with patch('uuid.uuid4') as mock_uuid:
            recent_matches = []
            for i in range(1, 16):
                mock_uuid.return_value = str(i)
                winner_id = await self.conn.add_member(f'test_user_{i}', b'password')

                mock_uuid.return_value = str(i*100)
                loser_id = await self.conn.add_member(f'test_user_{i*100}', b'password')

                mock_uuid.return_value = f'1234{i}'
                test_match = DbMatchReport(
                    winner_id=winner_id,
                    loser_id=loser_id,
                    winner_pieces_left=i,
                    loser_pieces_left=20-i,
                    move_counter=20,
                    grid_size='small',
                    squadron_size='medium',
                    started_at=datetime(2020, 1, 1, i, 0, 0),
                    finished_at=datetime(2020, 1, 1, i+1, 0, 0),
                    is_ranked=True,
                    is_void=False,
                )

                await self.conn.add_match_result(test_match)
                recent_matches.append(
                    GameResultHistory(
                        player_won=f'test_user_{i}',
                        player_lost=f'test_user_{i*100}',
                        won_score=i,
                        lost_score=20-i,
                        start=datetime(2020, 1, 1, i, 0, 0),
                        finish=datetime(2020, 1, 1, i+1, 0, 0),
                        moves=20,
                    )
                )

            recent_matches.reverse()

            matches = await self.conn.get_recent_matches()

            self.assertEqual(len(matches), len(recent_matches))
            for i in range(len(matches)):
                self.assertEqual(matches[i].player_won, recent_matches[i].player_won)
                self.assertEqual(matches[i].player_lost, recent_matches[i].player_lost)
                self.assertEqual(matches[i].won_score, recent_matches[i].won_score)
                self.assertEqual(matches[i].lost_score, recent_matches[i].lost_score)
                self.assertEqual(matches[i].start, recent_matches[i].start)
                self.assertEqual(matches[i].finish, recent_matches[i].finish)
