from datetime import datetime, timezone
from hashlib import md5
from unittest.mock import patch
import jwt
from . import QuadradiusIntegrationTestCase


class ApiOauthIT(QuadradiusIntegrationTestCase):
    async def itSetUpConfig(self, config):
        self.secret_key = 'TEST_KEY'
        config.set('origin', 'http://localhost')
        config.set('api.enabled', True)
        config.set('api.token_secret', self.secret_key)
        config.set('api.access_token_lifetime_sec', 60)
        config.set('api.refresh_token_lifetime_sec', 120)

    async def _create_test_user(self):
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value = '1234'
            await self.connector.create_member(
                username='testuser',
                password=md5('++TESTUSER++asd'.encode()).hexdigest().encode(),
                discord_user_id='@asd',
            )

    async def _login(self, client, username='testuser', password='asd'):
        async with client.post('/oauth/token', json={
            'grant_type': 'password',
            'username': username,
            'password': md5(f'++{username.upper()}++{password}'.encode()).hexdigest(),
        }) as r:
            return r.status, await r.json()

    async def test_wellknown(self):
        client = await self.new_api_client('v1')

        async with client.get('/.well-known/openid-configuration') as r:
            self.assertEqual(r.status, 200)
            doc = await r.json()

        self.assertEqual(doc['issuer'], 'http://localhost')
        self.assertEqual(doc['token_endpoint'], 'http://localhost/oauth/token')
        self.assertEqual(doc['userinfo_endpoint'], 'http://localhost/oauth/userinfo')
        self.assertEqual(doc['response_types_supported'], ['token'])
        self.assertEqual(doc['grant_types_supported'], ['password', 'refresh_token'])
        self.assertEqual(doc['token_endpoint_auth_methods_supported'], ['none'])

    # password grant
    async def test_password_grant_missing_body(self):
        client = await self.new_api_client('v1')

        async with client.post('/oauth/token') as r:
            self.assertEqual(r.status, 400)
            self.assertEqual((await r.json())['error'], 'invalid_request')

    async def test_password_grant_missing_fields(self):
        client = await self.new_api_client('v1')

        # Missing field
        async with client.post('/oauth/token', json={
            'grant_type': 'password',
            'username': 'testuser',
        }) as r:
            self.assertEqual(r.status, 400)
            self.assertEqual((await r.json())['error'], 'invalid_request')

        # Value present but set to None
        async with client.post('/oauth/token', json={
            'grant_type': 'password',
            'username': 'testuser',
            'password': None
        }) as r:
            self.assertEqual(r.status, 400)
            self.assertEqual((await r.json())['error'], 'invalid_request')

    async def test_password_grant_nonexistent_user(self):
        client = await self.new_api_client('v1')

        status, body = await self._login(client, username='nonexistent', password='asd')
        self.assertEqual(status, 401)
        self.assertEqual(body['error'], 'invalid_grant')

    async def test_password_grant_wrong_password(self):
        client = await self.new_api_client('v1')
        await self._create_test_user()

        status, body = await self._login(client, password='wrongpassword')

        self.assertEqual(status, 401)
        self.assertEqual(body['error'], 'invalid_grant')

    async def test_password_grant_success(self):
        client = await self.new_api_client('v1')
        await self._create_test_user()

        with patch('QRServer.api.auth.datetime') as mock_datetime:
            mock_datetime.now.return_value = datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

            status, body = await self._login(client)

        self.assertEqual(status, 200)
        self.assertEqual(body['token_type'], 'Bearer')
        self.assertEqual(body['expires_in'], 60)

        # verify access token (skip datetime validation)
        payload = jwt.decode(
            body['access_token'],
            self.secret_key,
            algorithms=['HS256'],
            options={"verify_exp": False}
        )
        self.assertEqual(payload['username'], 'testuser')
        self.assertEqual(payload['sub'], '1234')
        self.assertEqual(payload['type'], 'access')

        # verify refresh token (skip datetime validation)
        payload = jwt.decode(
            body['refresh_token'],
            self.secret_key, algorithms=['HS256'],
            options={"verify_exp": False}
        )
        self.assertEqual(payload['sub'], '1234')
        self.assertEqual(payload['type'], 'refresh')
        self.assertIn('jti', payload)

    async def test_unsupported_grant_type(self):
        client = await self.new_api_client('v1')

        async with client.post('/oauth/token', json={
            'grant_type': 'authorization_code',
            'code': 'asd',
        }) as r:
            self.assertEqual(r.status, 400)
            self.assertEqual((await r.json())['error'], 'unsupported_grant_type')

    # refresh token grant
    async def test_refresh_grant_success(self):
        client = await self.new_api_client('v1')
        await self._create_test_user()

        status, body = await self._login(client)
        self.assertEqual(status, 200)
        refresh_token = body['refresh_token']

        async with client.post('/oauth/token', json={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        }) as r:
            self.assertEqual(r.status, 200)
            body = await r.json()

        self.assertEqual(body['token_type'], 'Bearer')
        # refresh grants do not issue a new refresh token
        self.assertNotIn('refresh_token', body)

        # No need for datetime override since the token is both generated and tested
        # at the current time
        payload = jwt.decode(body['access_token'], self.secret_key, algorithms=['HS256'])
        self.assertEqual(payload['type'], 'access')
        self.assertEqual(payload['username'], 'testuser')

    async def test_refresh_grant_invalid_token(self):
        client = await self.new_api_client('v1')

        async with client.post('/oauth/token', json={
            'grant_type': 'refresh_token',
            'refresh_token': 'asd',
        }) as r:
            self.assertEqual(r.status, 401)
            self.assertEqual((await r.json())['error'], 'invalid_grant')
