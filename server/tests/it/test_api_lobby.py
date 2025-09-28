from . import QuadradiusIntegrationTestCase


class ApiLobbyIT(QuadradiusIntegrationTestCase):
    async def itSetUpConfig(self, config):
        config.set('api.enabled', True)
        config.set('auth.auto_register', True)

    async def test_lobby_stats(self):
        api_client = await self.new_api_client('v1')
        async with api_client.get('lobby/stats') as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {
                'player_count': 0,
            })

        client1 = await self.new_lobby_client()
        await client1.join_lobby('Player', 'cf585d509bf09ce1d2ff5d4226b7dacb')

        async with api_client.get('lobby/stats') as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {
                'player_count': 1,
            })

        client2 = await self.new_lobby_client()
        await client2.join_lobby('Player 2', 'ff585d509bf09ce1d2ff5d4226b7dacb')

        async with api_client.get('lobby/stats') as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {
                'player_count': 2,
            })

        await client1.disconnect_and_wait()

        async with api_client.get('lobby/stats') as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {
                'player_count': 1,
            })
