import asyncio
from unittest.mock import patch

from QRServer.common.messages import JoinLobbyRequest, LobbyStateResponse
from QRServer.lobby.lobbyserver import LobbyPlayer
from QRServer.server import QRServer

from . import QuadradiusIntegrationTestCase, TestClientConnection as ClientConnection

PASSWORD_HASH = 'cf585d509bf09ce1d2ff5d4226b7dacb'


class LoopbackHelperTest(QuadradiusIntegrationTestCase):
    async def test_is_loopback(self):
        for host in ['127.0.0.1', '127.1.2.3', '::1', '::ffff:127.0.0.1']:
            with self.subTest(host=host):
                self.assertTrue(QRServer._is_loopback(host))
        for host in ['192.168.1.10', '203.0.113.7', '2001:db8::1', '::ffff:203.0.113.7', 'garbage', '']:
            with self.subTest(host=host):
                self.assertFalse(QRServer._is_loopback(host))


class ProxyProtocolIT(QuadradiusIntegrationTestCase):
    async def itSetUpConfig(self, config):
        config.set('auth.auto_register', True)
        config.set('server.use_proxy_protocol', True)

    async def _lobby_client_sending(self, prefix: bytes) -> ClientConnection:
        host, port, *_ = self.server.lobby_socks[0].getsockname()
        reader, writer = await asyncio.open_connection(host, port)
        writer.write(prefix)
        client = ClientConnection(self.server, reader, writer, True)
        self._clients.append(client)
        return client

    async def _assert_closed_by_server(self, client: ClientConnection):
        await asyncio.wait_for(client.reader.read(), 2)  # returns at EOF
        self.assertTrue(client.reader.at_eof())

    async def test_loopback_with_proxied_header(self):
        client = await self._lobby_client_sending(b'PROXY TCP4 203.0.113.7 127.0.0.1 40000 3000\r\n')
        with self.assertLogs('qr.client_handler', level='INFO') as logs:
            await client.send_message(JoinLobbyRequest.new('asd', PASSWORD_HASH))
            await client.assert_received_message(LobbyStateResponse.new([LobbyPlayer(username='asd')]))

        self.assertEqual(self.server.lobby_server.clients[0].addr, ('203.0.113.7', 40000))
        self.assertIn("Authenticated user: 'asd'@[203.0.113.7]:40000", '\n'.join(logs.output))

    async def test_loopback_with_proxy_header_ipv6(self):
        client = await self._lobby_client_sending(b'PROXY TCP6 2001:db8::1 ::ffff:127.0.0.1 40001 3000\r\n')
        await client.send_message(JoinLobbyRequest.new('asd', PASSWORD_HASH))
        await client.assert_received_message(LobbyStateResponse.new([LobbyPlayer(username='asd')]))

        self.assertEqual(self.server.lobby_server.clients[0].addr, ('2001:db8::1', 40001))

    async def test_loopback_with_unknown_header_keeps_socket_address(self):
        # fallback when ip provided by proxy was not parseable - connection should still work
        client = await self._lobby_client_sending(b'PROXY UNKNOWN\r\n')
        await client.send_message(JoinLobbyRequest.new('asd', PASSWORD_HASH))
        await client.assert_received_message(LobbyStateResponse.new([LobbyPlayer(username='asd')]))

        self.assertEqual(self.server.lobby_server.clients[0].addr[0], '127.0.0.1')

    async def test_loopback_without_header_is_rejected(self):
        # If proxy protocol is enforced then local connections (from proxy) are required
        # to provide proxy header
        client = await self._lobby_client_sending(b'')
        with self.assertLogs('qr.server', level='WARNING') as logs:
            await client.send_message(JoinLobbyRequest.new('asd', PASSWORD_HASH))
            await self._assert_closed_by_server(client)

        self.assertIn('Rejected loopback peer', '\n'.join(logs.output))
        self.assertIsNone(self.server.lobby_server.clients[0])

    async def test_loopback_with_garbage_is_rejected(self):
        client = await self._lobby_client_sending(b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09')
        await self._assert_closed_by_server(client)
        self.assertIsNone(self.server.lobby_server.clients[0])

    async def test_non_loopback_peer_skips_proxy_parsing(self):
        # We still want to allow direct connection to game server (without proxy and bridge)
        # for clients using Launcher

        # the test client can only connect from loopback, so pretend it is a remote peer
        with patch.object(QRServer, '_is_loopback', return_value=False):
            client = await self._lobby_client_sending(b'')
            # a spoofed header from a non-loopback peer is just protocol garbage, never an address
            await client.send_message(JoinLobbyRequest.new('asd', PASSWORD_HASH))
            await client.assert_received_message(LobbyStateResponse.new([LobbyPlayer(username='asd')]))

        self.assertEqual(self.server.lobby_server.clients[0].addr[0], '127.0.0.1')

    async def test_ignore_non_loopback_spoofed_headers(self):
        with patch.object(QRServer, '_is_loopback', return_value=False):
            client = await self._lobby_client_sending(b'PROXY TCP4 203.0.113.7 127.0.0.1 40000 3000\r\n')
            await client.send_message(JoinLobbyRequest.new('asd', PASSWORD_HASH))
            await asyncio.sleep(0.2)

        for c in self.server.lobby_server.clients:
            self.assertTrue(c is None or c.addr[0] != '203.0.113.7')


class ProxyProtocolDisabledIT(QuadradiusIntegrationTestCase):
    async def itSetUpConfig(self, config):
        config.set('auth.auto_register', True)

    async def test_flag_off_loopback_works_without_header(self):
        client = await self.new_lobby_client()
        await client.send_message(JoinLobbyRequest.new('asd', PASSWORD_HASH))
        await client.assert_received_message(LobbyStateResponse.new([LobbyPlayer(username='asd')]))

        self.assertEqual(self.server.lobby_server.clients[0].addr[0], '127.0.0.1')
