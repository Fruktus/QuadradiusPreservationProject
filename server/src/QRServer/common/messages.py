from abc import ABCMeta
from datetime import datetime
from typing import List, Optional

from QRServer.common import powers
from QRServer.common.classes import GameResultHistory, MatchStats, RankingEntry, LobbyPlayer

delim = '~'


class Message:
    args: List[str]
    prefix = None
    argc = None

    def __init__(self, args: List[str]) -> None:
        self.args = args

        for arg in self.args:
            if not isinstance(arg, str):
                raise ValueError(f'Wrong argument type: {type(arg)}')

        prefix = self.__class__.prefix
        argc = self.__class__.argc

        if prefix is None or argc is None:
            raise AttributeError()

        if not _valid(args, prefix, argc):
            raise ValueError(f"Invalid args for {__class__}: {args}")

    def to_data(self) -> bytes:
        return delim.join(self.args).encode('ascii', 'replace') + b'\x00'

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.args.__repr__()})'

    def __eq__(self, other):
        if not isinstance(other, Message):
            return False
        return self.args == other.args


################################################################################
# REQUESTS
################################################################################


class RequestMessage(Message):
    def __init__(self, args: List[str]) -> None:
        super().__init__(args)

    @staticmethod
    def from_data(data: bytes):
        return _parse_data(data.decode('ascii', 'replace'))


class DisconnectRequest(RequestMessage):
    prefix = ['<DISCONNECTED>']
    argc = [1]

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return __class__(args)

    @classmethod
    def new(cls):
        return cls.from_args(DisconnectRequest.prefix)


class PolicyFileRequest(RequestMessage):
    prefix = ['<policy-file-request/>']
    argc = [1]

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return __class__(args)


class HelloLobbyRequest(RequestMessage):
    prefix = ['<QR_L>']
    argc = [1]

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return __class__(args)

    def get_swf_version(self):
        return int(self.args[1])


class JoinLobbyRequest(RequestMessage):
    prefix = ['<L>']
    argc = [3]

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return __class__(args)

    @classmethod
    def new(cls, username, password):
        return cls.from_args([*JoinLobbyRequest.prefix, username, password])

    def get_username(self):
        return self.args[1]

    def get_password(self):
        return self.args[2]


class HelloGameRequest(RequestMessage):
    prefix = ['<QR_G>']
    argc = [1]

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return __class__(args)


class JoinGameRequest(RequestMessage):
    prefix = ['<L>']
    argc = [6]

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return __class__(args)

    def get_username(self):
        return self.args[1]

    def get_auth(self):
        return self.args[2]

    def get_opponent_username(self):
        return self.args[3]

    def get_opponent_auth(self):
        return self.args[4]

    def get_password(self):
        return self.args[5]


class ServerRecentRequest(RequestMessage):
    prefix = ['<SERVER>', '<RECENT>']
    argc = [2]

    @staticmethod
    def from_args(args: List[str]):
        return __class__(args)

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)


class ServerRankingRequest(RequestMessage):
    prefix = ['<SERVER>', '<RANKING>']
    argc = [4]

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)

        self._year = int(self.args[2])
        self._month = int(self.args[3])

    @staticmethod
    def from_args(args: List[str]):
        return __class__(args)

    def get_year(self) -> int:
        return self._year

    def get_month(self) -> int:
        return self._month


class ServerAliveRequest(RequestMessage):
    prefix = ['<SERVER>', '<ALIVE?>']
    argc = [2]

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return __class__(args)


class ServerPingRequest(RequestMessage):
    prefix = ['<SERVER>', '<PING>']
    argc = [2]

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return __class__(args)


class SetCommentRequest(RequestMessage):
    prefix = ['<SERVER>', '<COMMENT>']
    argc = [4]

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return __class__(args)

    @classmethod
    def new(cls, idx: int, comment: str):
        return cls([*cls.prefix, str(idx), comment])

    def get_idx(self) -> int:
        return int(self.args[2])

    def get_comment(self) -> str:
        return self.args[3]


