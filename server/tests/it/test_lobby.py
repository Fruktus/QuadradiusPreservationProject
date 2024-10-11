import asyncio
from unittest.mock import patch

from QRServer.common.classes import LobbyPlayer
from QRServer.common.messages import JoinLobbyRequest, LobbyStateResponse, LobbyDuplicateResponse, SetCommentRequest, \
    BroadcastCommentResponse, NameTakenRequest, NameTakenResponseYes, NameTakenResponseNo
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
        await client.assert_no_more_messages()

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
        await client1.assert_received_message(
            LobbyStateResponse.new([LobbyPlayer(username='John'), LobbyPlayer(username='Robert')]))
        await client2.assert_received_message(
            LobbyStateResponse.new([LobbyPlayer(username='John'), LobbyPlayer(username='Robert')]))
        await client1.assert_no_more_messages()
        await client2.assert_no_more_messages()

        clients = self.server.lobby_server.clients
        self.assertEqual(clients[0].username, 'John')
        self.assertEqual(clients[1].username, 'Robert')
        for i in range(2, 13):
            self.assertEqual(clients[i], None)

        await client1.disconnect_and_wait()

        await client2.assert_received_message(
            LobbyStateResponse.new([None, LobbyPlayer(username='Robert')]))
        await client2.assert_no_more_messages()

        clients = self.server.lobby_server.clients
        self.assertEqual(clients[0], None)
        self.assertEqual(clients[1].username, 'Robert')
        for i in range(2, 13):
            self.assertEqual(clients[i], None)

    async def test_leave_lobby(self):
        client = await self.new_lobby_client()
        await client.join_lobby('Robert', 'cf585d509bf09ce1d2ff5d4226b7dacb')
        await client.disconnect()
        await client.wait_for_disconnect()

    async def test_leave_lobby_abruptly(self):
        client = await self.new_lobby_client()
        await client.join_lobby('Robert', 'cf585d509bf09ce1d2ff5d4226b7dacb')
        await client.close()
        await client.wait_for_disconnect()

    async def test_join_duplicate_username(self):
        client1 = await self.new_lobby_client()
        await client1.join_lobby('Robert', 'cf585d509bf09ce1d2ff5d4226b7dacb')

        client2 = await self.new_lobby_client()
        await client2.send_message(
            JoinLobbyRequest.new('Robert', 'cf585d509bf09ce1d2ff5d4226b7dacb'))

        await client2.assert_received_message(
            LobbyDuplicateResponse.new())

        await client1.assert_no_more_messages()
        await client2.assert_no_more_messages()

    async def test_communique(self):
        client1 = await self.new_lobby_client()
        await client1.join_lobby('Robert', 'cf585d509bf09ce1d2ff5d4226b7dacb')

        client2 = await self.new_lobby_client()
        await client2.join_lobby('Bobert', 'cf585d509bf09ce1d2ff5d4226b7dacb')
        await client1.assert_received_message_type(LobbyStateResponse)

        client3 = await self.new_lobby_client()
        await client3.join_lobby('John', 'cf585d509bf09ce1d2ff5d4226b7dacb')
        await client1.assert_received_message_type(LobbyStateResponse)
        await client2.assert_received_message_type(LobbyStateResponse)

        await client2.send_message(
            SetCommentRequest.new(1, 'test communique'))
        await client1.assert_received_message(BroadcastCommentResponse.new(1, 'test communique'))
        await client2.assert_received_message(BroadcastCommentResponse.new(1, 'test communique'))
        await client3.assert_received_message(BroadcastCommentResponse.new(1, 'test communique'))

        await client1.assert_no_more_messages()
        await client2.assert_no_more_messages()
        await client3.assert_no_more_messages()

    async def test_communique_wrong_id(self):
        client1 = await self.new_lobby_client()
        await client1.join_lobby('Robert', 'cf585d509bf09ce1d2ff5d4226b7dacb')

        client2 = await self.new_lobby_client()
        await client2.join_lobby('Bobert', 'cf585d509bf09ce1d2ff5d4226b7dacb')
        await client1.assert_received_message_type(LobbyStateResponse)

        client3 = await self.new_lobby_client()
        await client3.join_lobby('John', 'cf585d509bf09ce1d2ff5d4226b7dacb')
        await client1.assert_received_message_type(LobbyStateResponse)
        await client2.assert_received_message_type(LobbyStateResponse)

        await client2.send_message(
            SetCommentRequest.new(0, 'test communique'))

        await client1.assert_no_more_messages()
        await client2.assert_no_more_messages()
        await client3.assert_no_more_messages()

    async def test_communique_broadcast_after_join(self):
        client1 = await self.new_lobby_client()
        await client1.join_lobby('Robert', 'cf585d509bf09ce1d2ff5d4226b7dacb')
        await client1.send_message(
            SetCommentRequest.new(0, 'test communique'))

        client2 = await self.new_lobby_client()
        await client2.send_message(JoinLobbyRequest.new('Bobert', 'cf585d509bf09ce1d2ff5d4226b7dacb'))
        await client2.assert_received_message(LobbyStateResponse.new([
            LobbyPlayer(username='Robert', comment='test communique'),
            LobbyPlayer(username='Bobert'),
        ]))
        await client2.assert_no_more_messages()

    async def test_communique_non_persistent(self):
        client1 = await self.new_lobby_client()
        await client1.join_lobby('Robert', 'cf585d509bf09ce1d2ff5d4226b7dacb')
        await client1.send_message(
            SetCommentRequest.new(0, 'test communique'))
        await client1.disconnect_and_wait()

        client1 = await self.new_lobby_client()
        await client1.join_lobby('Robert', 'cf585d509bf09ce1d2ff5d4226b7dacb')

        client2 = await self.new_lobby_client()
        await client2.send_message(JoinLobbyRequest.new('Bobert', 'cf585d509bf09ce1d2ff5d4226b7dacb'))
        await client2.assert_received_message(LobbyStateResponse.new([
            LobbyPlayer(username='Robert'),
            LobbyPlayer(username='Bobert'),
        ]))
        await client2.assert_no_more_messages()

    async def test_lobby_kick_on_limit(self):
        first_client = await self.new_lobby_client()
        await first_client.join_lobby('First Player', 'cf585d509bf09ce1d2ff5d4226b7dacb')
        for i in range(12):
            client = await self.new_lobby_client()
            await client.join_lobby(f'Player {i}', 'cf585d509bf09ce1d2ff5d4226b7dacb')

        # drain messages
        for i in range(12):
            await first_client.assert_received_message_type(LobbyStateResponse)
        await first_client.assert_no_more_messages()

        # make sure not disconnected (yet)
        await first_client.send_message(
            SetCommentRequest.new(0, 'test communique'))

        # connect 14th player
        client_over_limit = await self.new_lobby_client()
        await client_over_limit.join_lobby('Player Over Limit', 'cf585d509bf09ce1d2ff5d4226b7dacb')

        # first should be kicked
        await first_client.assert_connection_closed()

        # make sure the new player is not disconnected
        await client_over_limit.send_message(
            SetCommentRequest.new(0, 'test communique'))

    async def test_lobby_kick_on_limit2(self):
        first_client = await self.new_lobby_client()
        await first_client.join_lobby('First Player', 'cf585d509bf09ce1d2ff5d4226b7dacb')
        second_client = await self.new_lobby_client()
        await second_client.join_lobby('Second Player', 'cf585d509bf09ce1d2ff5d4226b7dacb')
        await first_client.close()

        for i in range(12):
            client = await self.new_lobby_client()
            await client.join_lobby(f'Player {i}', 'cf585d509bf09ce1d2ff5d4226b7dacb')

        # drain messages
        for i in range(13):
            await second_client.assert_received_message_type(LobbyStateResponse)
        await second_client.assert_no_more_messages()

        # make sure not disconnected (yet)
        await second_client.send_message(
            SetCommentRequest.new(0, 'test communique'))

        # connect 14th player
        client_over_limit = await self.new_lobby_client()
        await client_over_limit.join_lobby('Player Over Limit', 'cf585d509bf09ce1d2ff5d4226b7dacb')

        # second should be kicked
        await second_client.assert_connection_closed()

        # make sure the new player is not disconnected
        await client_over_limit.send_message(
            SetCommentRequest.new(0, 'test communique'))

    @patch('asyncio.sleep', return_value=asyncio.sleep(0))
    async def test_lobby_name_taken(self, mock_sleep):
        # Create a member
        member = await self.new_lobby_client()
        await member.join_lobby('member_name', 'cf585d509bf09ce1d2ff5d4226b7dacb')
        await member.close()

        guest = await self.new_lobby_client()
        await guest.join_lobby_guest('guest_name')

        mock_sleep.assert_not_called()

        await guest.send_message(NameTakenRequest.new('member_name'))
        await guest.assert_received_message(NameTakenResponseYes.new())
        mock_sleep.assert_called_once()
        mock_sleep.reset_mock()

        await guest.send_message(NameTakenRequest.new('some other member name'))
        await guest.assert_received_message(NameTakenResponseNo.new())
        mock_sleep.assert_called_once()
