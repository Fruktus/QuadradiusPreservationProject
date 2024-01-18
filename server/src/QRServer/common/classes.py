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


@dataclass
class MatchStats:
    owner: str
    own_piece_count: int
    opponent_piece_count: int
    cycle_counter: int
    grid_size: str = ''
    squadron_size: str = ''


@dataclass
class MatchResult:
    player1_username: str
    player2_username: str
    player1_pieces_left: int
    player2_pieces_left: int
    move_counter: int
    grid_size: str
    squadron_size: str
    started_at: datetime
    finished_at: datetime
    is_ranked: bool
    is_void: bool


class MatchReporter:
    @staticmethod
    def build_report(match_results: List[MatchStats], is_ranked: bool, is_void: bool,
                     start_time: datetime, end_time: datetime):
        if len(match_results) != 2:
            return None
        stat1 = match_results[0]
        stat2 = match_results[1]
        report = {
            'player1_username': stat1.owner,
            'player2_username': stat2.owner,
            'player1_pieces_left': stat1.own_piece_count,
            'player2_pieces_left': stat2.own_piece_count,
            'move_counter': max(stat1.cycle_counter, stat2.cycle_counter),
            'grid_size': stat1.grid_size,
            'squadron_size': stat1.grid_size,
            'started_at': start_time.timestamp(),
            'finished_at': end_time.timestamp(),
            'is_ranked': is_ranked,
            'is_void': is_void 
        }
        return MatchResult(**report)

class Match:
    id: MatchId
    parties: List[MatchParty]
    results: List[MatchStats]

    def __init__(self, _id: MatchId) -> None:
        super().__init__()
        self.id = _id
        self.parties = []
        self.results = []
        self.start_time = datetime.now()

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

    def add_match_stats(self, result: MatchStats):
        self.results.append(result)
    
    def generate_result(self) -> MatchResult:
        return MatchReporter.build_report(
            match_results=self.results,
            is_ranked=self.is_ranked(),
            is_void=self.is_void(),
            start_time=self.start_time,
            end_time=datetime.now())

    def is_void(self):
        for party in self.parties:
            if not party.void_score:
                return False
        return True

    def is_ranked(self):
        for party in self.parties:
            if party.is_guest:
                return False
        return True
