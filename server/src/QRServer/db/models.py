from datetime import datetime, timezone
from dataclasses import dataclass, field
import uuid
import logging

log = logging.getLogger('qr.db_models')


@dataclass
class DbUser:
    user_id: str
    username: str
    password: str
    created_at: str
    discord_user_id: str
    banned_at: datetime | None
    ban_reason: str | None

    @property
    def is_guest(self):
        return self.username.lower().endswith(' guest')

    @property
    def is_banned(self):
        return bool(self.banned_at)


@dataclass
class DbMatchReport:
    winner_id: str
    loser_id: str
    winner_pieces_left: int
    loser_pieces_left: int
    move_counter: int
    grid_size: str
    squadron_size: str
    started_at: datetime
    finished_at: datetime
    is_ranked: bool
    is_void: bool
    match_id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class UserRating:
    user_id: str
    month: int
    year: int
    rating: int = field(default=500)
    revision: int = field(default=0)


@dataclass
class Tournament:
    tournament_id: str
    name: str
    created_by_dc_id: str
    tournament_msg_dc_id: str
    required_matches_per_duel: int
    created_at: datetime
    started_at: datetime | None
    finished_at: datetime | None


@dataclass
class TournamentParticipant:
    tournament_id: str
    user_id: str


@dataclass
class TournamentDuel:
    tournament_id: str
    duel_idx: int
    active_until: datetime
    user1_id: str
    user2_id: str


@dataclass
class TournamentMatch:
    duel_idx: int
    match: DbMatchReport


@dataclass
class MatchInvite:
    invite_id: str
    challenger_id: str
    challenged_id: str
    challenger_auth: int
    challenged_auth: int
    challenger_tmp_pass: str
    challenged_tmp_pass: str
    issued_at: datetime
    active_until: datetime
    is_used: bool
    used_at: datetime | None
    match_id: str | None

    @property
    def is_active(self):
        return not self.is_used and self.active_until > datetime.now(timezone.utc)
