import logging

from QRServer.achievements.challenge import Challenge
from QRServer.achievements.challenges import CHALLENGES
from QRServer.config import Config
from QRServer.db.connector import DbConnector
from QRServer.db.models import ChallengeProgress, DbMatchReport, DbRecordedMessage

log = logging.getLogger(__name__)


class AchievementsManager:
    config: Config
    connector: DbConnector
    challenges: list[Challenge]

    def __init__(self, config: Config, connector: DbConnector, challenges: list[Challenge] | None = None):
        self.config = config
        self.connector = connector
        # tests inject instances here
        self.challenges = challenges if challenges is not None else [c() for c in CHALLENGES]

        keys = [c.key for c in self.challenges]
        if len(keys) != len(set(keys)):
            # Hard fail if two challenges share the same key
            raise ValueError("duplicate challenge keys")

        if not config.get('recordings.enabled'):
            log.warning('recordings are disabled - some achievements may not work (at all)')

    @staticmethod
    def _applies(challenge: Challenge, report: DbMatchReport, recording: list[DbRecordedMessage]) -> bool:
        try:
            # challenge level expiry, the db filter only knows about already stored progress
            if challenge.expires_at is not None and report.finished_at > challenge.expires_at:
                return False

            return challenge.applies(report, recording)
        except Exception:
            log.exception("challenge %s: applies() failed", challenge.key)
            return False

    async def dispatch(self, report: DbMatchReport, recording: list[DbRecordedMessage]) -> None:
        try:
            if report.is_void or not report.is_ranked:
                return

            # List all defined challenges that apply to current report (run preconditions check)
            # Preconditions include stuff like minimal move count, specific board size etc.
            available_challenges = [c for c in self.challenges if self._applies(c, report, recording)]
            if not available_challenges:
                return

            keys = [c.key for c in available_challenges]
            # Check both users
            for user_id in (report.winner_id, report.loser_id):
                try:
                    # Fetch user's progress (or None if not started) for available challenges' keys
                    # Done and expired challenges are left out, a None value means no row (progress) yet
                    current_challenge_progresses = await self.connector.get_open_challenge_progress(user_id, keys)
                except Exception:
                    log.exception("reading challenge progress failed for user %s", user_id)
                    continue

                # Only check the challenges which currently apply (preconditions are met)
                for challenge in available_challenges:
                    if challenge.key in current_challenge_progresses:
                        await self._run_challenge(user_id, challenge,
                                                  current_challenge_progresses[challenge.key], report, recording)
        except Exception:
            log.exception("challenge dispatch failed")

    async def _run_challenge(self, user_id: str, challenge: Challenge, challenge_progress: ChallengeProgress | None,
                             report: DbMatchReport, recording: list[DbRecordedMessage]) -> None:
        # compute first, no write lock held
        try:
            progress = challenge_progress.progress if challenge_progress is not None else challenge.initial_progress()
            current_progress = challenge.decode_progress(progress)
            outcome = challenge.run(user_id, current_progress, report, recording)

            if outcome is None:
                # Nothing to update
                return

            # User made progress
            serialized_progress = challenge.encode_progress(outcome.progress)
        except Exception:
            log.exception("challenge %s: run failed for user %s", challenge.key, user_id)
            return

        # Save first: losing progress is worse than a delayed award
        try:
            await self.connector.save_challenge_progress(
                user_id,
                challenge.key,
                serialized_progress,
                completed_at=report.finished_at if outcome.completed else None,
                expires_at=challenge.expires_at,  # every save, it's a full overwrite (allows modifying end date)
            )
        except Exception:
            log.exception("challenge %s: save failed for user %s", challenge.key, user_id)
            return

        if not outcome.completed:
            return

        try:
            if not await self.connector.award_achievement(challenge.reward_key, user_id):
                log.warning("award %s for user %s was not granted (does the achievement exist?)",
                            challenge.reward_key, user_id)
        except Exception:
            # If we failed to award achievement for some reason but got this far,
            # we already know that user completed the challenge and will attempt
            # to reconcile during next restart
            log.exception("award %s failed for user %s", challenge.reward_key, user_id)

    async def run_reconciliation(self) -> None:
        for challenge in self.challenges:
            try:
                unrewarded_user_ids = await self.connector.get_unrewarded_challenge_user_ids(
                    challenge.key, challenge.reward_key)
                for user_id in unrewarded_user_ids:
                    try:
                        if not await self.connector.award_achievement(challenge.reward_key, user_id):
                            log.warning("reconcile: award %s to %s was not granted (does the achievement exist?)",
                                        challenge.reward_key, user_id)
                    except Exception:
                        log.exception("reconcile: award %s to %s failed", challenge.reward_key, user_id)
            except Exception:
                log.exception("reconcile: %s failed", challenge.key)
