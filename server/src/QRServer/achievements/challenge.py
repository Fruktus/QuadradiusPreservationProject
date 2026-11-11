import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from QRServer.db.models import DbMatchReport, DbRecordedMessage


@dataclass
class Outcome:
    progress: Any = None
    completed: bool = False


class Challenge:
    """Used to define a Challenge that can be completed by the user.
    Has to have unique key, since this is how it's distinguished from others.
    Instances are used for all dispatches, so they should not hold state.
    If expiration is set, it will not be processed after that time, otherwise it will
    always run if not already completed."""
    key: str
    reward_key: str
    expires_at: datetime | None = None

    def applies(self, report: DbMatchReport, recording: list[DbRecordedMessage]) -> bool:
        """Cheap prefilter ran without DB access.
        Runs before the progress read.
        Use for easy to check stuff, like whether the today's date matches conditions."""
        return True

    def initial_progress(self) -> str:
        """Encoded progress used when the user has no progress in db yet (it goes through
        decode_progress before run()). Since the progress can be interpreted individually
        by each challenge, they also need to provide its default state (for example empty json)"""
        return self.encode_progress(None)

    def encode_progress(self, progress: Any) -> str:
        """This function encodes the progress for db - serializes into string"""
        return json.dumps(progress)

    def decode_progress(self, raw: str) -> Any:
        """This function decodes the progress from db - deserializes from string"""
        return json.loads(raw)

    def pretty_print_progress(self, progress: Any) -> str:
        """Format progress for human-friendly display, can be customized to include units etc."""
        return f'Progress: {progress}'

    def run(self, user_id: str, progress: Any, report: DbMatchReport,
            recording: list[DbRecordedMessage]) -> Outcome | None:
        """Runs the actual checks for challenges - override the implementation.
        If db is not required to check preconditions, fill out the `applies` as well.
        For multistage challenges the manager injects the previous (or initial) progress.

        Returns Outcome if anything changed (completed or update needed - manager
        knows what to update via challenge key) or None if no change is required.
        """
        raise NotImplementedError
