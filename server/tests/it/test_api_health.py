from . import QuadradiusIntegrationTestCase


class ApiHealthIT(QuadradiusIntegrationTestCase):
    async def itSetUpConfig(self, config):
        config.set('api.enabled', True)

    async def test_health(self):
        client = await self.new_api_client('v1')
        async with client.get('health') as r:
            self.assertEqual(r.status, 200)
            self.assertEqual(await r.json(), {})
