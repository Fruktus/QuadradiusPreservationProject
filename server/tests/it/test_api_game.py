from . import QuadradiusIntegrationTestCase


class ApiGameIT(QuadradiusIntegrationTestCase):
    async def itSetUpConfig(self, config):
        config.set('api.enabled', True)
        config.set('auth.auto_register', True)

    async def test_game_stats(self):
        # Make sure all players have accounts
        client = await self.new_lobby_client()
        await client.join_lobby('PlayerA', 'ff585d509bf09ce1d2ff5d4226b7dacb')
        client = await self.new_lobby_client()
        await client.join_lobby('PlayerB', 'ff585d509bf09ce1d2ff5d4226b7dacb')
        client = await self.new_lobby_client()
        await client.join_lobby('PlayerC', 'ff585d509bf09ce1d2ff5d4226b7dacb')
        client = await self.new_lobby_client()
        await client.join_lobby('PlayerD', 'ff585d509bf09ce1d2ff5d4226b7dacb')
        client = await self.new_lobby_client()
        await client.join_lobby('PlayerE', 'ff585d509bf09ce1d2ff5d4226b7dacb')
        client = await self.new_lobby_client()
        await client.join_lobby('PlayerF', 'ff585d509bf09ce1d2ff5d4226b7dacb')

        api_client = await self.new_api_client('v1')
        async with api_client.get('game/stats') as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {
                'player_count': 0,
            })

        client1 = await self.new_game_client()
        await client1.join_game(
            'PlayerA', '1234',
            'PlayerB', '4321',
            'ff585d509bf09ce1d2ff5d4226b7dacb')

        async with api_client.get('game/stats') as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {
                'player_count': 2,
            })

        client2 = await self.new_game_client()
        await client2.join_game(
            'PlayerB', '4321',
            'PlayerA', '1234',
            'ff585d509bf09ce1d2ff5d4226b7dacb')

        async with api_client.get('game/stats') as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {
                'player_count': 2,
            })

        client3 = await self.new_game_client()
        await client3.join_game(
            'PlayerC', '2345',
            'PlayerD', '5432',
            'ff585d509bf09ce1d2ff5d4226b7dacb')

        async with api_client.get('game/stats') as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {
                'player_count': 4,
            })

        client4 = await self.new_game_client()
        await client4.join_game(
            'PlayerE', '6789',
            'PlayerF', '9876',
            'ff585d509bf09ce1d2ff5d4226b7dacb')

        async with api_client.get('game/stats') as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {
                'player_count': 6,
            })

        await client4.disconnect_and_wait()

        async with api_client.get('game/stats') as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {
                'player_count': 4,
            })