class AddStatsRequest(RequestMessage):
    prefix = ['<SERVER>', '<STATS>']
    argc = [7]
    grid_sizes = ['small', 'medium', 'large (default)', 'maximum']
    squadron_sizes = ['small', 'medium', 'large (default)', 'maximum']

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)
        self._owner_piece_count = int(self.args[2])
        self._opponent_piece_count = int(self.args[3])
        self._cycle_counter = int(self.args[4])
        self._grid_size = self.args[5]
        self._squadron_size = self.args[6]

    @staticmethod
    def from_args(args: List[str]):
        return __class__(args)

    def get_owner_piece_count(self) -> int:
        return self._owner_piece_count

    def get_opponent_piece_count(self) -> int:
        return self._opponent_piece_count

    def get_cycle_counter(self) -> int:
        return self._cycle_counter

    def get_grid_size(self) -> str:
        return self._grid_size

    def get_squadron_size(self) -> str:
        return self._squadron_size

    def to_stats(self) -> MatchStats:
        return MatchStats(
            own_piece_count=self._owner_piece_count,
            opponent_piece_count=self._opponent_piece_count,
            cycle_counter=self._cycle_counter,
            grid_size=self._grid_size,
            squadron_size=self._squadron_size
        )


class VoidScoreRequest(RequestMessage):
    prefix = ['<SERVER>', '<VOID>']
    argc = [2]

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return __class__(args)


################################################################################
# RESPONSES
################################################################################

class ResponseMessage(Message, metaclass=ABCMeta):
    def __init__(self, args: List[str]) -> None:
        super().__init__(args)


class CrossDomainPolicyAllowAllResponse(ResponseMessage):
    prefix = ['<cross-domain-policy><allow-access-from domain="*" to-ports="*" /></cross-domain-policy>']
    argc = [1]

    def __init__(self) -> None:
        super().__init__(['<cross-domain-policy><allow-access-from domain="*" to-ports="*" /></cross-domain-policy>'])


class PlayerCountResponse(ResponseMessage):
    prefix = ['<S>', '<SERVER>', '<PLAYERS_COUNT>']
    argc = [4]

    def __init__(self, player_count: int) -> None:
        super().__init__(['<S>', '<SERVER>', '<PLAYERS_COUNT>', str(player_count)])


class BroadcastCommentResponse(ResponseMessage):
    prefix = ['<B>', '<COMMENT>']
    argc = [4]

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)

    @classmethod
    def from_args(cls, args: List[str]):
        return cls(args)

    @classmethod
    def new(cls, who: int, comment: str):
        return cls([*cls.prefix, str(who), comment])


class OldSwfResponse(ResponseMessage):
    prefix = ['<S>', '<SERVER>', '<OLD_SWF>']
    argc = [3]

    def __init__(self) -> None:
        super().__init__(['<S>', '<SERVER>', '<OLD_SWF>'])


class NameTakenResponse(ResponseMessage):
    prefix = ['<S>', '<SERVER>', '<NAME_TAKEN>']
    argc = [4]

    def __init__(self, taken: bool) -> None:
        super().__init__(['<S>', '<SERVER>', '<NAME_TAKEN>', '<YES>' if taken else '<NO>'])


class ServerAliveResponse(ResponseMessage):
    prefix = ['<S>', '<SERVER>', '<ALIVE>']
    argc = [3]

    def __init__(self) -> None:
        super().__init__(['<S>', '<SERVER>', '<ALIVE>'])


class GameServerAliveResponse(ResponseMessage):
    prefix = ['<SERVER>', '<ALIVE>']
    argc = [2]

    def __init__(self) -> None:
        super().__init__(['<SERVER>', '<ALIVE>'])


class LobbyDuplicateResponse(ResponseMessage):
    prefix = ['<L>', '<DUPLICATE>']
    argc = [2]

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return __class__(args)

    @classmethod
    def new(cls):
        return cls(cls.prefix)


class LobbyBadMemberResponse(ResponseMessage):
    prefix = ['<L>', '<BAD_MEMBER>']
    argc = [2]

    def __init__(self) -> None:
        super().__init__(['<L>', '<BAD_MEMBER>'])


class LastLoggedResponse(ResponseMessage):
    prefix = ['<S>', '<SERVER>', '<LAST_LOGGED>']
    argc = [6]

    def __init__(self, player: str, time: datetime, motd: str) -> None:
        super().__init__([
            '<S>', '<SERVER>', '<LAST_LOGGED>', player,
            str(self.__last_logged_minutes(time)),
            motd])

    def __last_logged_minutes(self, time: datetime):
        diff = datetime.now() - time
        return int(diff.total_seconds()) // 60


