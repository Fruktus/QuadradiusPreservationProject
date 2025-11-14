from datetime import datetime, timezone
from unittest.mock import patch
import uuid

from QRServer.db.models import DbMatchReport, DbUser
from . import QuadradiusIntegrationTestCase


class ApiTournamentsIT(QuadradiusIntegrationTestCase):
    async def itSetUpConfig(self, config):
        config.set('api.enabled', True)
        config.set('auth.auto_register', True)

    async def _make_two_users(self) -> tuple[DbUser, DbUser]:
        client1 = await self.new_lobby_client()
        await client1.join_lobby('PlayerA', 'ff585d509bf09ce1d2ff5d4226b7dacb')
        user1 = await self.connector.get_user_by_username('PlayerA')
        if not user1:
            raise AssertionError('Failed to create user 1')

        client2 = await self.new_lobby_client()
        await client2.join_lobby('PlayerB', 'ff585d509bf09ce1d2ff5d4226b7dacb')
        user2 = await self.connector.get_user_by_username('PlayerB')
        if not user2:
            raise AssertionError('Failed to create user 2')

        return (user1, user2)

    async def test_tournaments_users_empty(self):
        tournament_id = await self.connector.create_tournament('test_name2', '123', '234', 3)
        api_client = await self.new_api_client('v1')

        async with api_client.get(f'tournaments/{tournament_id}/users') as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {'users': []})

    async def test_tournaments_users(self):
        tournament_id = await self.connector.create_tournament('test_name', '123', '234', 3)

        user1, user2 = await self._make_two_users()
        result = await self.connector.add_participant(tournament_id, user1.user_id)
        self.assertTrue(result)
        result = await self.connector.add_participant(tournament_id, user2.user_id)
        self.assertTrue(result)

        api_client = await self.new_api_client('v1')
        async with api_client.get(f'tournaments/{tournament_id}/users') as r:
            self.assertEqual(r.status, 200)
            self.assertCountEqual(await r.json(), {
                'users': [
                    {
                        'id': user1.user_id,
                        'username': user1.username,
                    },
                    {
                        'id': user2.user_id,
                        'username': user2.username,
                    },
                ]
            })

    async def test_tournaments_users_404(self):
        api_client = await self.new_api_client('v1')
        async with api_client.get('tournaments/nonexistent/users') as r:
            self.assertEqual(r.status, 404)
            self.assertEqual(await r.json(), None)

    async def test_tournaments(self):
        with patch('QRServer.db.connector.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2020, 1, 2, 12, 0, 0, tzinfo=timezone.utc)

            tournament_id = await self.connector.create_tournament('test_name', '123', '234', 3)

        api_client = await self.new_api_client('v1')
        async with api_client.get(f'tournaments/{tournament_id}') as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {
                'tournament': {
                    'id': tournament_id,
                    'name': 'test_name',
                    'created_at': '2020-01-02T12:00:00+00:00',
                    'started_at': None,
                    'finished_at': None,
                    'required_matches_per_duel': 3,
                }
            })

        with patch('QRServer.db.connector.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2020, 1, 3, 12, 0, 0, tzinfo=timezone.utc)

            result = await self.connector.start_tournament(tournament_id)

        self.assertTrue(result)

        async with api_client.get(f'tournaments/{tournament_id}') as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {
                'tournament': {
                    'id': tournament_id,
                    'name': 'test_name',
                    'created_at': '2020-01-02T12:00:00+00:00',
                    'started_at': '2020-01-03T12:00:00+00:00',
                    'finished_at': None,
                    'required_matches_per_duel': 3,
                }
            })

    async def test_tournaments_404(self):
        api_client = await self.new_api_client('v1')
        async with api_client.get('tournaments/nonexistent') as r:
            self.assertEqual(r.status, 404)
            self.assertEqual(await r.json(), None)

    async def test_tournaments_duels_empty(self):
        tournament_id = await self.connector.create_tournament('test_name', '123', '234', 3)

        api_client = await self.new_api_client('v1')
        async with api_client.get(f'tournaments/{tournament_id}/duels') as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {'duels': []})

    async def test_tournaments_duels(self):
        tournament_id = await self.connector.create_tournament('test_name', '123', '234', 3)
        user1, user2 = await self._make_two_users()

        result = await self.connector.add_duel(
            tournament_id=tournament_id,
            duel_idx=0,
            active_until=datetime(2020, 12, 1, 1, 1, 1, tzinfo=timezone.utc),
            user1_id=user1.user_id,
            user2_id=user2.user_id,
        )
        self.assertTrue(result)

        api_client = await self.new_api_client('v1')
        async with api_client.get(f'tournaments/{tournament_id}/duels') as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {
                'duels': [
                    {
                        'idx': 0,
                        'active_until': '2020-12-01T01:01:01+00:00',
                        'user1_id': user1.user_id,
                        'user2_id': user2.user_id,
                    }
                ]
            })

    async def test_tournaments_duels_404(self):
        api_client = await self.new_api_client('v1')
        async with api_client.get('tournaments/nonexistent/duels') as r:
            self.assertEqual(r.status, 404)
            self.assertEqual(await r.json(), None)

    async def test_tournaments_matches_empty(self):
        tournament_id = await self.connector.create_tournament('test_name2', '123', '234', 3)
        api_client = await self.new_api_client('v1')

        async with api_client.get(f'tournaments/{tournament_id}/matches') as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {'tournament_matches': []})

    async def test_tournaments_matches(self):
        tournament_id = await self.connector.create_tournament('test_name', '123', '234', 3)
        user1, user2 = await self._make_two_users()

        api_client = await self.new_api_client('v1')
        await self.server.connector.add_duel(
            tournament_id=tournament_id,
            duel_idx=0,
            active_until=datetime(2020, 12, 1, 1, 1, 1, tzinfo=timezone.utc),
            user1_id=user1.user_id,
            user2_id=user2.user_id,
        )

        match_id = str(uuid.uuid4())
        match = DbMatchReport(
            winner_id=user1.user_id,
            loser_id=user2.user_id,
            winner_pieces_left=10,
            loser_pieces_left=0,
            move_counter=200,
            grid_size='default',
            squadron_size='default',
            started_at=datetime(2020, 1, 1, 1, 1, 1, tzinfo=timezone.utc),
            finished_at=datetime(2020, 1, 1, 2, 1, 1, tzinfo=timezone.utc),
            is_ranked=True,
            is_void=False,
            match_id=match_id,
        )
        await self.connector.add_match_result(match)
        result = await self.connector.add_duel_match(tournament_id, 0, match_id)
        self.assertTrue(result)

        async with api_client.get(f'tournaments/{tournament_id}/matches') as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {
                'tournament_matches': [
                    {
                        'duel_idx': 0,
                        'match': {
                            'id': match_id,
                            'winner_id': user1.user_id,
                            'loser_id': user2.user_id,
                            'winner_pieces_left': 10,
                            'loser_pieces_left': 0,
                            'started_at': '2020-01-01T01:01:01+00:00',
                            'finished_at': '2020-01-01T02:01:01+00:00',
                            'is_ranked': True,
                            'is_void': False,
                        },
                    }
                ]
            })

    async def test_tournaments_matches_404(self):
        api_client = await self.new_api_client('v1')
        async with api_client.get('tournaments/nonexistent/matches') as r:
            self.assertEqual(r.status, 404)
            self.assertEqual(await r.json(), None)
