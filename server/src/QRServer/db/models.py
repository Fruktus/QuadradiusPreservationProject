from datetime import datetime
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

    @property
    def is_guest(self):
        return self.username.lower().endswith(' guest')


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