class LastPlayedResponse(ResponseMessage):
    prefix = ['<S>', '<SERVER>', '<LAST_PLAYED>']
    argc = [18]

    def __init__(self, recent_games: List[GameResultHistory]) -> None:
        super().__init__([
            '<S>', '<SERVER>', '<LAST_PLAYED>',
            *reversed(self.__serialize_entries(recent_games))])

    def __serialize_entries(self, recent_games: List[GameResultHistory]):
        if recent_games is None or len(recent_games) == 0:
            return ['No recent battles# # '] + [self.__serialize_entry(None)] * 14

        to_serialize: List[Optional[GameResultHistory]] = recent_games[0:15]
        while len(to_serialize) < 15:
            to_serialize.append(None)
        return [self.__serialize_entry(e) for e in to_serialize]

    def __serialize_entry(self, entry: Optional[GameResultHistory]):
        if entry is None:
            return ' # # '

        duration_sec = (entry.finish - entry.start).total_seconds()
        minutes, seconds = divmod(duration_sec, 60)
        data = [
            f'{entry.player_won} beat {entry.player_lost}',
            f'{entry.won_score}-{entry.lost_score}',
            f'{minutes:.0f}:{seconds:02.0f}',
        ]
        return '#'.join(data)


class ServerRankingThisMonthResponse(ResponseMessage):
    prefix = ['<S>', '<SERVER>', '<RANKING(thisMonth)>']
    argc = [-1]

    def __init__(self, ranking: List[RankingEntry]) -> None:
        super().__init__([
            '<S>', '<SERVER>', '<RANKING(thisMonth)>',
            *self.__serialize_entries(ranking)])

    def __serialize_entries(self, entries: List[RankingEntry]):
        to_serialize: List[Optional[RankingEntry]] = entries[0:100]
        return [x for e in to_serialize for x in self.__serialize_entry(e)]

    def __serialize_entry(self, entry: RankingEntry):
        return [
            entry.player,
            str(entry.wins),
            str(entry.games),
        ]


class LobbyStateResponse(ResponseMessage):
    prefix = ['<L>']
    argc = [170]

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return __class__(args)

    @classmethod
    def new(cls, players: List[LobbyPlayer]):
        return __class__(['<L>', *cls.__serialize_players(players)])

    @classmethod
    def __serialize_players(cls, players: List[LobbyPlayer]):
        to_serialize: List[Optional[LobbyPlayer]] = players[0:13]
        while len(to_serialize) < 13:
            to_serialize.append(None)
        return [x for e in to_serialize for x in cls.__serialize_player(e)]

    @classmethod
    def __serialize_player(cls, player: LobbyPlayer):
        if player is None:
            player = LobbyPlayer()
            player.username = '<EMPTY>'
        return [
            player.username,
            player.comment,
            str(player.score),
            *map(str, player.awards),
        ]


class OpponentDeadResponse(ResponseMessage):
    prefix = ['<S>', '<SERVER>', '<OPPDEAD>']
    argc = [3]

    def __init__(self) -> None:
        super().__init__(['<S>', '<SERVER>', '<OPPDEAD>'])


class VoidScoreResponse(ResponseMessage):
    prefix = ['<S>', '<SERVER>', '<VOID>']
    argc = [3]

    def __init__(self) -> None:
        super().__init__(['<S>', '<SERVER>', '<VOID>'])


################################################################################
# GENERIC MESSAGES
################################################################################

class UsePowerMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<USE_POWER>']
    argc = [4, 5]

    def __init__(self, power_name: str, piece: int, arg: Optional[str] = None) -> None:
        args = [*self.prefix, power_name, str(piece)] + ([arg] if arg is not None else [])
        super().__init__(args)

        if not powers.is_valid(power_name):
            raise ValueError('Invalid power: {power_name}')

    def get_power_name(self):
        return self.args[2]

    def get_piece(self):
        return int(self.args[3])

    def get_power_arg(self):
        try:
            return self.args[4]
        except IndexError:
            return None

    @staticmethod
    def from_args(args: List[str]):
        return UsePowerMessage(args[2], int(args[3]), args[4] if len(args) > 4 else None)


class GameChatMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<CHAT>']
    argc = [3]

    def __init__(self, text: str) -> None:
        args = [*self.prefix, text]
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return GameChatMessage(args[2])

    def get_text(self):
        return self.args[2]


