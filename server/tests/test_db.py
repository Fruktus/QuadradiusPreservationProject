import unittest
from datetime import datetime
from unittest.mock import patch
from QRServer.common.classes import GameResultHistory
from QRServer.db.connector import DbConnector
from QRServer.db.models import DbMatchReport
from QRServer.common.classes import RankingEntry
from QRServer.common import utils


class DbTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.conn = DbConnector(':memory:')
        await self.conn.connect()

    async def asyncTearDown(self):
        await self.conn.close()

    async def test_get_nonexistent_user(self):
        user = await self.conn.get_user('1234')
        self.assertIsNone(user)

    async def test_get_user_by_username(self):
        with patch('uuid.uuid4') as mock_uuid, \
             patch('QRServer.db.connector.datetime') as mock_datetime:
            mock_uuid.return_value = '1234'
            mock_datetime.now.return_value = datetime(2020, 1, 1, 0, 0, 0)

            await self.conn.authenticate_user(username='test GUEST', password=None, auto_create=True)
            user = await self.conn.get_user_by_username('test GUEST')
            self.assertEqual(user.user_id, '1234')
            self.assertEqual(user.username, 'test GUEST')
            self.assertEqual(user.created_at, datetime(2020, 1, 1, 0, 0, 0).timestamp())
            self.assertTrue(user.is_guest)

    async def test_add_match_results(self):
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = '1'
            winner = await self.conn.authenticate_user('test_user_1', b'password', auto_create=True)

            mock_uuid.return_value = '2'
            loser = await self.conn.authenticate_user('test_user_2', b'password', auto_create=True)

            mock_uuid.return_value = '1234'
            test_match = DbMatchReport(
                winner_id=winner.user_id,
                loser_id=loser.user_id,
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
            self.assertEqual(match.winner_id, winner.user_id)
            self.assertEqual(match.loser_id, loser.user_id)
            self.assertEqual(match.winner_pieces_left, 10)
            self.assertEqual(match.loser_pieces_left, 5)
            self.assertEqual(match.move_counter, 20)
            self.assertEqual(match.grid_size, 'small')
            self.assertEqual(match.squadron_size, 'medium')
            self.assertEqual(match.started_at, datetime(2020, 1, 1, 0, 0, 0))
            self.assertEqual(match.finished_at, datetime(2020, 1, 1, 1, 0, 0))
            self.assertTrue(match.is_ranked)
            self.assertFalse(match.is_void)

            winner = await self.conn.get_user(winner.user_id)
            self.assertEqual(winner.user_id, winner.user_id)
            self.assertEqual(winner.username, 'test_user_1')

            loser = await self.conn.get_user(loser.user_id)
            self.assertEqual(loser.user_id, loser.user_id)
            self.assertEqual(loser.username, 'test_user_2')

    async def test_get_nonexistent_match(self):
        match = await self.conn.get_match('1234')
        self.assertIsNone(match)

    async def test_get_recent_matches(self):
        with patch('uuid.uuid4') as mock_uuid:
            recent_matches = []
            for i in range(1, 16):
                mock_uuid.return_value = str(i)
                winner = await self.conn.authenticate_user(f'test_user_{i}', b'password', auto_create=True)

                mock_uuid.return_value = str(i*100)
                loser = await self.conn.authenticate_user(f'test_user_{i*100}', b'password', auto_create=True)

                mock_uuid.return_value = f'1234{i}'
                test_match = DbMatchReport(
                    winner_id=winner.user_id,
                    loser_id=loser.user_id,
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

    async def test_get_ranking(self):
        with patch('uuid.uuid4') as mock_uuid:
            # Generate 5 matches for user 1 in month 1
            mock_uuid.return_value = '1'
            user1 = await self.conn.authenticate_user('test_user_1', b'password', auto_create=True)
            mock_uuid.return_value = '2'
            user2 = await self.conn.authenticate_user('test_user_2', b'password', auto_create=True)
            mock_uuid.return_value = '3'
            user3 = await self.conn.authenticate_user('test_user_3', b'password', auto_create=True)

            for i in range(1, 6):
                mock_uuid.return_value = f'1{i}'
                test_match = DbMatchReport(
                    winner_id=user1.user_id,
                    loser_id=user2.user_id,
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

            # Generate 10 matches for user 2 in month 1
            for i in range(1, 11):
                mock_uuid.return_value = f'2{i}'
                test_match = DbMatchReport(
                    winner_id=user2.user_id,
                    loser_id=user3.user_id,
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

            # Generate 10 matches for user 2 in month 2
            for i in range(1, 11):
                mock_uuid.return_value = f'3{i}'
                test_match = DbMatchReport(
                    winner_id=user2.user_id,
                    loser_id=user3.user_id,
                    winner_pieces_left=i,
                    loser_pieces_left=20-i,
                    move_counter=20,
                    grid_size='small',
                    squadron_size='medium',
                    started_at=datetime(2020, 2, 1, i, 0, 0),
                    finished_at=datetime(2020, 2, 1, i+1, 0, 0),
                    is_ranked=True,
                    is_void=False,
                )

                await self.conn.add_match_result(test_match)

            # Generate 2 unranked matches
            for i in range(1, 3):
                mock_uuid.return_value = f'4{i}'
                test_match = DbMatchReport(
                    winner_id=user2.user_id,
                    loser_id=user3.user_id,
                    winner_pieces_left=i,
                    loser_pieces_left=20-i,
                    move_counter=20,
                    grid_size='small',
                    squadron_size='medium',
                    started_at=datetime(2020, 1, 1, i, 0, 0),
                    finished_at=datetime(2020, 1, 1, i+1, 0, 0),
                    is_ranked=False,
                    is_void=False,
                )

                await self.conn.add_match_result(test_match)

            # Generate 3 ranked void matches
            for i in range(1, 4):
                mock_uuid.return_value = f'5{i}'
                test_match = DbMatchReport(
                    winner_id=user2.user_id,
                    loser_id=user3.user_id,
                    winner_pieces_left=i,
                    loser_pieces_left=20-i,
                    move_counter=20,
                    grid_size='small',
                    squadron_size='medium',
                    started_at=datetime(2020, 1, 1, i, 0, 0),
                    finished_at=datetime(2020, 1, 1, i+1, 0, 0),
                    is_ranked=True,
                    is_void=True,
                )

                await self.conn.add_match_result(test_match)

            ranking_entries_default = [
                RankingEntry(player='test_user_2', wins=10, games=15),
                RankingEntry(player='test_user_1', wins=5, games=5),
                RankingEntry(player='test_user_3', wins=0, games=10),
            ]

            ranking_entries_unranked = [
                RankingEntry(player='test_user_2', wins=12, games=17),
                RankingEntry(player='test_user_1', wins=5, games=5),
                RankingEntry(player='test_user_3', wins=0, games=12),
            ]

            ranking_entries_void = [
                RankingEntry(player='test_user_2', wins=13, games=18),
                RankingEntry(player='test_user_1', wins=5, games=5),
                RankingEntry(player='test_user_3', wins=0, games=13),
            ]

            ranking_entries_full = [
                RankingEntry(player='test_user_2', wins=15, games=20),
                RankingEntry(player='test_user_1', wins=5, games=5),
                RankingEntry(player='test_user_3', wins=0, games=15),
            ]

            start_date, end_date = utils.make_month_dates(month=1, year=2020)

            self.assertEqual(ranking_entries_default, await self.conn.get_ranking(
                start_date=start_date, end_date=end_date
            ))
            self.assertEqual(ranking_entries_unranked, await self.conn.get_ranking(
                start_date=start_date, end_date=end_date, ranked_only=False
            ))
            self.assertEqual(ranking_entries_void, await self.conn.get_ranking(
                start_date=start_date, end_date=end_date, include_void=True
            ))
            self.assertEqual(ranking_entries_full, await self.conn.get_ranking(
                start_date=start_date, end_date=end_date, include_void=True, ranked_only=False
            ))

    async def test_create_member(self):
        with patch('uuid.uuid4') as mock_uuid, \
             patch('QRServer.db.connector.datetime') as mock_datetime:
            mock_uuid.return_value = '1234'
            mock_datetime.now.return_value = datetime(2020, 1, 1, 0, 0, 0)

            await self.conn.create_member('test_user', b'password', '11111111111')
            user = await self.conn.get_user('1234')

            self.assertEqual(user.user_id, '1234')
            self.assertEqual(user.username, 'test_user')
            self.assertEqual(user.created_at, datetime(2020, 1, 1, 0, 0, 0).timestamp())
            self.assertEqual(user.discord_user_id, '11111111111')
            self.assertFalse(user.is_guest)
