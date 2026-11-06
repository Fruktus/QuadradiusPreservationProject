import asyncio

from QRServer.common.messages import AddStatsRequest, GameChatMessage, GrabPieceMessage, Message, \
    SettingsReadyOnMessage, SwitchPlayerMessage, VoidScoreRequest, VoidScoreResponse
from . import QuadradiusIntegrationTestCase

PASSWORD = 'ff585d509bf09ce1d2ff5d4226b7dacb'


class GameRecordingsIT(QuadradiusIntegrationTestCase):
    async def itSetUpConfig(self, config):
        config.set('auth.auto_register', True)

    async def _join_game(self, username: str, opponent_username: str):
        client = await self.new_game_client()
        await client.join_game(username, '1234', opponent_username, '4321', PASSWORD)
        return client

    async def _play_match(self) -> str:
        for username in ('PlayerA', 'PlayerB'):
            lobby_client = await self.new_lobby_client()
            await lobby_client.join_lobby(username, PASSWORD)

        client_a = await self._join_game('PlayerA', 'PlayerB')
        client_b = await self._join_game('PlayerB', 'PlayerA')

        # wait for each message to arrive, so that the order in which the server gets them is deterministic
        async def exchange(sender, receiver, message: Message):
            await sender.send_message(message)
            await receiver.assert_received_message(message)

        await exchange(client_a, client_b, SettingsReadyOnMessage.new(10, 2, 1, '0000FF'))
        await exchange(client_b, client_a, SettingsReadyOnMessage.new(10, 2, 1, '0000FF'))
        await exchange(client_a, client_b, GrabPieceMessage.new(3))
        await exchange(client_a, client_b, GameChatMessage.new('hello'))
        await exchange(client_b, client_a, SwitchPlayerMessage.new(3))

        await client_a.send_message(AddStatsRequest.new(6, 2, 40, 'medium', 'medium'))
        await client_b.send_message(AddStatsRequest.new(2, 6, 35, 'medium', 'medium'))

        match_id = await self._wait_for_match_result()
        await self._wait_for_recording(match_id)
        await client_a.disconnect()
        await client_b.disconnect()
        return match_id

    async def _wait_for_match_result(self) -> str:
        async def wait():
            while True:
                async with self.connector._transaction('r') as c:
                    await c.execute('select match_id from match_results')
                    row = await c.fetchone()
                if row:
                    return row[0]
                await asyncio.sleep(0.01)

        return await asyncio.wait_for(wait(), 2)

    async def _wait_for_recording(self, match_id: str):
        async def wait():
            while True:
                recording = await self.connector.get_match_recording(match_id)
                if recording:
                    return recording
                await asyncio.sleep(0.01)

        return await asyncio.wait_for(wait(), 2)

    async def test_recording_saved_without_chat_by_default(self):
        match_id = await self._play_match()

        recording = await self.connector.get_match_recording(match_id)
        self.assertEqual([Message.from_data(m.message) for m in recording], [
            SettingsReadyOnMessage.new(10, 2, 1, '0000FF'),
            SettingsReadyOnMessage.new(10, 2, 1, '0000FF'),
            GrabPieceMessage.new(3),
            SwitchPlayerMessage.new(3),
        ])

        user_a = await self.connector.get_user_by_username('PlayerA')
        user_b = await self.connector.get_user_by_username('PlayerB')
        self.assertEqual(recording[2].sender_id, user_a.user_id)
        self.assertEqual(recording[2].receiver_id, user_b.user_id)
        self.assertEqual(recording[3].sender_id, user_b.user_id)
        self.assertEqual(recording[3].receiver_id, user_a.user_id)

    async def test_recording_saved_with_chat_when_enabled(self):
        self.config.set('recordings.include_chat', True)

        match_id = await self._play_match()

        recording = await self.connector.get_match_recording(match_id)
        self.assertEqual([Message.from_data(m.message) for m in recording], [
            SettingsReadyOnMessage.new(10, 2, 1, '0000FF'),
            SettingsReadyOnMessage.new(10, 2, 1, '0000FF'),
            GrabPieceMessage.new(3),
            GameChatMessage.new('hello'),
            SwitchPlayerMessage.new(3),
        ])

    async def test_void_request_is_recorded(self):
        for username in ('PlayerA', 'PlayerB'):
            lobby_client = await self.new_lobby_client()
            await lobby_client.join_lobby(username, PASSWORD)

        client_a = await self._join_game('PlayerA', 'PlayerB')
        client_b = await self._join_game('PlayerB', 'PlayerA')

        ready = SettingsReadyOnMessage.new(10, 2, 1, '0000FF')
        await client_a.send_message(ready)
        await client_b.assert_received_message(ready)
        await client_b.send_message(ready)
        await client_a.assert_received_message(ready)

        await client_a.send_message(VoidScoreRequest.new())
        await client_b.assert_received_message(VoidScoreResponse.new())

        await client_a.send_message(AddStatsRequest.new(6, 2, 40, 'medium', 'medium'))
        await client_b.send_message(AddStatsRequest.new(2, 6, 35, 'medium', 'medium'))
        match_id = await self._wait_for_match_result()
        await self._wait_for_recording(match_id)

        user_a = await self.connector.get_user_by_username('PlayerA')
        recording = await self.connector.get_match_recording(match_id)
        self.assertEqual([Message.from_data(m.message) for m in recording], [
            ready,
            ready,
            VoidScoreResponse.new(),
        ])
        self.assertEqual(recording[2].sender_id, user_a.user_id)