class LobbyChatMessage(RequestMessage, ResponseMessage):
    prefix = ['<B>', '<CHAT>']
    argc = [4]

    def __init__(self, idx: int, text: str) -> None:
        args = [*self.prefix, str(idx), text]
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return LobbyChatMessage(int(args[2]), args[3])

    def get_idx(self):
        return int(self.args[2])

    def get_text(self):
        return self.args[3]


class GrabPieceMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<GRAB_PIECE>']
    argc = [3]

    def __init__(self, piece: int) -> None:
        args = [*self.prefix, str(piece)]
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return GrabPieceMessage(int(args[2]))

    def get_piece(self):
        return int(self.args[2])


class ReleasePieceMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<RELEASE_PIECE>']
    argc = [3]

    def __init__(self, piece: int) -> None:
        args = [*self.prefix, str(piece)]
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return ReleasePieceMessage(int(args[2]))

    def get_piece(self):
        return int(self.args[2])


class SwitchPlayerMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<SWITCH_PLAYER>']
    argc = [3]

    def __init__(self, piece: int) -> None:
        args = [*self.prefix, str(piece)]
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return SwitchPlayerMessage(int(args[2]))

    def get_piece(self):
        return int(self.args[2])


class RecursiveDoneMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<RECURSIVE_DONE>']
    argc = [3]

    def __init__(self, piece: int) -> None:
        args = [*self.prefix, str(piece)]
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return RecursiveDoneMessage(int(args[2]))

    def get_piece(self):
        return int(self.args[2])


class SwitcherooMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<SWITCHEROO>']
    argc = [6]

    def __init__(self, args) -> None:
        super().__init__(args)

    @classmethod
    def from_args(cls, args: List[str]):
        return cls(args)

    @classmethod
    def new(cls, piece: int, old_column: int, old_row: int, occupier: int):
        return cls([*cls.prefix, str(piece), str(old_column), str(old_row), str(occupier)])


class RemoveOneWayWallMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<REMOVE_ONEWAY_WALL>']
    argc = [4]

    def __init__(self, args) -> None:
        super().__init__(args)

    @classmethod
    def from_args(cls, args: List[str]):
        return cls(args)

    @classmethod
    def new(cls, wall: int, piece: int):
        return cls([*cls.prefix, str(wall), str(piece)])


class BankruptActionMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<BR_ANIMATION>']
    argc = [3]

    def __init__(self, args) -> None:
        super().__init__(args)

    @classmethod
    def from_args(cls, args: List[str]):
        return cls(args)

    @classmethod
    def new(cls, player_index: int):
        return cls([*cls.prefix, str(player_index)])


class RemovePlayerMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<REMOVE_PLAYER>']
    argc = [3]

    def __init__(self, piece: int) -> None:
        args = [*self.prefix, str(piece)]
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return RemovePlayerMessage(int(args[2]))

    def get_piece(self):
        return int(self.args[2])


class PowerNoEffectMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<NO_EFFECT_OPP>']
    argc = [3]

    def __init__(self, power_id: int) -> None:
        args = [*self.prefix, str(power_id)]
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return PowerNoEffectMessage(int(args[2]))

    def get_power_id(self):
        return int(self.args[2])


class NukeMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<NUKE>']
    argc = [2]

    def __init__(self) -> None:
        args = [*self.prefix]
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return __class__()


class JumpOnPieceMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<JUMP_ON_PIECE_ANIMATION>']
    argc = [4]

    def __init__(self, piece: int, target_piece: int) -> None:
        args = [*self.prefix, str(piece), str(target_piece)]
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return JumpOnPieceMessage(int(args[2]), int(args[3]))

    def get_piece(self):
        return int(self.args[2])

    def get_target_piece(self):
        return int(self.args[3])


class GetPowerSquareMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<GET_POWER_SQUARE>']
    argc = [4]

    def __init__(self, square_piece: int, player_piece: int) -> None:
        args = [*self.prefix, str(square_piece), str(player_piece)]
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return GetPowerSquareMessage(int(args[2]), int(args[3]))

    def get_square_piece(self):
        return int(self.args[2])

    def get_player_piece(self):
        return int(self.args[3])


class SettingsLoadedMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<SETTINGS>', '<LOADED>']
    argc = [4]

    def __init__(self, version: int) -> None:
        args = [*self.prefix, str(version)]
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return SettingsLoadedMessage(int(args[3]))

    def get_version(self):
        return int(self.args[3])


class AssignPowerSquareMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<ASSIGN_POWER_SQUARE>']
    argc = [4]

    def __init__(self, power_id: int, piece: int) -> None:
        args = [*self.prefix, str(power_id), str(piece)]
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return AssignPowerSquareMessage(int(args[2]), int(args[3]))

    def get_power_id(self):
        return int(self.args[2])

    def get_piece(self):
        return int(self.args[3])


class AssignNextPowerCountMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<ASSIGN_NEXT_POWER_COUNT>']
    argc = [3]

    def __init__(self, count: int) -> None:
        args = [*self.prefix, str(count)]
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return AssignNextPowerCountMessage(int(args[2]))

    def get_count(self):
        return int(self.args[2])


class NewGridCoordMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<NEW_GRID_CORD>']
    argc = [6]

    def __init__(self, piece: int, column: int, row: int, step: int) -> None:
        args = [*self.prefix, str(piece), str(column), str(row), str(step)]
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return NewGridCoordMessage(int(args[2]), int(args[3]), int(args[4]), int(args[5]))

    def get_piece(self):
        return int(self.args[2])

    def get_column(self):
        return int(self.args[3])

    def get_row(self):
        return int(self.args[4])

    def get_step(self):
        return int(self.args[5])


class ResignMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<SETTINGS>', '<RESIGN>']
    argc = [3]

    def __init__(self) -> None:
        args = [*self.prefix]
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return __class__()


class ChallengeMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', None, None, '<SHALLWEPLAYAGAME?>']
    argc = [4]

    def __init__(self, challenged_idx: int, challenger_idx: int) -> None:
        args = [self.prefix[0], str(challenged_idx), str(challenger_idx), self.prefix[3]]
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return ChallengeMessage(int(args[1]), int(args[2]))

    def get_challenged_idx(self):
        return int(self.args[1])

    def get_challenger_idx(self):
        return int(self.args[2])


class ChallengeAuthMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', None, None, '<AUTHENTICATION>']
    argc = [5]

    def __init__(self, challenged_idx: int, challenger_idx: int, auth: str) -> None:
        args = [self.prefix[0], str(challenged_idx), str(challenger_idx), self.prefix[3], auth]
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return ChallengeAuthMessage(int(args[1]), int(args[2]), args[4])

    def get_challenged_idx(self):
        return int(self.args[1])

    def get_challenger_idx(self):
        return int(self.args[2])

    def get_auth(self):
        return self.args[4]


class SettingsReadyOffMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<SETTINGS>', '<READY_OFF>']
    argc = [3]

    def __init__(self) -> None:
        args = [*self.prefix]
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return SettingsReadyOffMessage()


class SettingsArenaSizeMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<SETTINGS>', '<ARENA_SIZE>']
    argc = [4]

    valid_sizes = ['small', 'medium', '9x9', 'large', 'extraLarge']

    def __init__(self, size: str) -> None:
        args = [*self.prefix, size]
        super().__init__(args)

        if size not in self.valid_sizes:
            raise ValueError(f'Invalid size: {size}')

    @staticmethod
    def from_args(args: List[str]):
        return SettingsArenaSizeMessage(args[3])

    def get_size(self):
        return self.args[3]


class SettingsSquadronSizeMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<SETTINGS>', '<SQUADRON_SIZE>']
    argc = [4]

    valid_sizes = ['small', 'medium', 'large', 'extraLarge']

    def __init__(self, size: str) -> None:
        args = [*self.prefix, size]
        super().__init__(args)

        if size not in self.valid_sizes:
            raise ValueError(f'Invalid size: {size}')

    @staticmethod
    def from_args(args: List[str]):
        return SettingsSquadronSizeMessage(args[3])

    def get_size(self):
        return self.args[3]


class SettingsTimerMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<SETTINGS>', '<TIMER>']
    argc = [4]

    valid_times = [240000, 120000, 60000, 30000, 15000, 500000000]

    def __init__(self, time: int) -> None:
        args = [*self.prefix, str(time)]
        super().__init__(args)

        if time not in self.valid_times:
            raise ValueError(f'Invalid time: {time}')

    @staticmethod
    def from_args(args: List[str]):
        return SettingsTimerMessage(int(args[3]))

    def get_time(self):
        return int(self.args[3])


class SettingsTopBottomMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<SETTINGS>', '<TOP_BOTTOM>']
    argc = [4]

    def __init__(self, is_top_bottom: bool) -> None:
        args = [*self.prefix, 'true' if is_top_bottom else 'false']
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return SettingsTopBottomMessage(args[3] == 'true')

    def is_top_bottom(self):
        return self.args[3] == 'true'


class SettingsColorMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<SETTINGS>', '<COLOR>']
    argc = [5]

    def __init__(self, decoration_color: int, text_color: str) -> None:
        args = [*self.prefix, str(decoration_color), text_color]
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return SettingsColorMessage(int(args[3]), args[4])

    def get_decoration_color(self):
        return int(self.args[3])

    def get_text_color(self):
        return self.args[4]


class SettingsReadyOnMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<SETTINGS>', '<READY_ON>']
    argc = [7]

    def __init__(self, grid_size: int, player_size: int, decoration_color: int, text_color: str) -> None:
        args = [*self.prefix, str(grid_size), str(player_size), str(decoration_color), text_color]
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return SettingsReadyOnMessage(int(args[3]), int(args[4]), int(args[5]), args[6])

    def get_grid_size(self):
        return int(self.args[3])

    def get_player_size(self):
        return int(self.args[4])

    def get_decoration_color(self):
        return int(self.args[5])

    def get_text_color(self):
        return self.args[6]


class SettingsReadyOnAgainMessage(RequestMessage, ResponseMessage):
    prefix = ['<S>', '<SETTINGS>', '<READY_ON>']
    argc = [3]

    def __init__(self) -> None:
        args = [*self.prefix]
        super().__init__(args)

    @staticmethod
    def from_args(args: List[str]):
        return SettingsReadyOnAgainMessage()


################################################################################
# UTILS
################################################################################

__message_classes = [
    DisconnectRequest,
    PolicyFileRequest,
    HelloLobbyRequest,
    JoinLobbyRequest,
    HelloGameRequest,
    JoinGameRequest,
    SetCommentRequest,
    GameChatMessage,
    LobbyChatMessage,
    UsePowerMessage,
    ServerRecentRequest,
    ServerRankingRequest,
    ServerAliveRequest,
    ServerPingRequest,
    CrossDomainPolicyAllowAllResponse,
    PlayerCountResponse,
    BroadcastCommentResponse,
    OldSwfResponse,
    NameTakenResponse,
    ServerAliveResponse,
    GameServerAliveResponse,
    LobbyDuplicateResponse,
    LobbyBadMemberResponse,
    LastLoggedResponse,
    LastPlayedResponse,
    ServerRankingThisMonthResponse,
    LobbyStateResponse,
    OpponentDeadResponse,
    VoidScoreResponse,
    GrabPieceMessage,
    ReleasePieceMessage,
    SwitchPlayerMessage,
    RecursiveDoneMessage,
    RemovePlayerMessage,
    PowerNoEffectMessage,
    NukeMessage,
    ResignMessage,
    JumpOnPieceMessage,
    GetPowerSquareMessage,
    SettingsLoadedMessage,
    AssignPowerSquareMessage,
    AssignNextPowerCountMessage,
    NewGridCoordMessage,
    ChallengeMessage,
    ChallengeAuthMessage,
    SettingsReadyOffMessage,
    SettingsArenaSizeMessage,
    SettingsSquadronSizeMessage,
    SettingsTimerMessage,
    SettingsTopBottomMessage,
    SettingsColorMessage,
    SettingsReadyOnMessage,
    SettingsReadyOnAgainMessage,
    VoidScoreRequest,
    AddStatsRequest,
]


def _parse_data(data: str) -> Optional[Message]:
    args = data.split(delim)

    for clazz in __message_classes:
        if _valid(args, clazz.prefix, clazz.argc):
            try:
                return clazz.from_args(args)
            except ValueError:
                return None

    return None


def _valid(args: List[str], prefix: List[str], argc: List[int]):
    if len(args) not in argc and -1 not in argc:
        return False

    for p, a in zip(prefix, args):
        if p is not None and p != a:
            return False

    return True
