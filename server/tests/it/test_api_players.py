import base64
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from QRServer.db.models import DbMatchReport

from . import QuadradiusIntegrationTestCase

PASSWORD = 'ff585d509bf09ce1d2ff5d4226b7dacb'
SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><path d="M2 1h6v3a3 3 0 0 1-6 0z"/></svg>'


class ApiPlayersIT(QuadradiusIntegrationTestCase):
    async def itSetUpConfig(self, config):
        config.set('api.enabled', True)
        config.set('auth.auto_register', True)

    async def _login(self, api_client, username):
        await self.connector.authenticate_user(username, PASSWORD.encode(), auto_create=True)
        data = {'username': username, 'password': PASSWORD, 'grant_type': 'password'}
        async with api_client.post('/api/oauth/token', json=data) as r:
            self.assertEqual(r.status, 200)
            return {'Authorization': f'Bearer {(await r.json())["access_token"]}'}

    async def _match(self, winner_id, loser_id, moves=20):
        started = datetime(2020, 1, 1, tzinfo=timezone.utc)
        await self.connector.create_match_and_add_result(DbMatchReport(
            match_id=str(uuid.uuid4()),
            winner_id=winner_id,
            loser_id=loser_id,
            winner_pieces_left=10,
            loser_pieces_left=4,
            move_counter=moves,
            grid_size='standard',
            squadron_size='standard',
            started_at=started,
            finished_at=started + timedelta(minutes=10),
            is_ranked=True,
            is_void=False,
        ))

    async def test_requires_authentication(self):
        api_client = await self.new_api_client('v1')
        async with api_client.get('/api/v1/players/PlayerA') as r:
            self.assertEqual(r.status, 401)

    async def test_unknown_guest_and_banned_players_are_not_found(self):
        api_client = await self.new_api_client('v1')
        headers = await self._login(api_client, 'PlayerA')
        await self.connector.authenticate_user('Someone GUEST', None, auto_create=True)
        banned = await self.connector.authenticate_user('Banned', PASSWORD.encode(), auto_create=True)
        await self.connector.ban_user(banned.user_id, '1', 'reason')

        for name in ('Nobody', 'Someone GUEST', 'Banned'):
            async with api_client.get(f'/api/v1/players/{name}', headers=headers) as r:
                self.assertEqual(r.status, 404, name)
                self.assertEqual((await r.json())['error_code'], 'player_not_found')

    async def test_profile_of_a_fresh_player(self):
        api_client = await self.new_api_client('v1')
        headers = await self._login(api_client, 'PlayerA')

        async with api_client.get('/api/v1/players/PlayerA', headers=headers) as r:
            self.assertEqual(r.status, 200)
            body = await r.json()

        self.assertEqual(body['player']['username'], 'PlayerA')
        self.assertIsNotNone(body['player']['member_since'])
        self.assertEqual(body['stats'], {
            'total_matches': 0, 'wins': 0, 'losses': 0, 'win_rate': None,
            'longest_match_seconds': None, 'most_moves': None, 'biggest_win_margin': None, 'nemesis': None,
        })
        self.assertEqual(body['trophies'], [])

    async def test_profile_can_be_looked_up_by_another_player(self):
        api_client = await self.new_api_client('v1')
        headers = await self._login(api_client, 'PlayerA')
        player_b = await self.connector.authenticate_user('Player B', PASSWORD.encode(), auto_create=True)
        player_a = await self.connector.get_user_by_username('PlayerA')
        for _ in range(5):
            await self._match(player_a.user_id, player_b.user_id, moves=42)

        async with api_client.get('/api/v1/players/Player%20B', headers=headers) as r:
            self.assertEqual(r.status, 200)
            body = await r.json()

        self.assertEqual(body['player']['username'], 'Player B')
        self.assertEqual(body['stats']['losses'], 5)
        self.assertEqual(body['stats']['most_moves'], 42)
        self.assertEqual(body['stats']['nemesis'], {'username': 'PlayerA', 'losses': 5})

    async def test_trophies_are_returned_as_data_uris(self):
        api_client = await self.new_api_client('v1')
        headers = await self._login(api_client, 'PlayerA')
        player = await self.connector.get_user_by_username('PlayerA')
        tournament_id = await self.connector.create_tournament('Cup', 'discord-id', 'msg-id', 1)
        trophy_id = await self.connector.create_trophy('Cup winner', SVG, tournament_id)
        await self.connector.award_trophy(trophy_id, player.user_id)

        async with api_client.get('/api/v1/players/PlayerA', headers=headers) as r:
            body = await r.json()

        self.assertEqual(len(body['trophies']), 1)
        trophy = body['trophies'][0]
        self.assertEqual(trophy['name'], 'Cup winner')
        prefix = 'data:image/svg+xml;base64,'
        self.assertTrue(trophy['image'].startswith(prefix))
        self.assertEqual(base64.b64decode(trophy['image'][len(prefix):]), SVG)

    async def test_profile_is_cached(self):
        api_client = await self.new_api_client('v1')
        headers = await self._login(api_client, 'PlayerA')
        player_a = await self.connector.get_user_by_username('PlayerA')
        player_b = await self.connector.authenticate_user('PlayerB', PASSWORD.encode(), auto_create=True)

        now = [1000.0]
        with patch('QRServer.common.utils.cache._clock', lambda: now[0]):
            async with api_client.get('/api/v1/players/PlayerA', headers=headers) as r:
                self.assertEqual(r.status, 200)
                self.assertEqual(r.headers['Cache-Control'], 'private, max-age=600')
                self.assertEqual((await r.json())['stats']['wins'], 0)

            await self._match(player_a.user_id, player_b.user_id)

            now[0] += 599
            async with api_client.get('/api/v1/players/PlayerA', headers=headers) as r:
                self.assertEqual((await r.json())['stats']['wins'], 0)  # still the cached one

            now[0] += 2
            async with api_client.get('/api/v1/players/PlayerA', headers=headers) as r:
                self.assertEqual((await r.json())['stats']['wins'], 1)

    async def test_cached_profile_does_not_touch_the_database(self):
        api_client = await self.new_api_client('v1')
        headers = await self._login(api_client, 'PlayerA')
        queries = ('get_user_by_username', 'get_player_stats', 'get_user_trophies')

        with patch('QRServer.common.utils.cache._clock', lambda: 1000.0):
            mocks = {name: patch.object(self.connector, name, wraps=getattr(self.connector, name))
                     for name in queries}
            started = {name: m.start() for name, m in mocks.items()}
            try:
                for _ in range(5):
                    async with api_client.get('/api/v1/players/PlayerA', headers=headers) as r:
                        self.assertEqual(r.status, 200)
                for name in queries:
                    self.assertEqual(started[name].call_count, 1, name)
            finally:
                for m in mocks.values():
                    m.stop()

    async def test_not_found_is_cached_too(self):
        api_client = await self.new_api_client('v1')
        headers = await self._login(api_client, 'PlayerA')

        now = [1000.0]
        with patch('QRServer.common.utils.cache._clock', lambda: now[0]):
            async with api_client.get('/api/v1/players/Latecomer', headers=headers) as r:
                self.assertEqual(r.status, 404)

            await self.connector.authenticate_user('Latecomer', PASSWORD.encode(), auto_create=True)
            async with api_client.get('/api/v1/players/Latecomer', headers=headers) as r:
                self.assertEqual(r.status, 404)  # still the cached one

            now[0] += 601
            async with api_client.get('/api/v1/players/Latecomer', headers=headers) as r:
                self.assertEqual(r.status, 200)

    async def test_cached_profile_still_requires_authentication(self):
        api_client = await self.new_api_client('v1')
        headers = await self._login(api_client, 'PlayerA')

        async with api_client.get('/api/v1/players/PlayerA', headers=headers) as r:
            self.assertEqual(r.status, 200)  # now it is cached

        async with api_client.get('/api/v1/players/PlayerA') as r:
            self.assertEqual(r.status, 401)
