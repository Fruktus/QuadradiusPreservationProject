from collections.abc import Iterable
from dataclasses import dataclass

from QRServer.achievements.conditions.constants import GridSize, SquadronSize
from QRServer.db.models import DbMatchReport


@dataclass(frozen=True)
class ReportCondition:
    """Every field that is set is a condition that must be met (AND operator between them).
    If list is passed for grid/squadron, they are all treated as allowed values.
    Unset means not applicable (skipped).
    Evaluated from the given user's point of view (so winner/loser is correctly handled)."""

    won: bool | None = None  # True: won, False: lost
    grid: GridSize | Iterable[GridSize] | None = None
    squadron: SquadronSize | Iterable[SquadronSize] | None = None
    min_moves: int | None = None
    max_moves: int | None = None
    min_pieces: int | None = None  # the user's own pieces left
    max_pieces: int | None = None
    min_seconds: int | None = None  # match duration (finished_at - started_at)
    max_seconds: int | None = None

    @staticmethod
    def _matches(value: str, target: str | Iterable[str]) -> bool:
        """Check a report's value against a condition that may be a single
        target value or a collection of acceptable values.
        Value must match target exactly or be present inside the collection.
        """
        if isinstance(target, str):
            return value == target
        return value in target

    def met(self, report: DbMatchReport, user_id: str) -> bool:
        won = report.winner_id == user_id
        pieces = report.winner_pieces_left if won else report.loser_pieces_left
        seconds = (report.finished_at - report.started_at).total_seconds()
        return (
            (self.won is None or self.won == won)
            and (self.grid is None or self._matches(report.grid_size, self.grid))
            and (self.squadron is None or self._matches(report.squadron_size, self.squadron))
            and (self.min_moves is None or report.move_counter >= self.min_moves)
            and (self.max_moves is None or report.move_counter <= self.max_moves)
            and (self.min_pieces is None or pieces >= self.min_pieces)
            and (self.max_pieces is None or pieces <= self.max_pieces)
            and (self.min_seconds is None or seconds >= self.min_seconds)
            and (self.max_seconds is None or seconds <= self.max_seconds)
        )
