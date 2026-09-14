from unittest.mock import patch

from . import QuadradiusIntegrationTestCase


class ApiGameIT(QuadradiusIntegrationTestCase):
    async def itSetUpConfig(self, config):
        config.set('api.enabled', True)
        config.set('auth.auto_register', True)

    async def test_make_invite_url(self):
        # Make sure all players have accounts
        client = await self.new_lobby_client()
        await client.join_lobby('PlayerA', 'ff585d509bf09ce1d2ff5d4226b7dacb')
        client = await self.new_lobby_client()
        await client.join_lobby('PlayerB', 'ff585d509bf09ce1d2ff5d4226b7dacb')
        client = await self.new_lobby_client()

        # Obtain oidc tokens for both players
        api_client = await self.new_api_client('v1')
        data = {
            'username': 'PlayerA',
            'password': 'ff585d509bf09ce1d2ff5d4226b7dacb',
            'grant_type': 'password',
        }
        async with api_client.post('/api/oauth/token', json=data) as r:
            self.assertEqual(r.status, 200)
            resp = await r.json()
            access_token_1 = resp['access_token']

        data = {
            'username': 'PlayerB',
            'password': 'ff585d509bf09ce1d2ff5d4226b7dacb',
            'grant_type': 'password',
        }
        async with api_client.post('/api/oauth/token', json=data) as r:
            self.assertEqual(r.status, 200)
            resp = await r.json()
            access_token_2 = resp['access_token']

        # Create invite manually
        user1 = await self.connector.get_user_by_username('PlayerA')
        user2 = await self.connector.get_user_by_username('PlayerB')

        with patch('uuid.uuid4') as mock_uuid, \
             patch('QRServer.db.connector.random') as random_mock:
            mock_uuid.side_effect = ['1', '2', '3']
            random_mock.randint.side_effect = [-1, -2]
            invite_id = await self.connector.create_match_invite(user1.user_id, user2.user_id)
        # Get the invite as both players using url and oidc
        # PlayerA
        async with api_client.get(
            f'/api/v1/invites/{invite_id}/make-params', headers={'Authorization': f'Bearer {access_token_1}'}
        ) as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {"params": "myName=PlayerA&myAuthentication=-1&opponentName=PlayerB&opponentAuthentication=-2&myPass=2"})  # NOQA: E501

        # Get the invite as both players using url and oidc
        # PlayerB
        async with api_client.get(
            f'/api/v1/invites/{invite_id}/make-params', headers={'Authorization': f'Bearer {access_token_2}'}
        ) as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {"params": "myName=PlayerB&myAuthentication=-2&opponentName=PlayerA&opponentAuthentication=-1&myPass=3"})  # NOQA: E501
