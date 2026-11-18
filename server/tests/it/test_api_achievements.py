from . import QuadradiusIntegrationTestCase

PASSWORD = 'ff585d509bf09ce1d2ff5d4226b7dacb'
SVG = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><path d="M2 1h6v3a3 3 0 0 1-6 0z"/></svg>'
SVG_DATA_URI = (
    'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIH'
    'ZpZXdCb3g9IjAgMCAxMCAxMCI+PHBhdGggZD0iTTIgMWg2djNhMyAzIDAgMCAxLTYgMHoiLz48L3N2Zz'
    '4='
)


class ApiAchievementsIT(QuadradiusIntegrationTestCase):
    async def itSetUpConfig(self, config):
        config.set('api.enabled', True)
        config.set('auth.auto_register', True)

    async def _login(self, api_client, username='PlayerA'):
        await self.connector.authenticate_user(username, PASSWORD.encode(), auto_create=True)
        data = {'username': username, 'password': PASSWORD, 'grant_type': 'password'}
        async with api_client.post('/api/oauth/token', json=data) as r:
            self.assertEqual(r.status, 200)
            return {'Authorization': f'Bearer {(await r.json())["access_token"]}'}

    async def _create(self, key, name, description, svg=None):
        # The connector has no function for creating definitions, create them by hand and hope for the best
        async with self.connector._transaction('w') as c:
            await c.execute(
                'insert into achievements (key, name, description, created_at, svg) values (?, ?, ?, ?, ?)',
                (key, name, description, 0, svg))

    async def test_requires_authentication(self):
        api_client = await self.new_api_client('v1')
        await self._create('demo', 'Demo Ach', 'Do the thing.')

        async with api_client.get('/api/v1/achievements/demo') as r:
            self.assertEqual(r.status, 401)

    async def test_achievement_with_image(self):
        api_client = await self.new_api_client('v1')
        headers = await self._login(api_client)
        await self._create('demo', 'Demo Ach', 'Do the thing.', SVG)

        async with api_client.get('/api/v1/achievements/demo', headers=headers) as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(r.headers['Cache-Control'], 'private, max-age=604800')
            self.assertEqual(await r.json(), {
                'achievement': {
                    'key': 'demo',
                    'name': 'Demo Ach',
                    'description': 'Do the thing.',
                    'image': SVG_DATA_URI,
                },
            })

    async def test_achievement_without_image(self):
        api_client = await self.new_api_client('v1')
        headers = await self._login(api_client)
        await self._create('none', 'No Image', 'Not uploaded yet.', None)
        await self._create('empty', 'Empty Image', 'Uploaded as nothing.', b'')

        async with api_client.get('/api/v1/achievements/none', headers=headers) as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(r.headers['Cache-Control'], 'private, max-age=86400')
            self.assertEqual(await r.json(), {
                'achievement': {
                    'key': 'none',
                    'name': 'No Image',
                    'description': 'Not uploaded yet.',
                    'image': None,
                },
            })

        async with api_client.get('/api/v1/achievements/empty', headers=headers) as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {
                'achievement': {
                    'key': 'empty',
                    'name': 'Empty Image',
                    'description': 'Uploaded as nothing.',
                    'image': None,
                },
            })

    async def test_unknown_achievement_is_not_found(self):
        api_client = await self.new_api_client('v1')
        headers = await self._login(api_client)

        async with api_client.get('/api/v1/achievements/nope', headers=headers) as r:
            self.assertEqual(r.status, 404)
            self.assertEqual(r.headers['Cache-Control'], 'private, max-age=86400')
            self.assertEqual(await r.json(), {
                'error': 'this achievement does not exist',
                'error_code': 'achievement_not_found',
            })

    async def test_key_lookup_ignores_case(self):
        # The key column is case-insensitive, the achievement is always returned with the stored key
        api_client = await self.new_api_client('v1')
        headers = await self._login(api_client)
        await self._create('Advent-2026', 'Advent', 'Finish them all.')

        for requested in ('Advent-2026', 'advent-2026', 'ADVENT-2026'):
            async with api_client.get(f'/api/v1/achievements/{requested}', headers=headers) as r:
                self.assertEqual(r.status, 200, requested)
                self.assertEqual(await r.json(), {
                    'achievement': {
                        'key': 'Advent-2026',
                        'name': 'Advent',
                        'description': 'Finish them all.',
                        'image': None,
                    },
                }, requested)
