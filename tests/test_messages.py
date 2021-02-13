import unittest
from datetime import datetime

from QRServer.common import messages
from QRServer.common.classes import GameResultHistory, RankingEntry
from QRServer.common.messages import HelloGameRequest, JoinGameRequest, ChatRequest, ServerRecentRequest, \
    ServerRankingRequest, JoinLobbyRequest, LastPlayedResponse, ServerRankingResponse


class RequestMessagesTest(unittest.TestCase):
    def test_start_game_request(self):
        msg = messages._parse_data('<QR_G>')
        self.assertTrue(isinstance(msg, HelloGameRequest))

    def test_start_game_request_invalid(self):
        msg = messages._parse_data('<QR_G>~2')
        self.assertIsNone(msg)

    def test_join_game_request(self):
        msg = messages._parse_data('<L>~1~2~3~4~5')
        self.assertTrue(isinstance(msg, JoinGameRequest))
        self.assertEqual(msg.get_username(), '1')
        self.assertEqual(msg.get_auth(), '2')
        self.assertEqual(msg.get_opponent_username(), '3')
        self.assertEqual(msg.get_opponent_auth(), '4')
        self.assertEqual(msg.get_password(), '5')

    def test_join_game_request_invalid(self):
        msg = messages._parse_data('<L>~1')
        self.assertIsNone(msg)
        msg = messages._parse_data('<L>~1~2~3~4')
        self.assertIsNone(msg)
        msg = messages._parse_data('<L>~1~2~3~4~5~6')
        self.assertIsNone(msg)

    def test_chat_request(self):
        msg = messages._parse_data('<S>~<CHAT>~xyz')
        self.assertTrue(isinstance(msg, ChatRequest))
        self.assertEqual(msg.get_text(), 'xyz')

    def test_chat_request_invalid(self):
        msg = messages._parse_data('<S>~<CHAT>')
        self.assertIsNone(msg)
        msg = messages._parse_data('<S>~<CHAT>~a~b')
        self.assertIsNone(msg)

    def test_server_recent_request(self):
        msg = messages._parse_data('<SERVER>~<RECENT>')
        self.assertTrue(isinstance(msg, ServerRecentRequest))

    def test_server_recent_request_invalid(self):
        msg = messages._parse_data('<SERVER>~<RECENT>~a')
        self.assertIsNone(msg)

    def test_server_ranking_request(self):
        msg = messages._parse_data('<SERVER>~<RANKING>~1~2')
        self.assertTrue(isinstance(msg, ServerRankingRequest))
        self.assertEqual(msg.get_year(), 1)
        self.assertEqual(msg.get_month(), 2)

    def test_server_ranking_invalid(self):
        msg = messages._parse_data('<SERVER>~<RANKING>~1')
        self.assertIsNone(msg)
        msg = messages._parse_data('<SERVER>~<RANKING>~1~a')
        self.assertIsNone(msg)
        msg = messages._parse_data('<SERVER>~<RANKING>~~a')
        self.assertIsNone(msg)

    def test_join_lobby_request(self):
        msg = messages._parse_data('<L>~a~b')
        self.assertTrue(isinstance(msg, JoinLobbyRequest))
        self.assertEqual(msg.get_username(), 'a')
        self.assertEqual(msg.get_password(), 'b')


class ResponseMessagesTest(unittest.TestCase):
    def test_last_played_response(self):
        start = datetime.strptime('09:10:31', '%H:%M:%S')
        finish = datetime.strptime('09:15:32', '%H:%M:%S')
        msg = LastPlayedResponse([
            GameResultHistory(
                player_won='a',
                player_lost='b',
                won_score=7,
                lost_score=0,
                start=start,
                finish=finish),
            GameResultHistory(
                player_won='c',
                player_lost='d',
                won_score=8,
                lost_score=2,
                start=start,
                finish=finish),
        ])
        data = msg.to_data()
        self.assertEqual(
            data,
            b'<S>~<SERVER>~<LAST_PLAYED>~'
            b'a beat b#7-0#5:01~'
            b'c beat d#8-2#5:01~'
            b' # # ~ # # ~ # # ~'
            b' # # ~ # # ~ # # ~'
            b' # # ~ # # ~ # # ~'
            b' # # ~ # # ~ # # ~'
            b' # # \x00')

    def test_server_ranking_response(self):
        msg = ServerRankingResponse(True, [
            RankingEntry(
                player='test',
                wins=5,
                games=20),
            RankingEntry(
                player='test2',
                wins=7,
                games=7),
        ])
        data = msg.to_data()
        self.assertEqual(
            data,
            b'<S>~<SERVER>~<RANKING(thisMonth)>~'
            b'test~5~20~'
            b'test2~7~7\x00')

    def test_server_ranking_response2(self):
        msg = ServerRankingResponse(False, [])
        data = msg.to_data()
        self.assertEqual(
            data,
            b'<S>~<SERVER>~<RANKING>\x00')
