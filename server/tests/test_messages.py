import unittest
from datetime import datetime

from QRServer.common import messages
from QRServer.common.classes import GameResultHistory, RankingEntry
from QRServer.common.messages import AddStatsRequest, AssignNextPowerCountMessage, AssignPowerSquareMessage, \
    BankruptActionMessage, BroadcastCommentResponse, ChangePasswordRequest, ChangePasswordResponseOk, \
    CrossDomainPolicyAllowAllResponse, DisconnectRequest, GetPowerSquareMessage, GrabPieceMessage, HelloGameRequest, \
    HelloLobbyRequest, JoinGameRequest, GameChatMessage, JumpOnPieceMessage, LastLoggedResponse, \
    LobbyBadMemberResponse, LobbyChatMessage, LobbyDuplicateResponse, LobbyStateResponse, NameTakenRequest, \
    NameTakenResponse, NameTakenResponseNo, NameTakenResponseYes, NewGridCoordMessage, NukeMessage, OldSwfResponse, \
    OpponentDeadResponse, PlayerCountResponse, PolicyFileRequest, PowerNoEffectMessage, RecursiveDoneMessage, \
    ReleasePieceMessage, RemoveOneWayWallMessage, RemovePlayerMessage, ServerAliveRequest, ServerAliveResponse, \
    ServerPingRequest, ServerRecentRequest, ServerRankingRequest, JoinLobbyRequest, LastPlayedResponse, \
    ServerRankingThisMonthResponse, SetCommentRequest, SettingsArenaSizeMessage, SettingsColorMessage, \
    SettingsLoadedMessage, SettingsReadyOffMessage, SettingsReadyOnAgainMessage, SettingsSquadronSizeMessage, \
    SettingsTimerMessage, SettingsTopBottomMessage, SwitchPlayerMessage, SwitcherooMessage, UsePowerMessage, \
    ChallengeMessage, ChallengeAuthMessage, SettingsReadyOnMessage, ResignMessage, VoidScoreRequest, VoidScoreResponse


class MessagesTest(unittest.TestCase):
    def test_every_message_has_unique_id(self):
        ids = set()
        for message in getattr(messages, "__message_classes"):
            self.assertIsNotNone(message.message_type_id)
            self.assertNotIn(message.message_type_id, ids)
            ids.add(message.message_type_id)

    def test_every_message_has_mapping(self):
        self.assertEqual(messages.get_message_type_from_id(0), DisconnectRequest)
        self.assertEqual(messages.get_message_type_from_id(1), PolicyFileRequest)
        self.assertEqual(messages.get_message_type_from_id(2), HelloLobbyRequest)
        self.assertEqual(messages.get_message_type_from_id(3), JoinLobbyRequest)
        self.assertEqual(messages.get_message_type_from_id(4), HelloGameRequest)
        self.assertEqual(messages.get_message_type_from_id(5), JoinGameRequest)
        self.assertEqual(messages.get_message_type_from_id(6), ServerRecentRequest)
        self.assertEqual(messages.get_message_type_from_id(7), ServerRankingRequest)
        self.assertEqual(messages.get_message_type_from_id(8), ServerAliveRequest)
        self.assertEqual(messages.get_message_type_from_id(9), ServerPingRequest)

        self.assertEqual(messages.get_message_type_from_id(10), SetCommentRequest)
        self.assertEqual(messages.get_message_type_from_id(11), AddStatsRequest)
        self.assertEqual(messages.get_message_type_from_id(12), VoidScoreRequest)
        self.assertEqual(messages.get_message_type_from_id(13), NameTakenRequest)
        self.assertEqual(messages.get_message_type_from_id(14), ChangePasswordRequest)
        self.assertEqual(messages.get_message_type_from_id(15), CrossDomainPolicyAllowAllResponse)
        self.assertEqual(messages.get_message_type_from_id(16), PlayerCountResponse)
        self.assertEqual(messages.get_message_type_from_id(17), BroadcastCommentResponse)
        self.assertEqual(messages.get_message_type_from_id(18), OldSwfResponse)
        self.assertEqual(messages.get_message_type_from_id(19), NameTakenResponse)

        self.assertEqual(messages.get_message_type_from_id(20), ServerAliveResponse)
        self.assertEqual(messages.get_message_type_from_id(21), LobbyDuplicateResponse)
        self.assertEqual(messages.get_message_type_from_id(22), LobbyBadMemberResponse)
        self.assertEqual(messages.get_message_type_from_id(23), LastLoggedResponse)
        self.assertEqual(messages.get_message_type_from_id(24), LastPlayedResponse)
        self.assertEqual(messages.get_message_type_from_id(25), ServerRankingThisMonthResponse)
        self.assertEqual(messages.get_message_type_from_id(26), LobbyStateResponse)
        self.assertEqual(messages.get_message_type_from_id(27), OpponentDeadResponse)
        self.assertEqual(messages.get_message_type_from_id(28), VoidScoreResponse)
        self.assertEqual(messages.get_message_type_from_id(29), NameTakenResponseNo)

        self.assertEqual(messages.get_message_type_from_id(30), NameTakenResponseYes)
        self.assertEqual(messages.get_message_type_from_id(31), ChangePasswordResponseOk)
        self.assertEqual(messages.get_message_type_from_id(32), UsePowerMessage)
        self.assertEqual(messages.get_message_type_from_id(33), GameChatMessage)
        self.assertEqual(messages.get_message_type_from_id(34), LobbyChatMessage)
        self.assertEqual(messages.get_message_type_from_id(35), GrabPieceMessage)
        self.assertEqual(messages.get_message_type_from_id(36), ReleasePieceMessage)
        self.assertEqual(messages.get_message_type_from_id(37), SwitchPlayerMessage)
        self.assertEqual(messages.get_message_type_from_id(38), RecursiveDoneMessage)
        self.assertEqual(messages.get_message_type_from_id(39), SwitcherooMessage)

        self.assertEqual(messages.get_message_type_from_id(40), RemoveOneWayWallMessage)
        self.assertEqual(messages.get_message_type_from_id(41), BankruptActionMessage)
        self.assertEqual(messages.get_message_type_from_id(42), RemovePlayerMessage)
        self.assertEqual(messages.get_message_type_from_id(43), PowerNoEffectMessage)
        self.assertEqual(messages.get_message_type_from_id(44), NukeMessage)
        self.assertEqual(messages.get_message_type_from_id(45), JumpOnPieceMessage)
        self.assertEqual(messages.get_message_type_from_id(46), GetPowerSquareMessage)
        self.assertEqual(messages.get_message_type_from_id(47), SettingsLoadedMessage)
        self.assertEqual(messages.get_message_type_from_id(48), AssignPowerSquareMessage)
        self.assertEqual(messages.get_message_type_from_id(49), AssignNextPowerCountMessage)

        self.assertEqual(messages.get_message_type_from_id(50), NewGridCoordMessage)
        self.assertEqual(messages.get_message_type_from_id(51), ResignMessage)
        self.assertEqual(messages.get_message_type_from_id(52), ChallengeMessage)
        self.assertEqual(messages.get_message_type_from_id(53), ChallengeAuthMessage)
        self.assertEqual(messages.get_message_type_from_id(54), SettingsReadyOffMessage)
        self.assertEqual(messages.get_message_type_from_id(55), SettingsArenaSizeMessage)
        self.assertEqual(messages.get_message_type_from_id(56), SettingsSquadronSizeMessage)
        self.assertEqual(messages.get_message_type_from_id(57), SettingsTimerMessage)
        self.assertEqual(messages.get_message_type_from_id(58), SettingsTopBottomMessage)
        self.assertEqual(messages.get_message_type_from_id(59), SettingsColorMessage)

        self.assertEqual(messages.get_message_type_from_id(60), SettingsReadyOnMessage)
        self.assertEqual(messages.get_message_type_from_id(61), SettingsReadyOnAgainMessage)


