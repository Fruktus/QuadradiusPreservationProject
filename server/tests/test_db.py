import unittest
from datetime import datetime, timezone
from unittest.mock import patch
import uuid
from QRServer.common.classes import GameResultHistory
from QRServer.db import migrations
from QRServer.db.common import UpdateCollisionError
from QRServer.db.connector import DbConnector
from QRServer.db.models import DbMatchReport, Tournament, TournamentParticipant
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
            mock_datetime.now.return_value = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

            await self.conn.authenticate_user(username='test GUEST', password=None, auto_create=True)
            user = await self.conn.get_user_by_username('test GUEST')
            self.assertEqual(user.user_id, '1234')
            self.assertEqual(user.username, 'test GUEST')
            self.assertEqual(user.created_at, datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp())
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
                started_at=datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                finished_at=datetime(2020, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
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
            self.assertEqual(match.started_at, datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc))
            self.assertEqual(match.finished_at, datetime(2020, 1, 1, 1, 0, 0, tzinfo=timezone.utc))
            self.assertTrue(match.is_ranked)
            self.assertFalse(match.is_void)

            winner = await self.conn.get_user(winner.user_id)
            self.assertEqual(winner.user_id, winner.user_id)
            self.assertEqual(winner.username, 'test_user_1')

            loser = await self.conn.get_user(loser.user_id)
            self.assertEqual(loser.user_id, loser.user_id)
            self.assertEqual(loser.username, 'test_user_2')

            ranking = await self.conn.get_ranking(
                start_date=datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
                end_date=datetime(2020, 1, 2, 0, 0, 0, tzinfo=timezone.utc))
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
                    started_at=datetime(2020, 1, 1, i, 0, 0, tzinfo=timezone.utc),
                    finished_at=datetime(2020, 1, 1, i+1, 0, 0, tzinfo=timezone.utc),
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
                        start=datetime(2020, 1, 1, i, 0, 0, tzinfo=timezone.utc),
                        finish=datetime(2020, 1, 1, i+1, 0, 0, tzinfo=timezone.utc),
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
                    started_at=datetime(2020, 1, 1, i, 0, 0, tzinfo=timezone.utc),
                    finished_at=datetime(2020, 1, 1, i+1, 0, 0, tzinfo=timezone.utc),
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
                    started_at=datetime(2020, 1, 1, i, 0, 0, tzinfo=timezone.utc),
                    finished_at=datetime(2020, 1, 1, i+1, 0, 0, tzinfo=timezone.utc),
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
                    started_at=datetime(2020, 1, 1, i, 0, 0, tzinfo=timezone.utc),
                    finished_at=datetime(2020, 1, 1, i+1, 0, 0, tzinfo=timezone.utc),
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
                    started_at=datetime(2020, 2, 1, i, 0, 0, tzinfo=timezone.utc),
                    finished_at=datetime(2020, 2, 1, i+1, 0, 0, tzinfo=timezone.utc),
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
                    started_at=datetime(2020, 1, 1, i, 0, 0, tzinfo=timezone.utc),
                    finished_at=datetime(2020, 1, 1, i+1, 0, 0, tzinfo=timezone.utc),
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
                    started_at=datetime(2020, 1, 1, i, 0, 0, tzinfo=timezone.utc),
                    finished_at=datetime(2020, 1, 1, i+1, 0, 0, tzinfo=timezone.utc),
                    is_ranked=True,
                    is_void=True,
                )

                await self.conn.add_match_result(test_match)

            ranking_entries = [
                RankingEntry(username='test_user_0', user_id='0', wins=7, games=7, rating=640),
                RankingEntry(username='test_user_1', user_id='1', wins=5, games=5, rating=575),
                RankingEntry(username='test_user_2', user_id='2', wins=10, games=22, rating=538),
                RankingEntry(username='test_user_3', user_id='3', wins=0, games=10, rating=247),
            ]

            start_date, end_date = utils.make_month_dates(month=1, year=2020)

            self.assertEqual(ranking_entries, await self.conn.get_ranking(
                start_date=start_date, end_date=end_date
            ))

    async def test_get_ranking_elo(self):
        # Test to check if the difference between playing against the same vs different players
        # is noticeable
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

            # Generate 2 matches for user_2 (winner) vs user_3 (loser)
            for i in range(1, 3):
                mock_uuid.return_value = f'1{i}'
                test_match = DbMatchReport(
                    winner_id=user2.user_id,
                    loser_id=user3.user_id,
                    winner_pieces_left=i,
                    loser_pieces_left=20-i,
                    move_counter=20,
                    grid_size='small',
                    squadron_size='medium',
                    started_at=datetime(2020, 1, 1, i, 0, 0, tzinfo=timezone.utc),
                    finished_at=datetime(2020, 1, 1, i+1, 0, 0, tzinfo=timezone.utc),
                    is_ranked=True,
                    is_void=False,
                )

                await self.conn.add_match_result(test_match)

            # Generate 2 matches for user_2 (winner) vs user_1 (loser)
            for i in range(1, 3):
                mock_uuid.return_value = f'2{i}'
                test_match = DbMatchReport(
                    winner_id=user2.user_id,
                    loser_id=user1.user_id,
                    winner_pieces_left=i,
                    loser_pieces_left=20-i,
                    move_counter=20,
                    grid_size='small',
                    squadron_size='medium',
                    started_at=datetime(2020, 1, 1, i, 0, 0, tzinfo=timezone.utc),
                    finished_at=datetime(2020, 1, 1, i+1, 0, 0, tzinfo=timezone.utc),
                    is_ranked=True,
                    is_void=False,
                )

                await self.conn.add_match_result(test_match)

            # Generate 5 matches for user_0 (winner) vs user_1 (loser) - user_1 lost some rating on user_2
            for i in range(1, 6):
                mock_uuid.return_value = f'0{i}'
                test_match = DbMatchReport(
                    winner_id=user0.user_id,
                    loser_id=user1.user_id,
                    winner_pieces_left=i,
                    loser_pieces_left=20-i,
                    move_counter=20,
                    grid_size='small',
                    squadron_size='medium',
                    started_at=datetime(2020, 1, 1, i, 0, 0, tzinfo=timezone.utc),
                    finished_at=datetime(2020, 1, 1, i+1, 0, 0, tzinfo=timezone.utc),
                    is_ranked=True,
                    is_void=False,
                )

                await self.conn.add_match_result(test_match)

            # user_2 played less games than user_1,
            # but played against different players, therefore should have higher rating
            ranking_entries_default = [
                RankingEntry(user_id='2', username='test_user_2', wins=4, games=4, rating=607),
                RankingEntry(user_id='0', username='test_user_0', wins=5, games=5, rating=600),
                RankingEntry(user_id='3', username='test_user_3', wins=0, games=2, rating=442),
                RankingEntry(user_id='1', username='test_user_1', wins=0, games=7, rating=351),
            ]

            start_date, end_date = utils.make_month_dates(month=1, year=2020)

            self.assertEqual(ranking_entries_default, await self.conn.get_ranking(
                start_date=start_date, end_date=end_date
            ))

    async def test_create_member(self):
        with patch('uuid.uuid4') as mock_uuid, \
             patch('QRServer.db.connector.datetime') as mock_datetime:
            mock_uuid.return_value = '1234'
            mock_datetime.now.return_value = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

            await self.conn.create_member('test_user', b'password', '11111111111')
            user = await self.conn.get_user('1234')

            self.assertEqual(user.user_id, '1234')
            self.assertEqual(user.username, 'test_user')
            self.assertEqual(user.created_at, datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc).timestamp())
            self.assertEqual(user.discord_user_id, '11111111111')
            self.assertFalse(user.is_guest)

    async def test_update_rating_rollback(self):
        # Forces collision (update during other update) to test if rollback will work

        with patch('uuid.uuid4') as mock_uuid:
            # Set up 4 users
            mock_uuid.return_value = '0'
            winner = await self.conn.authenticate_user('test_user_0', b'password', auto_create=True)
            mock_uuid.return_value = '1'
            loser = await self.conn.authenticate_user('test_user_1', b'password', auto_create=True)

            # This helper will be executed every time when update_user_rating rungs
            # This will cause the outer call to fail (but the helper will succeed)
            # so with 3 retries we should see 3 updates (revision 2 - counting from 0)
            async def perform_conflicting_update():
                await self.conn.update_users_rating(winner.user_id, loser.user_id, 4, 2025)

            # Try and update user rating - if every retry fails this will raise exception
            collision_detected = False
            try:
                await self.conn.update_users_rating(winner.user_id, loser.user_id, 4, 2025, perform_conflicting_update)
            except UpdateCollisionError:
                collision_detected = True

            self.assertTrue(collision_detected)

            winner_rating = await self.conn.get_user_rating(winner.user_id, 4, 2025)
            loser_rating = await self.conn.get_user_rating(loser.user_id, 4, 2025)

            self.assertEqual(winner_rating.year, 2025)
            self.assertEqual(winner_rating.month, 4)
            self.assertEqual(winner_rating.rating, 580)
            self.assertEqual(winner_rating.revision, 2)  # updated 3 times -> revision == 2

            self.assertEqual(loser_rating.year, 2025)
            self.assertEqual(loser_rating.month, 4)
            self.assertEqual(loser_rating.rating, 420)
            self.assertEqual(loser_rating.revision, 2)  # updated 3 times -> revision == 2


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

    async def get_table_names(self) -> list[str]:
        # Utility to pull the names of the existing tables
        # Flattens them to list of strings from tuples
        await self.c.execute("select name from sqlite_master where type='table';")
        tables = await self.c.fetchall()
        return [i[0] for i in tables]

    async def get_table_info(self, table_name: str) -> list[tuple]:
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

    async def test_migration_v7(self):
        await migrations.execute_migrations(self.c, self.dbconn.config, 6)

        self.assertNotIn('user_ratings', await self.get_table_names())

        await migrations.execute_migrations(self.c, self.dbconn.config, 7)

        self.assertIn('user_ratings', await self.get_table_names())

        table_info = await self.get_table_info('user_ratings')
        self.assertEqual(len(table_info), 5)
        self.assertEqual(table_info[0][:3], (0, 'user_id', 'varchar'))
        self.assertEqual(table_info[1][:3], (1, 'year', 'INTEGER'))
        self.assertEqual(table_info[2][:3], (2, 'month', 'INTEGER'))
        self.assertEqual(table_info[3][:3], (3, 'revision', 'INTEGER'))
        self.assertEqual(table_info[4][:3], (4, 'rating', 'INTEGER'))

    async def test_migration_v8(self):
        await migrations.execute_migrations(self.c, self.dbconn.config, 7)

        table_names = await self.get_table_names()
        self.assertNotIn('tournaments', table_names)
        self.assertNotIn('tournament_participants', table_names)
        self.assertNotIn('tournament_duels', table_names)
        self.assertNotIn('tournament_matches', table_names)

        await migrations.execute_migrations(self.c, self.dbconn.config, 8)

        table_names = await self.get_table_names()
        self.assertIn('tournaments', table_names)
        self.assertIn('tournament_participants', table_names)
        self.assertIn('tournament_duels', table_names)
        self.assertIn('tournament_matches', table_names)

        table_info = await self.get_table_info('tournaments')
        self.assertEqual(len(table_info), 8)
        self.assertEqual(table_info[0][:3], (0, 'id', 'varchar'))
        self.assertEqual(table_info[1][:3], (1, 'name', 'varchar'))
        self.assertEqual(table_info[2][:3], (2, 'created_by_dc_id', 'varchar'))
        self.assertEqual(table_info[3][:3], (3, 'tournament_msg_dc_id', 'varchar'))
        self.assertEqual(table_info[4][:3], (4, 'required_matches_per_duel', 'INTEGER'))
        self.assertEqual(table_info[5][:3], (5, 'created_at', 'INTEGER'))
        self.assertEqual(table_info[6][:3], (6, 'started_at', 'INTEGER'))
        self.assertEqual(table_info[7][:3], (7, 'finished_at', 'INTEGER'))

        table_info = await self.get_table_info('tournament_participants')
        self.assertEqual(len(table_info), 2)
        self.assertEqual(table_info[0][:3], (0, 'tournament_id', 'varchar'))
        self.assertEqual(table_info[1][:3], (1, 'user_id', 'varchar'))

        table_info = await self.get_table_info('tournament_duels')
        self.assertEqual(len(table_info), 5)
        self.assertEqual(table_info[0][:3], (0, 'tournament_id', 'varchar'))
        self.assertEqual(table_info[1][:3], (1, 'duel_idx', 'INTEGER'))
        self.assertEqual(table_info[2][:3], (2, 'active_until', 'INTEGER'))
        self.assertEqual(table_info[3][:3], (3, 'user1_id', 'varchar'))
        self.assertEqual(table_info[4][:3], (4, 'user2_id', 'varchar'))

        table_info = await self.get_table_info('tournament_matches')
        self.assertEqual(len(table_info), 3)
        self.assertEqual(table_info[0][:3], (0, 'tournament_id', 'varchar'))
        self.assertEqual(table_info[1][:3], (1, 'duel_idx', 'INTEGER'))
        self.assertEqual(table_info[2][:3], (2, 'match_id', 'varchar'))


class DbTournamentsTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        import aiosqlite

        self.dbconn = DbConnector(':memory:', Config())
        # manually initialize the dbconn to avoid executing migrations
        self.dbconn.conn = await aiosqlite.connect(':memory:', autocommit=False)
        c = await self.dbconn.conn.cursor()
        await migrations.setup_metadata(c)

        self.c = await self.dbconn.conn.cursor()
        await migrations.execute_migrations(self.c, self.dbconn.config, 8)  # TODO either 8 or len(migrations)
        await self.dbconn.conn.commit()

    async def asyncTearDown(self):
        await self.dbconn.conn.close()

    async def test_create_tournament(self):
        with patch('QRServer.db.connector.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

            tournament_id = await self.dbconn.create_tournament('test_tournament', '123', '456', 3)

        expected_tournament = Tournament(
            tournament_id=tournament_id,
            name='test_tournament',
            created_by_dc_id='123',
            tournament_msg_dc_id='456',
            required_matches_per_duel=3,
            created_at=datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            started_at=None,
            finished_at=None
        )
        tournament = await self.dbconn.get_tournament(tournament_id)
        self.assertEqual(tournament, expected_tournament)

        # Test create tournament with the same name
        with patch('QRServer.db.connector.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2020, 1, 1, 12, 0, 0, tzinfo=timezone.utc)

            tournament_id = await self.dbconn.create_tournament('test_tournament', '123', '456', 3)

            self.assertEqual(tournament_id, None)

    async def test_add_participants(self):
        tournament_id = await self.dbconn.create_tournament('test_tournament', '123', '456', 3)

        # Create member and add as participant
        member_id = await self.dbconn.create_member('user_0', 'password_0'.encode())
        await self.dbconn.add_participant(tournament_id, member_id)

        participants = await self.dbconn.list_participants(tournament_id)

        self.assertEqual(len(participants), 1)
        self.assertIn(TournamentParticipant(tournament_id, member_id), participants)

        # Test add participant after tournament was started
        result = await self.dbconn.start_tournament(tournament_id)
        self.assertTrue(result)

        id_ = str(uuid.uuid4())
        result = await self.dbconn.add_participant(tournament_id, id_)
        self.assertFalse(result)

        participant_ids = await self.dbconn.list_participants(tournament_id)
        self.assertNotIn(id_, participant_ids)

    async def test_remove_participant(self):
        tournament_id = await self.dbconn.create_tournament('test_tournament', '123', '456', 3)

        # Create member, add as participant and try to remove (should remove)
        member_id = await self.dbconn.create_member('user_0', 'password_0'.encode())
        await self.dbconn.add_participant(tournament_id, member_id)

        participant_ids = await self.dbconn.list_participants(tournament_id)
        participant_ids = [p.user_id for p in participant_ids]

        self.assertEqual(participant_ids, [member_id])

        result = await self.dbconn.remove_participant(tournament_id, member_id)
        self.assertTrue(result)

        participant_ids = await self.dbconn.list_participants(tournament_id)

        self.assertEqual(participant_ids, [])

        # Re-add the participant, start the tournament and try to remove participant (should not remove)
        await self.dbconn.add_participant(tournament_id, member_id)
        participant_ids = await self.dbconn.list_participants(tournament_id)
        participant_ids = [p.user_id for p in participant_ids]

        self.assertEqual(participant_ids, [member_id])

        await self.dbconn.start_tournament(tournament_id)

        result = await self.dbconn.remove_participant(tournament_id, member_id)
        self.assertFalse(result)

        participant_ids = await self.dbconn.list_participants(tournament_id)
        participant_ids = [p.user_id for p in participant_ids]
        self.assertEqual(participant_ids, [member_id])

        # Test remove nonexistent participant
        result = await self.dbconn.remove_participant(tournament_id, str(uuid.uuid4()))
        self.assertFalse(result)

        participant_ids = await self.dbconn.list_participants(tournament_id)
        participant_ids = [p.user_id for p in participant_ids]
        self.assertEqual(participant_ids, [member_id])

    async def test_start_tournament(self):
        # Test start existing tournament
        tournament_id = await self.dbconn.create_tournament('test_tournament', '123', '456', 3)

        with patch('QRServer.db.connector.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2020, 1, 2, 12, 0, 0, tzinfo=timezone.utc)

            result = await self.dbconn.start_tournament(tournament_id)

        self.assertTrue(result)

        tournament = await self.dbconn.get_tournament(tournament_id)
        self.assertEqual(tournament.started_at, datetime(2020, 1, 2, 12, 0, 0, tzinfo=timezone.utc))

        # Test start non-existent tournament
        result = await self.dbconn.start_tournament(str(uuid.uuid4()))

        self.assertFalse(result)

    async def test_duels(self):
        participants_count = 4
        active_until = datetime(2020, 1, 5, 12, 0, 0, tzinfo=timezone.utc)

        tournament_id = await self.dbconn.create_tournament('test_tournament', '123', '456', 3)

        member_ids = []
        for i in range(participants_count):
            member_id = await self.dbconn.create_member(f'user_{i}', f'password_{i}'.encode())
            member_ids.append(member_id)
            await self.dbconn.add_participant(tournament_id, member_id)

        await self.dbconn.add_duel(tournament_id, 0, active_until, member_ids[0], member_ids[1])
        await self.dbconn.add_duel(tournament_id, 1, active_until, member_ids[2], member_ids[3])

        # Test listing duels
        duels = await self.dbconn.list_duels(tournament_id)
        self.assertEqual(len(duels), 2)

        # Test specific duels
        duel_0 = await self.dbconn.get_duel(tournament_id, 0)
        duel_1 = await self.dbconn.get_duel(tournament_id, 1)

        self.assertEqual(duels[0], duel_0)
        self.assertEqual(duels[1], duel_1)

        # Test add existing duel idx
        result = await self.dbconn.add_duel(tournament_id, 0, active_until, member_ids[0], member_ids[1])
        self.assertFalse(result)

        # Test add duel with same users
        result = await self.dbconn.add_duel(tournament_id, 2, active_until, member_ids[0], member_ids[2])
        self.assertTrue(result)

        duels = await self.dbconn.list_duels(tournament_id)
        self.assertEqual(len(duels), 3)

    async def test_add_duel_matches(self):
        participants_count = 2
        active_until = datetime(2020, 1, 5, 12, 0, 0, tzinfo=timezone.utc)

        tournament_id = await self.dbconn.create_tournament('test_tournament', '123', '456', 3)

        member_ids = []
        for i in range(participants_count):
            member_id = await self.dbconn.create_member(f'user_{i}', f'password_{i}'.encode())
            member_ids.append(member_id)
            await self.dbconn.add_participant(tournament_id, member_id)

        await self.dbconn.start_tournament(tournament_id)

        result = await self.dbconn.add_duel(tournament_id, 0, active_until, member_ids[0], member_ids[1])
        self.assertTrue(result)

        duel = await self.dbconn.get_duel(tournament_id, 0)

        match = DbMatchReport(
            winner_id=duel.user1_id,
            loser_id=duel.user2_id,
            winner_pieces_left=10,
            loser_pieces_left=0,
            move_counter=255,
            grid_size='standard',
            squadron_size='standard',
            started_at=datetime(2020, 1, 5, 12, 0, 0, tzinfo=timezone.utc),
            finished_at=datetime(2020, 1, 5, 13, 0, 0, tzinfo=timezone.utc),
            is_ranked=True,
            is_void=False,
        )
        await self.dbconn.add_match_result(match)
        result = await self.dbconn.add_duel_match(tournament_id, 0, match.match_id)

        self.assertTrue(result)

        duel_matches = await self.dbconn.get_duel_matches(tournament_id, 0)
        self.assertEqual(len(duel_matches), 1)

        match.match_id = str(uuid.uuid4())

        await self.dbconn.add_match_result(match)
        await self.dbconn.add_duel_match(tournament_id, 0, match.match_id)

        duel_matches = await self.dbconn.get_duel_matches(tournament_id, 0)
        self.assertEqual(len(duel_matches), 2)
