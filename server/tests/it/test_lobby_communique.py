from QRServer.common.classes import LobbyPlayer
from QRServer.common.messages import GUEST_COMMUNICATION_DISABLED_MESSAGE, JoinLobbyRequest, BroadcastCommentResponse, \
    LobbyChatMessage, LobbyStateResponse, SetCommentRequest
from . import QuadradiusIntegrationTestCase


class LobbyCommuniqueIT(QuadradiusIntegrationTestCase):
    async def itSetUpConfig(self, config):
        config.set('auth.auto_register', True)

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

    async def test_communique_blocked_for_guests(self):
        client1 = await self.new_lobby_client()
        await client1.join_lobby('Robert GUEST', '24f380279d84e2e715f80ed14b1db063')

        client2 = await self.new_lobby_client()
        await client2.join_lobby('Bobert', 'cf585d509bf09ce1d2ff5d4226b7dacb')
        await client1.assert_received_message_type(LobbyStateResponse)

        await client1.send_message(
            SetCommentRequest.new(0, 'test communique'))
        await client1.assert_received_message(
            LobbyChatMessage.new(None, GUEST_COMMUNICATION_DISABLED_MESSAGE))
        await client2.assert_no_more_messages()