class RequestMessagesTest(unittest.TestCase):
    def test_start_game_request(self):
        msg = messages._parse_data('<QR_G>')
        self.assertTrue(isinstance(msg, HelloGameRequest))

    def test_start_game_request_invalid(self):
        msg = messages._parse_data('<QR_G>~2')
        self.assertIsNone(msg)

    def test_join_game_request(self):
        msg = messages._parse_data('<L>~1~2~3~4~5')
        if isinstance(msg, JoinGameRequest):
            self.assertEqual('1', msg.get_username())
            self.assertEqual('2', msg.get_auth())
            self.assertEqual('3', msg.get_opponent_username())
            self.assertEqual('4', msg.get_opponent_auth())
            self.assertEqual('5', msg.get_password())
        else:
            self.fail()

    def test_join_game_request_invalid(self):
        msg = messages._parse_data('<L>~1')
        self.assertIsNone(msg)
        msg = messages._parse_data('<L>~1~2~3~4')
        self.assertIsNone(msg)
        msg = messages._parse_data('<L>~1~2~3~4~5~6')
        self.assertIsNone(msg)

    def test_game_chat_request(self):
        msg = messages._parse_data('<S>~<CHAT>~xyz')
        if isinstance(msg, GameChatMessage):
            self.assertEqual('xyz', msg.get_text())
        else:
            self.fail()

    def test_game_chat_request_invalid(self):
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
        if isinstance(msg, ServerRankingRequest):
            self.assertEqual(1, msg.get_year())
            self.assertEqual(2, msg.get_month())
        else:
            self.fail()

    def test_server_ranking_invalid(self):
        msg = messages._parse_data('<SERVER>~<RANKING>~1')
        self.assertIsNone(msg)
        msg = messages._parse_data('<SERVER>~<RANKING>~1~a')
        self.assertIsNone(msg)
        msg = messages._parse_data('<SERVER>~<RANKING>~~a')
        self.assertIsNone(msg)

    def test_join_lobby_request(self):
        msg = messages._parse_data('<L>~a~b')
        if isinstance(msg, JoinLobbyRequest):
            self.assertEqual('a', msg.get_username())
            self.assertEqual('b', msg.get_password())
        else:
            self.fail()

    def test_use_power_request_invalid(self):
        msg = messages._parse_data('<S>~<USE_POWER>~UNKNOWN~piece')
        self.assertIsNone(msg)

    def test_use_power_request(self):
        msg = messages._parse_data('<S>~<USE_POWER>~PLATEAU~9')
        if isinstance(msg, UsePowerMessage):
            self.assertEqual('PLATEAU', msg.get_power_name())
            self.assertEqual(9, msg.get_piece())
            self.assertIsNone(msg.get_power_arg())
        else:
            self.fail()

    def test_use_power_request2(self):
        msg = messages._parse_data('<S>~<USE_POWER>~PLATEAU~7~arg')
        if isinstance(msg, UsePowerMessage):
            self.assertEqual('PLATEAU', msg.get_power_name())
            self.assertEqual(7, msg.get_piece())
            self.assertEqual('arg', msg.get_power_arg())
        else:
            self.fail()

    def test_challenge_request(self):
        msg = messages._parse_data('<S>~1~2~<SHALLWEPLAYAGAME?>')
        if isinstance(msg, ChallengeMessage):
            self.assertEqual(1, msg.get_challenged_idx())
            self.assertEqual(2, msg.get_challenger_idx())
        else:
            self.fail()

    def test_challenge_auth_request(self):
        msg = messages._parse_data('<S>~1~2~<AUTHENTICATION>~asdf')
        if isinstance(msg, ChallengeAuthMessage):
            self.assertEqual(1, msg.get_challenged_idx())
            self.assertEqual(2, msg.get_challenger_idx())
            self.assertEqual('asdf', msg.get_auth())
        else:
            self.fail()

    def test_settings_ready_on_request(self):
        msg = messages._parse_data('<S>~<SETTINGS>~<READY_ON>~10~2~1~0000FF')
        if isinstance(msg, SettingsReadyOnMessage):
            self.assertEqual(10, msg.get_grid_size())
            self.assertEqual(2, msg.get_player_size())
            self.assertEqual(1, msg.get_decoration_color())
            self.assertEqual('0000FF', msg.get_text_color())
        else:
            self.fail()

    def test_resign_request(self):
        msg = messages._parse_data('<S>~<SETTINGS>~<RESIGN>')
        self.assertTrue(isinstance(msg, ResignMessage))


