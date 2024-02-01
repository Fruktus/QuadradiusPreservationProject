import abc
from datetime import datetime
from dataclasses import dataclass, field
from typing import List
from QRServer.db.models import DbMatchReport


class MatchId:
    id: frozenset

    def __init__(self, user_a_id, user_b_id) -> None:
        self.id = frozenset({user_a_id, user_b_id})

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
class MatchStats:
    own_piece_count: int
    opponent_piece_count: int
    cycle_counter: int
    grid_size: str = ''
    squadron_size: str = ''


class Match:
    id: MatchId
    parties: List[MatchParty]
    match_stats: {}

    def __init__(self, _id: MatchId) -> None:
        super().__init__()
        self.id = _id
        self.parties = []
        self.match_stats = {}
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

    def add_match_stats(self, client_id: str, match_stats: MatchStats):
        self.match_stats[client_id] = match_stats

    def generate_match_report(self) -> DbMatchReport:
        if len(self.match_stats) != 2:
            return None

        p1_id = list(self.match_stats.keys())[0]
        p2_id = list(self.match_stats.keys())[1]
        stat1 = self.match_stats[p1_id]
        stat2 = self.match_stats[p2_id]
        winner_id, winner, loser_id, loser = (p1_id, stat1, p2_id, stat2) if \
            stat1.own_piece_count > stat2.own_piece_count else (p2_id, stat2, p1_id, stat2)

        # Winner reports his pieces normally and opponent's as 0 when giving up
        # Loser seems to report both correctly (his own +-1, may not have got last move)
        return DbMatchReport(
            winner_id=winner_id,
            loser_id=loser_id,
            winner_pieces_left=winner.own_piece_count,
            loser_pieces_left=winner.opponent_piece_count,
            move_counter=max(winner.cycle_counter, loser.cycle_counter),
            grid_size=winner.grid_size,
            squadron_size=winner.squadron_size,
            started_at=self.start_time,
            finished_at=datetime.now(),
            is_ranked=self.is_ranked(),
            is_void=self.is_void()
        )

    def is_void(self):
        return all(party.void_score for party in self.parties)

    def is_ranked(self):
        return all(not party.is_guest for party in self.parties)


@dataclass
class GameResultHistory:
    player_won: str
    player_lost: str
    won_score: int
    lost_score: int
    start: datetime
    finish: datetime
    moves: int

    def time_str(self):
        duration_sec = (self.finish - self.start).total_seconds()
        minutes, seconds = divmod(duration_sec, 60)
        return f'{minutes:.0f}:{seconds:02.0f}'


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
