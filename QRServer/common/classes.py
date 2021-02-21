import abc
from datetime import datetime
from dataclasses import dataclass, field
from typing import List


class MatchId:
    id: frozenset

    def __init__(self, username_a, username_b) -> None:
        self.id = frozenset({username_a, username_b})

    def __eq__(self, o) -> bool:
        if not isinstance(o, MatchId):
            return False
        return self.id.__eq__(o.id)

    def __hash__(self) -> int:
        return self.id.__hash__()


class MatchParty(abc.ABC):
    @abc.abstractmethod
    def match_opponent(self, opponent: 'MatchParty'):
        pass

    @abc.abstractmethod
    def unmatch_opponent(self):
        pass


class Match:
    id: MatchId
    parties: List[MatchParty]

    def __init__(self, _id: MatchId) -> None:
        super().__init__()
        self.id = _id
        self.parties = []

    def empty(self):
        return len(self.parties) == 0

    def full(self):
        return len(self.parties) == 2

    def add_party(self, party: MatchParty):
        if len(self.parties) >= 2:
            raise Exception('Too many parties for a match')
        self.parties.append(party)

        if len(self.parties) == 2:
            party.match_opponent(self.parties[0])
            self.parties[0].match_opponent(party)

    def remove_party(self, party: MatchParty):
        if party not in self.parties:
            raise Exception('Cannot find the given party')

        self.parties.remove(party)
        if len(self.parties) > 0:
            self.parties[0].unmatch_opponent()
        party.unmatch_opponent()


@dataclass
class GameResultHistory:
    player_won: str
    player_lost: str
    won_score: int
    lost_score: int
    start: datetime
    finish: datetime


@dataclass
class RankingEntry:
    player: str
    wins: int
    games: int


@dataclass
class LobbyPlayer:
    user_id: str = None
    username: str = ''
    comment: str = ''
    score: int = 0
    awards: List[int] = field(default_factory=lambda: [0] * 10)
    idx: int = None
    joined_at: datetime = None