class ResponseMessagesTest(unittest.TestCase):
    def test_last_played_response(self):
        start = datetime.strptime('09:10:31', '%H:%M:%S')
        finish = datetime.strptime('09:15:32', '%H:%M:%S')
        msg = LastPlayedResponse.new([
            GameResultHistory(
                player_won='a',
                player_lost='b',
                won_score=7,
                lost_score=0,
                start=start,
                finish=finish,
                moves=15),
            GameResultHistory(
                player_won='c',
                player_lost='d',
                won_score=8,
                lost_score=2,
                start=start,
                finish=finish,
                moves=10),
        ])
        data = msg.to_data()
        self.assertEqual(
            b'<S>~<SERVER>~<LAST_PLAYED>~'
            b' # # ~ # # ~ # # ~'
            b' # # ~ # # ~ # # ~'
            b' # # ~ # # ~ # # ~'
            b' # # ~ # # ~ # # ~'
            b' # # ~'
            b'c beat d#8-2#5:01~'
            b'a beat b#7-0#5:01\x00',
            data)

    def test_last_played_response_empty(self):
        msg = LastPlayedResponse.new([])
        data = msg.to_data()
        self.assertEqual(
            b'<S>~<SERVER>~<LAST_PLAYED>~'
            b' # # ~ # # ~'
            b' # # ~ # # ~ # # ~'
            b' # # ~ # # ~ # # ~'
            b' # # ~ # # ~ # # ~'
            b' # # ~ # # ~ # # ~'
            b'No recent battles# # \x00',
            data)

    def test_server_ranking_this_month_response(self):
        msg = ServerRankingThisMonthResponse.new([
            RankingEntry(
                username='test',
                user_id='',
                wins=5,
                games=20,
            ),
            RankingEntry(
                username='test2',
                user_id='',
                wins=7,
                games=7,
            ),
        ])
        data = msg.to_data()
        self.assertEqual(
            b'<S>~<SERVER>~<RANKING(thisMonth)>~'
            b'test~5~20~'
            b'test2~7~7\x00',
            data)

    def test_use_power_response_exception(self):
        self.assertRaises(ValueError, lambda: UsePowerMessage.new('power_name', 12))

    def test_use_power_response(self):
        msg = UsePowerMessage.new('PLATEAU', 7)
        data = msg.to_data()
        self.assertEqual(
            b'<S>~<USE_POWER>~PLATEAU~7\x00',
            data)

    def test_use_power_response2(self):
        msg = UsePowerMessage.new('PLATEAU', 4, 'arg')
        data = msg.to_data()
        self.assertEqual(
            data,
            b'<S>~<USE_POWER>~PLATEAU~4~arg\x00')
