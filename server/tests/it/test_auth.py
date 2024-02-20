from QRServer.common.messages import JoinLobbyRequest, LobbyBadMemberResponse, JoinGameRequest, PlayerCountResponse, \
    HelloGameRequest
from . import QuadradiusIntegrationTestCase


class AuthEnabledIT(QuadradiusIntegrationTestCase):
    async def itSetUpConfig(self, config):
        config.set('auth.disable', False)
        config.set('auth.auto_register', False)

    async def test_lobby_guest(self):
        client = await self.new_lobby_client()
        await client.join_lobby_guest('John')

    async def test_lobby_wrong_password(self):
        client = await self.new_lobby_client()
        await client.send_message(JoinLobbyRequest.new('John', '098f6bcd4621d373cade4e832627b4f6'))
        await client.assert_received_message_type(LobbyBadMemberResponse)

        client = await self.new_lobby_client()
        await client.send_message(JoinLobbyRequest.new('John', 'ad0234829205b9033196ba818f7a872b'))
        await client.assert_received_message_type(LobbyBadMemberResponse)

    async def test_game_guest(self):
        client = await self.new_game_client()
        await client.send_message(HelloGameRequest.new())
        await client.send_message(JoinGameRequest.new(
            'John GUEST', '1234',
            'John GUEST', '4321',
            '24f380279d84e2e715f80ed14b1db063'))
        await client.assert_received_message_type(PlayerCountResponse)

    async def test_game_wrong_password(self):
        client = await self.new_game_client()
        await client.send_message(HelloGameRequest.new())
        await client.send_message(JoinGameRequest.new(
            'John', '1234',
            'John', '4321',
            '098f6bcd4621d373cade4e832627b4f6'))
        await client.assert_connection_closed()
        await client.assert_no_more_messages()


class AuthDisabledIT(QuadradiusIntegrationTestCase):
    async def itSetUpConfig(self, config):
        config.set('auth.disable', True)
        config.set('auth.auto_register', False)

    async def test_lobby_guest(self):
        client = await self.new_lobby_client()
        await client.join_lobby_guest('John')

    async def test_lobby_any_password(self):
        client = await self.new_lobby_client()
        await client.join_lobby('John', '098f6bcd4621d373cade4e832627b4f6')
        await client.disconnect_and_wait()

        client = await self.new_lobby_client()
        await client.join_lobby('John', 'ad0234829205b9033196ba818f7a872b')
        await client.disconnect_and_wait()

    async def test_game_guest(self):
        client = await self.new_game_client()
        await client.send_message(HelloGameRequest.new())
        await client.send_message(JoinGameRequest.new(
            'John GUEST', '1234',
            'John GUEST', '4321',
            '24f380279d84e2e715f80ed14b1db063'))
        await client.assert_received_message_type(PlayerCountResponse)

    async def test_game_any_password(self):
        client = await self.new_game_client()
        await client.send_message(HelloGameRequest.new())
        await client.send_message(JoinGameRequest.new(
            'John', '1234',
            'John', '4321',
            '098f6bcd4621d373cade4e832627b4f6'))
        await client.assert_received_message_type(PlayerCountResponse)

        client = await self.new_game_client()
        await client.send_message(HelloGameRequest.new())
        await client.send_message(JoinGameRequest.new(
            'John', '1234',
            'John', '4321',
            'ad0234829205b9033196ba818f7a872b'))
        await client.assert_received_message_type(PlayerCountResponse)


class AuthAutoRegisterIT(QuadradiusIntegrationTestCase):
    async def itSetUpConfig(self, config):
        config.set('auth.disable', False)
        config.set('auth.auto_register', True)

    async def test_lobby_guest(self):
        client = await self.new_lobby_client()
        await client.join_lobby_guest('John')

    async def test_lobby_wrong_password(self):
        valid_pass = '098f6bcd4621d373cade4e832627b4f6'
        invalid_pass = 'ad0234829205b9033196ba818f7a872b'

        client = await self.new_lobby_client()
        await client.join_lobby('John', valid_pass)
        await client.disconnect_and_wait()

        client = await self.new_lobby_client()
        await client.join_lobby('John', valid_pass)
        await client.disconnect_and_wait()

        client = await self.new_lobby_client()
        await client.send_message(JoinLobbyRequest.new('John', invalid_pass))
        await client.assert_received_message_type(LobbyBadMemberResponse)

        client = await self.new_lobby_client()
        await client.join_lobby('John', valid_pass)
        await client.disconnect_and_wait()

    async def test_game_guest(self):
        client = await self.new_game_client()
        await client.send_message(HelloGameRequest.new())
        await client.send_message(JoinGameRequest.new(
            'John GUEST', '1234',
            'John GUEST', '4321',
            '24f380279d84e2e715f80ed14b1db063'))
        await client.assert_received_message_type(PlayerCountResponse)

    async def test_game_wrong_password(self):
        client = await self.new_game_client()
        await client.send_message(HelloGameRequest.new())
        await client.send_message(JoinGameRequest.new(
            'John', '1234',
            'John', '4321',
            '098f6bcd4621d373cade4e832627b4f6'))
        await client.assert_received_message_type(PlayerCountResponse)

        client = await self.new_game_client()
        await client.send_message(HelloGameRequest.new())
        await client.send_message(JoinGameRequest.new(
            'John', '1234',
            'John', '4321',
            'ad0234829205b9033196ba818f7a872b'))
        await client.assert_connection_closed()
        await client.assert_no_more_messages()

        client = await self.new_game_client()
        await client.send_message(HelloGameRequest.new())
        await client.send_message(JoinGameRequest.new(
            'John', '1234',
            'John', '4321',
            '098f6bcd4621d373cade4e832627b4f6'))
        await client.assert_received_message_type(PlayerCountResponse)
