import abc
from datetime import datetime
from dataclasses import dataclass, field
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

    def __repr__(self):
        args = '"' + '","'.join(self.id) + '"'
        return f'Match({args})'

    def __str__(self):
        return self.__repr__()


class MatchParty(abc.ABC):
    @abc.abstractmethod
    def match_opponent(self, opponent: 'MatchParty'):
        pass

    @abc.abstractmethod
    def unmatch_opponent(self):
        pass

    @property
    @abc.abstractmethod
    def is_void_score(self):
        pass

    @property
    @abc.abstractmethod
    def is_guest(self):
        pass

    @property
    @abc.abstractmethod
    def username(self) -> str | None:
        pass

    @property
    @abc.abstractmethod
    def user_id(self) -> str:
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
    ranked: bool
    users_voted_void: set[str]
    user_ids: set[str]
    parties: list[MatchParty]
    match_stats: dict[str, MatchStats]

    def __init__(self, _id: MatchId) -> None:
        super().__init__()
        self.id = _id
        # Assume it's ranked unless a guest joins
        self.ranked = True
        self.users_voted_void = set()
        self.parties = []
        self.match_stats = {}
        self.user_ids = set()
        self.start_time = datetime.now()

    def empty(self):
        return len(self.parties) == 0

    def full(self):
        return len(self.parties) == 2

    def add_party(self, party: MatchParty):
        if len(self.parties) >= 2:
            parties_str = list(map(lambda p: p.username, self.parties))
            raise Exception(
                f'Too many parties for a match. '
                f'Player {party.username} tried do join, '
                f'but there are already 2 players: {parties_str}')
        self.parties.append(party)
        self.user_ids.add(party.user_id)

        if party.is_guest:
            self.ranked = False

        if len(self.parties) == 2:
            party.match_opponent(self.parties[0])
            self.parties[0].match_opponent(party)

    def remove_party(self, party: MatchParty):
        if party not in self.parties:
            raise Exception('Cannot find the given party')

        if party.is_void_score:
            self.users_voted_void.add(party.user_id)

        self.parties.remove(party)
        if len(self.parties) > 0:
            self.parties[0].unmatch_opponent()
        party.unmatch_opponent()

    def add_match_stats(self, user_id: str, match_stats: MatchStats):
        self.match_stats[user_id] = match_stats

    def generate_match_report(self) -> DbMatchReport | None:
        if len(self.match_stats) < 1:
            return None

        if len(self.match_stats) == 1:
            winner_id, = self.match_stats.keys()
            winner_stats = self.match_stats[winner_id]
            loser_id = self.user_ids.difference({winner_id}).pop()
            loser_stats = None
        else:
            p1_id, p2_id = self.match_stats.keys()
            stat1 = self.match_stats[p1_id]
            stat2 = self.match_stats[p2_id]

            winner_id, winner_stats, loser_id, loser_stats = (p1_id, stat1, p2_id, stat2) if \
                stat1.own_piece_count > stat2.own_piece_count else (p2_id, stat2, p1_id, stat2)

        # Winner reports his pieces normally and opponent's as 0 when giving up
        # Loser seems to report both correctly (his own +-1, may not have last move)
        return DbMatchReport(
            winner_id=winner_id,
            loser_id=loser_id,
            winner_pieces_left=winner_stats.own_piece_count,
            loser_pieces_left=winner_stats.opponent_piece_count,
            move_counter=max(winner_stats.cycle_counter, loser_stats.cycle_counter if loser_stats else 0),
            grid_size=winner_stats.grid_size,
            squadron_size=winner_stats.squadron_size,
            started_at=self.start_time,
            finished_at=datetime.now(),
            is_ranked=self.ranked,
            is_void=self.is_void()
        )

    def is_void(self):
        for party in self.parties:
            if party.is_void_score:
                self.users_voted_void.add(party.user_id)

        return len(self.users_voted_void) == 2


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
    username: str
    user_id: str
    wins: int
    games: int
    rating: int = -1


@dataclass
class LobbyPlayer:
    user_id: str | None = None
    is_guest: bool = True
    username: str = ''
    comment: str = ''
    score: int = 0
    awards: list[int] = field(default_factory=lambda: [0] * 10)
    idx: int | None = None
    joined_at: datetime | None = None
