from . import QuadradiusIntegrationTestCase


class InitIT(QuadradiusIntegrationTestCase):
    async def test_init(self):
        # ensure tasks are running
        self.assertGreater(len(self.server.tasks), 0)
        # ensure ports are assigned
        self.assertGreater(self.server.lobby_port, 1023)
        self.assertGreater(self.server.game_port, 1023)
        # ensure no clients are connected
        for i in range(13):
            self.assertIsNone(self.server.lobby_server.clients[i])
        self.assertEqual(len(self.server.game_server.matches), 0)
