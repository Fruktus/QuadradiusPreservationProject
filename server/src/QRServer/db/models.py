from typing import List
from datetime import datetime
from dataclasses import dataclass, field
import uuid
import logging

log = logging.getLogger('db_models')


@dataclass
class DbUser:
    user_id: str
    username: str
    password: str
    created_at: str

    @property
    def is_guest(self):
        return 'GUEST' in self.username and self.password is None

    @staticmethod
    def from_row(row: List) -> "DbUser":
        try:
            return DbUser(
                user_id=row[0],
                username=row[1],
                password=row[2],
                created_at=row[3]
            )
        except Exception:
            log.warning(f'Failed to parse DbUser from row: {row}')
            return None


@dataclass
class DbMatch:
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

    @staticmethod
    def from_row(row: List) -> "DbMatch":
        try:
            return DbMatch(
                match_id=row[0],
                winner_id=row[1],
                loser_id=row[2],
                winner_pieces_left=row[3],
                loser_pieces_left=row[4],
                move_counter=row[5],
                grid_size=row[6],
                squadron_size=row[7],
                started_at=datetime.fromtimestamp(row[8]),
                finished_at=datetime.fromtimestamp(row[9]),
                is_ranked=row[10],
                is_void=row[11]
            )
        except Exception:
            log.warning(f'Failed to parse DbMatch from row: {row}')
            return None
