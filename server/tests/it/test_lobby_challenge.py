from QRServer.common.messages import LobbyStateResponse, ChallengeMessage, LobbyChatMessage, ChallengeAuthMessage
from . import QuadradiusIntegrationTestCase


class LobbyIT(QuadradiusIntegrationTestCase):
    async def itSetUpConfig(self, config):
        config.set('auth.auto_register', True)

    async def test_lobby_challenge_user(self):
        first_client = await self.new_lobby_client()
        await first_client.join_lobby('First Player', 'cf585d509bf09ce1d2ff5d4226b7dacb')

        second_client = await self.new_lobby_client()
        await second_client.join_lobby('Second Player', 'cf585d509bf09ce1d2ff5d4226b7dacb')

        await first_client.assert_received_message_type(LobbyStateResponse)

        challenge_message = ChallengeMessage.new(challenged_idx=0, challenger_idx=1)
        await second_client.send_message(challenge_message)
        await first_client.assert_received_message(challenge_message)

        challenge_auth_message = ChallengeAuthMessage.new(challenged_idx=1, challenger_idx=0, auth='test')
        await first_client.send_message(challenge_auth_message)
        await second_client.assert_received_message(challenge_auth_message)

    async def test_lobby_send_error_challenge_user(self):
        first_client = await self.new_lobby_client()
        await first_client.join_lobby('First Player', 'cf585d509bf09ce1d2ff5d4226b7dacb')

        second_client = await self.new_lobby_client()
        await second_client.join_lobby('Second Player', 'cf585d509bf09ce1d2ff5d4226b7dacb')

        await first_client.drop()

        await second_client.send_message(ChallengeMessage.new(challenged_idx=0, challenger_idx=1))
        await second_client.assert_received_message_type(LobbyStateResponse)
        await second_client.assert_received_message(LobbyChatMessage.new(None, 'Could not challenge the user'))
        await second_client.assert_no_more_messages()
        await first_client.wait_for_disconnect()

    async def test_lobby_send_error_challenge_auth(self):
        first_client = await self.new_lobby_client()
        await first_client.join_lobby('First Player', 'cf585d509bf09ce1d2ff5d4226b7dacb')

        second_client = await self.new_lobby_client()
        await second_client.join_lobby('Second Player', 'cf585d509bf09ce1d2ff5d4226b7dacb')

        await first_client.assert_received_message_type(LobbyStateResponse)

        challenge_message = ChallengeMessage.new(challenged_idx=0, challenger_idx=1)
        await second_client.send_message(challenge_message)
        await first_client.assert_received_message(challenge_message)

        await second_client.drop()

        challenge_auth_message = ChallengeAuthMessage.new(challenged_idx=1, challenger_idx=0, auth='test')
        await first_client.send_message(challenge_auth_message)

        await first_client.assert_received_message_type(LobbyStateResponse)
        await first_client.assert_received_message(LobbyChatMessage.new(None, 'Could not respond to the challenge'))
        await first_client.assert_no_more_messages()
        await second_client.wait_for_disconnect()

    async def test_lobby_challenge_wrong_idx(self):
        first_client = await self.new_lobby_client()
        await first_client.join_lobby('First Player', 'cf585d509bf09ce1d2ff5d4226b7dacb')

        second_client = await self.new_lobby_client()
        await second_client.join_lobby('Second Player', 'cf585d509bf09ce1d2ff5d4226b7dacb')

        await first_client.assert_received_message_type(LobbyStateResponse)

        challenge_message = ChallengeMessage.new(challenged_idx=1, challenger_idx=0)
        await second_client.send_message(challenge_message)

        await second_client.assert_received_message(LobbyChatMessage.new(None, 'Could not challenge the user'))
        await first_client.assert_no_more_messages()

    async def test_lobby_challenge_oob_idx(self):
        first_client = await self.new_lobby_client()
        await first_client.join_lobby('First Player', 'cf585d509bf09ce1d2ff5d4226b7dacb')

        second_client = await self.new_lobby_client()
        await second_client.join_lobby('Second Player', 'cf585d509bf09ce1d2ff5d4226b7dacb')

        await first_client.assert_received_message_type(LobbyStateResponse)

        challenge_message = ChallengeMessage.new(challenged_idx=100, challenger_idx=1)
        await second_client.send_message(challenge_message)

        await second_client.assert_received_message(LobbyChatMessage.new(None, 'Could not challenge the user'))
        await first_client.assert_no_more_messages()
