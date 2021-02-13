from datetime import datetime
from typing import List, Optional

from QRServer.common import powers
from QRServer.common.classes import GameResultHistory, RankingEntry

delim = '~'


class Message:
    args: List[str]

    def __init__(self, args: List[str]) -> None:
        self.args = args

        for arg in args:
            if not isinstance(arg, str):
                raise ValueError('Wrong argument type: {}'.format(type(arg)))

    def to_data(self) -> bytes:
        return delim.join(self.args).encode('ascii') + b'\x00'

    def __str__(self) -> str:
        return self.__repr__()

    def __repr__(self) -> str:
        return '{}({})'.format(self.__class__.__name__, self.args.__repr__())


################################################################################
# REQUESTS
################################################################################


class RequestMessage(Message):
    prefix = None
    argc = None

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)

        prefix = self.__class__.prefix
        argc = self.__class__.argc

        if prefix is None or argc is None:
            raise AttributeError()

        if len(args) not in argc:
            raise ValueError("{} not in {}".format(len(args), argc))

        if len(prefix) > len(args):
            raise ValueError("{} > {}".format(len(prefix), len(args)))

        for i, j in zip(prefix, args):
            if i != j:
                raise ValueError("{} != {}".format(i, j))


class HelloLobbyRequest(RequestMessage):
    prefix = ['<QR_L>']
    argc = [1]

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)


class JoinLobbyRequest(RequestMessage):
    prefix = ['<L>']
    argc = [3]

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)

    def get_username(self):
        return self.args[1]

    def get_password(self):
        return self.args[2]


class HelloGameRequest(RequestMessage):
    prefix = ['<QR_G>']
    argc = [1]

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)


class JoinGameRequest(RequestMessage):
    prefix = ['<L>']
    argc = [6]

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)

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


class ChatRequest(RequestMessage):
    prefix = ['<S>', '<CHAT>']
    argc = [3]

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)

    def get_text(self):
        return self.args[2]


class UsePowerRequest(RequestMessage):
    prefix = ['<S>', '<USE_POWER>']
    argc = [4, 5]

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)

        if not powers.is_valid(self.get_power_name()):
            raise ValueError('Invalid power: {}'.format(self.get_power_name()))

    def get_power_name(self):
        return self.args[2]

    def get_player_piece(self):
        return self.args[3]

    def get_power_arg(self):
        try:
            return self.args[4]
        except IndexError:
            return None


class ServerRecentRequest(RequestMessage):
    prefix = ['<SERVER>', '<RECENT>']
    argc = [2]

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)


class ServerRankingRequest(RequestMessage):
    prefix = ['<SERVER>', '<RANKING>']
    argc = [4]

    def __init__(self, args: List[str]) -> None:
        super().__init__(args)

        self._year = int(self.args[2])
        self._month = int(self.args[3])

    def get_year(self) -> int:
        return self._year

    def get_month(self) -> int:
        return self._month


################################################################################
# RESPONSES
################################################################################

class ResponseMessage(Message):
    def __init__(self, args: List[str]) -> None:
        super().__init__(args)


class PlayerCountResponse(ResponseMessage):
    def __init__(self, player_count: int) -> None:
        super().__init__(['<S>', '<SERVER>', '<PLAYERS_COUNT>', str(player_count)])


class BroadcastCommentResponse(ResponseMessage):
    def __init__(self, who: str, comment: str) -> None:
        super().__init__(['<B>', '<COMMENT>', who, comment])


class OldSwfResponse(ResponseMessage):
    def __init__(self) -> None:
        super().__init__(['<S>', '<SERVER>', '<OLD_SWF>'])


class NameTakenResponse(ResponseMessage):
    def __init__(self, taken: bool) -> None:
        super().__init__(['<S>', '<SERVER>', '<NAME_TAKEN>', '<YES>' if taken else '<NO>'])


class ServerAliveResponse(ResponseMessage):
    def __init__(self) -> None:
        super().__init__(['<S>', '<SERVER>', '<ALIVE>'])


class LobbyDuplicateResponse(ResponseMessage):
    def __init__(self) -> None:
        super().__init__(['<L>', '<DUPLICATE>'])


class LobbyBadMemberResponse(ResponseMessage):
    def __init__(self) -> None:
        super().__init__(['<L>', '<BAD_MEMBER>'])


class LastLoggedResponse(ResponseMessage):
    def __init__(self, player: str, time: datetime, motd: str) -> None:
        super().__init__([
            '<S>', '<SERVER>', '<LAST_LOGGED>', player,
            str(self.__last_logged_minutes(time)),
            motd])

    def __last_logged_minutes(self, time: datetime):
        diff = datetime.now() - time
        return int(diff.total_seconds()) // 60


class LastPlayedResponse(ResponseMessage):
    def __init__(self, recent_games: List[GameResultHistory]) -> None:
        super().__init__([
            '<S>', '<SERVER>', '<LAST_PLAYED>',
            *self.__serialize_entries(recent_games)])

    def __serialize_entries(self, recent_games: List[GameResultHistory]):
        to_serialize: List[Optional[GameResultHistory]] = recent_games[0:15]
        while len(to_serialize) < 15:
            to_serialize.append(None)
        return [self.__serialize_entry(e) for e in to_serialize]

    def __serialize_entry(self, entry: GameResultHistory):
        if entry is None:
            return ' # # '

        duration_sec = (entry.finish - entry.start).total_seconds()
        minutes, seconds = divmod(duration_sec, 60)
        data = [
            '{} beat {}'.format(entry.player_won, entry.player_lost),
            '{}-{}'.format(entry.won_score, entry.lost_score),
            '{:.0f}:{:02.0f}'.format(minutes, seconds),
        ]
        return '#'.join(data)


class ServerRankingResponse(ResponseMessage):
    def __init__(self, this_month: bool, ranking: List[RankingEntry]) -> None:
        super().__init__([
            '<S>', '<SERVER>',
            '<RANKING(thisMonth)>' if this_month else '<RANKING>',
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


################################################################################
# UTILS
################################################################################

__message_classes = [
    HelloLobbyRequest,
    JoinLobbyRequest,
    HelloGameRequest,
    JoinGameRequest,
    ChatRequest,
    UsePowerRequest,
    ServerRecentRequest,
    ServerRankingRequest,
]


def _parse_data(data: str) -> Optional[Message]:
    args = data.split(delim)

    for clazz in __message_classes:
        if _valid(args, clazz.prefix, clazz.argc):
            try:
                return clazz(args)
            except ValueError:
                return None

    return None


def _valid(args: List[str], prefix: List[str], argc: List[int]):
    return len(args) in argc and args[0:len(prefix)] == prefix
