from typing import List, Tuple
import unittest
from datetime import datetime
from unittest.mock import patch
from QRServer.common.classes import GameResultHistory
from QRServer.db import migrations
from QRServer.db.connector import DbConnector
from QRServer.db.models import DbMatchReport
from QRServer.common.classes import RankingEntry
from QRServer.common import utils
from QRServer.config import Config


class DbTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.conn = DbConnector(':memory:', Config())
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

            ranking = await self.conn.get_ranking(
                start_date=datetime(2020, 1, 1, 0, 0, 0),
                end_date=datetime(2020, 1, 2, 0, 0, 0))
            self.assertEqual(len(ranking), 2)
            self.assertEqual(ranking[0].username, 'test_user_1')
            self.assertEqual(ranking[0].user_id, '1')
            self.assertEqual(ranking[0].wins, 1)
            self.assertEqual(ranking[0].games, 1)
            self.assertEqual(ranking[1].username, 'test_user_2')
            self.assertEqual(ranking[1].user_id, '2')
            self.assertEqual(ranking[1].wins, 0)
            self.assertEqual(ranking[1].games, 1)

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
            # Set up 4 users
            mock_uuid.return_value = '0'
            user0 = await self.conn.authenticate_user('test_user_0', b'password', auto_create=True)
            mock_uuid.return_value = '1'
            user1 = await self.conn.authenticate_user('test_user_1', b'password', auto_create=True)
            mock_uuid.return_value = '2'
            user2 = await self.conn.authenticate_user('test_user_2', b'password', auto_create=True)
            mock_uuid.return_value = '3'
            user3 = await self.conn.authenticate_user('test_user_3', b'password', auto_create=True)

            # Generate 7 matches for user 1 in month 1
            for i in range(1, 8):
                mock_uuid.return_value = f'0{i}'
                test_match = DbMatchReport(
                    winner_id=user0.user_id,
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

            # Generate 5 matches for user 1 in month 1
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

            # Generate 2 unranked matches in month 1
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

            ranking_entries = [
                RankingEntry(username='test_user_0', user_id='0', wins=7, games=7),
                RankingEntry(username='test_user_1', user_id='1', wins=5, games=5),
                RankingEntry(username='test_user_2', user_id='2', wins=10, games=22),
                RankingEntry(username='test_user_3', user_id='3', wins=0, games=10),
            ]
            start_date, end_date = utils.make_month_dates(month=1, year=2020)

            self.assertEqual(ranking_entries, await self.conn.get_ranking(
                start_date=start_date, end_date=end_date
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


class DbMigrationTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        import aiosqlite

        self.dbconn = DbConnector(':memory:', Config())
        # manually initialize the dbconn to avoid executing migrations
        self.dbconn.conn = await aiosqlite.connect(':memory:', autocommit=False)
        c = await self.dbconn.conn.cursor()
        await migrations.setup_metadata(c)
        await self.dbconn.conn.commit()
        self.c = await self.dbconn.conn.cursor()

    async def asyncTearDown(self):
        await self.dbconn.conn.close()

    async def get_table_names(self) -> List[str]:
        # Utility to pull the names of the existing tables
        # Flattens them to list of strings from tuples
        await self.c.execute("select name from sqlite_master where type='table';")
        tables = await self.c.fetchall()
        return [i[0] for i in tables]

    async def get_table_info(self, table_name: str) -> List[Tuple]:
        await self.c.execute(f'pragma table_info(\'{table_name}\')')
        return await self.c.fetchall()

    async def test_migration_v1(self):
        self.assertNotIn('users', await self.get_table_names())

        await migrations.execute_migrations(self.c, self.dbconn.config, 1)

        self.assertIn('users', await self.get_table_names())
        table_info = await self.get_table_info('users')

        self.assertEqual(len(table_info), 3)
        self.assertEqual(table_info[0][:3], (0, 'id', 'varchar'))
        self.assertEqual(table_info[1][:3], (1, 'username', 'varchar'))
        self.assertEqual(table_info[2][:3], (2, 'password', 'varchar'))

    async def test_migration_v2(self):
        await migrations.execute_migrations(self.c, self.dbconn.config, 1)

        table_info = await self.get_table_info('users')
        self.assertEqual(len(table_info), 3)

        await migrations.execute_migrations(self.c, self.dbconn.config, 2)

        table_info = await self.get_table_info('users')
        self.assertEqual(len(table_info), 4)
        self.assertEqual(table_info[3][:3], (3, 'comment', 'varchar'))

    async def test_migration_v3(self):
        await migrations.execute_migrations(self.c, self.dbconn.config, 2)

        self.assertNotIn('matches', await self.get_table_names())

        await migrations.execute_migrations(self.c, self.dbconn.config, 3)

        self.assertIn('matches', await self.get_table_names())
        table_info = await self.get_table_info('matches')
        self.assertEqual(len(table_info), 12)
        self.assertEqual(table_info[0][:3], (0, 'id', 'varchar'))
        self.assertEqual(table_info[1][:3], (1, 'winner_id', 'varchar'))
        self.assertEqual(table_info[2][:3], (2, 'loser_id', 'varchar'))
        self.assertEqual(table_info[3][:3], (3, 'winner_pieces_left', 'INTEGER'))
        self.assertEqual(table_info[4][:3], (4, 'loser_pieces_left', 'INTEGER'))
        self.assertEqual(table_info[5][:3], (5, 'move_counter', 'INTEGER'))
        self.assertEqual(table_info[6][:3], (6, 'grid_size', 'varchar'))
        self.assertEqual(table_info[7][:3], (7, 'squadron_size', 'varchar'))
        self.assertEqual(table_info[8][:3], (8, 'started_at', 'INTEGER'))
        self.assertEqual(table_info[9][:3], (9, 'finished_at', 'INTEGER'))
        self.assertEqual(table_info[10][:3], (10, 'is_ranked', 'INTEGER'))
        self.assertEqual(table_info[11][:3], (11, 'is_void', 'INTEGER'))

    async def test_migration_v4(self):
        await migrations.execute_migrations(self.c, self.dbconn.config, 3)

        table_info = await self.get_table_info('users')
        self.assertEqual(len(table_info), 4)

        await migrations.execute_migrations(self.c, self.dbconn.config, 4)

        table_info = await self.get_table_info('users')
        self.assertEqual(len(table_info), 5)
        self.assertEqual(table_info[4][:3], (4, 'created_at', 'INTEGER'))

    async def test_migration_v5(self):
        await migrations.execute_migrations(self.c, self.dbconn.config, 4)

        table_info = await self.get_table_info('users')
        self.assertEqual(len(table_info), 5)

        await migrations.execute_migrations(self.c, self.dbconn.config, 5)

        table_info = await self.get_table_info('users')
        self.assertEqual(len(table_info), 6)
        self.assertEqual(table_info[5][:3], (5, 'discord_user_id', 'varchar'))

    async def test_migration_v6(self):
        await migrations.execute_migrations(self.c, self.dbconn.config, 5)

        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = '1'
            winner = await self.dbconn.authenticate_user('test_user_1', b'password', auto_create=True)

            mock_uuid.return_value = '2'
            loser = await self.dbconn.authenticate_user('test_user_2', b'password', auto_create=True)

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
            await self.c.execute(
                "insert into matches ("
                "  id,"
                "  winner_id,"
                "  loser_id,"
                "  winner_pieces_left,"
                "  loser_pieces_left,"
                "  move_counter,"
                "  grid_size,"
                "  squadron_size,"
                "  started_at,"
                "  finished_at,"
                "  is_ranked,"
                "  is_void"
                ") values ("
                "?, ?, ?, ?, ?, ?,"
                "?, ?, ?, ?, ?, ?"
                ")", (
                    test_match.match_id,
                    test_match.winner_id,
                    test_match.loser_id,
                    test_match.winner_pieces_left,
                    test_match.loser_pieces_left,
                    test_match.move_counter,
                    test_match.grid_size,
                    test_match.squadron_size,
                    test_match.started_at.timestamp(),
                    test_match.finished_at.timestamp(),
                    test_match.is_ranked,
                    test_match.is_void
                )
            )

            await self.dbconn.conn.commit()

        self.assertNotIn('rankings', await self.get_table_names())

        await migrations.execute_migrations(self.c, self.dbconn.config, 6)

        self.assertIn('rankings', await self.get_table_names())
        table_info = await self.get_table_info('rankings')
        self.assertEqual(len(table_info), 6)
        self.assertEqual(table_info[0][:3], (0, 'year', 'INTEGER'))
        self.assertEqual(table_info[1][:3], (1, 'month', 'INTEGER'))
        self.assertEqual(table_info[2][:3], (2, 'position', 'INTEGER'))
        self.assertEqual(table_info[3][:3], (3, 'user_id', 'varchar'))
        self.assertEqual(table_info[4][:3], (4, 'wins', 'INTEGER'))
        self.assertEqual(table_info[5][:3], (5, 'total_games', 'INTEGER'))

        # TODO self.get_ranking, compare
        await self.c.execute('select * from rankings')
        ranking_data = await self.c.fetchall()
        self.assertEqual(len(ranking_data), 2)
        self.assertEqual(ranking_data[0], (2020, 1, 1, '1', 1, 1))
        self.assertEqual(ranking_data[1], (2020, 1, 2, '2', 0, 1))
