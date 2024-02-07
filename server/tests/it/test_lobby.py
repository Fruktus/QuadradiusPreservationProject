from QRServer.common.classes import LobbyPlayer
from QRServer.common.messages import JoinLobbyRequest, LobbyStateResponse, LobbyDuplicateResponse
from . import QuadradiusIntegrationTestCase


class LobbyIT(QuadradiusIntegrationTestCase):
    async def itSetUpConfig(self, config):
        config.set('auth.auto_register', True)

    async def test_join_lobby(self):
        client = await self.new_lobby_client()

        await client.send_message(
            JoinLobbyRequest.new('John', 'cf585d509bf09ce1d2ff5d4226b7dacb'))

        await client.assert_received_message(
            LobbyStateResponse.new([LobbyPlayer(username='John')]))

        clients = self.server.lobby_server.clients
        self.assertEqual(clients[0].username, 'John')
        for i in range(1, 13):
            self.assertEqual(clients[i], None)

    async def test_join_multiple(self):
        client1 = await self.new_lobby_client()
        client2 = await self.new_lobby_client()

        await client1.send_message(
            JoinLobbyRequest.new('John', 'cf585d509bf09ce1d2ff5d4226b7dacb'))
        await client1.assert_received_message(
            LobbyStateResponse.new([LobbyPlayer(username='John')]))

        await client2.send_message(
            JoinLobbyRequest.new('Robert', 'cf585d509bf09ce1d2ff5d4226b7dacb'))
        await client2.assert_received_message(
            LobbyStateResponse.new([LobbyPlayer(username='John'), LobbyPlayer(username='Robert')]))

        clients = self.server.lobby_server.clients
        self.assertEqual(clients[0].username, 'John')
        self.assertEqual(clients[1].username, 'Robert')
        for i in range(2, 13):
            self.assertEqual(clients[i], None)

    async def test_leave_lobby(self):
        client = await self.new_lobby_client()
        await client.join_lobby('Robert', 'cf585d509bf09ce1d2ff5d4226b7dacb')
        await client.disconnect()
        await self.wait_for_empty_lobby()

    async def test_leave_lobby_abrupt(self):
        client = await self.new_lobby_client()
        await client.join_lobby('Robert', 'cf585d509bf09ce1d2ff5d4226b7dacb')
        client.close()
        await self.wait_for_empty_lobby()

    async def test_join_duplicate_username(self):
        client1 = await self.new_lobby_client()
        await client1.join_lobby('Robert', 'cf585d509bf09ce1d2ff5d4226b7dacb')

        client2 = await self.new_lobby_client()
        await client2.send_message(
            JoinLobbyRequest.new('Robert', 'cf585d509bf09ce1d2ff5d4226b7dacb'))

        await client2.assert_received_message(
            LobbyDuplicateResponse.new())
