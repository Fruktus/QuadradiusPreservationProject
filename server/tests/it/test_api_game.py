from QRServer.common.messages import JoinGameRequest, PlayerCountResponse, \
    HelloGameRequest
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
        await client1.send_message(HelloGameRequest.new())
        await client1.send_message(JoinGameRequest.new(
            'PlayerA', '1234',
            'PlayerB', '4321',
            'ff585d509bf09ce1d2ff5d4226b7dacb'))
        await client1.assert_received_message_type(PlayerCountResponse)

        async with api_client.get('game/stats') as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {
                'player_count': 2,
            })

        client2 = await self.new_game_client()
        await client2.send_message(HelloGameRequest.new())
        await client2.send_message(JoinGameRequest.new(
            'PlayerB', '4321',
            'PlayerA', '1234',
            'ff585d509bf09ce1d2ff5d4226b7dacb'))
        await client2.assert_received_message_type(PlayerCountResponse)

        async with api_client.get('game/stats') as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {
                'player_count': 2,
            })

        client3 = await self.new_game_client()
        await client3.send_message(HelloGameRequest.new())
        await client3.send_message(JoinGameRequest.new(
            'PlayerC', '2345',
            'PlayerD', '5432',
            'ff585d509bf09ce1d2ff5d4226b7dacb'))
        await client3.assert_received_message_type(PlayerCountResponse)

        async with api_client.get('game/stats') as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {
                'player_count': 4,
            })

        client4 = await self.new_game_client()
        await client4.send_message(HelloGameRequest.new())
        await client4.send_message(JoinGameRequest.new(
            'PlayerE', '6789',
            'PlayerF', '9876',
            'ff585d509bf09ce1d2ff5d4226b7dacb'))
        await client4.assert_received_message_type(PlayerCountResponse)

        async with api_client.get('game/stats') as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {
                'player_count': 6,
            })
