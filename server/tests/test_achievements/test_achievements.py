from collections import Counter
import unittest
from datetime import datetime, timezone
from unittest.mock import Mock, patch
import uuid

from QRServer.achievements.challenge import Challenge, Outcome
from QRServer.achievements.challenges import CHALLENGES
from QRServer.achievements.manager import AchievementsManager
from QRServer.config import Config
from QRServer.db.connector import DbConnector
from QRServer.db.models import DbMatchReport, DbRecordedMessage, UserAchievement

LOGGER = 'QRServer.achievements.manager'


class DemoChallenge(Challenge):
    """Configurable challenge for tests. By default it completes on the first run.
    `initial` is the raw (already encoded) progress, same as a real challenge would provide"""

    def __init__(self, key='demo', reward_key='demo_ach', *, run=None, applies=True, initial='null',
                 expires_at=None):
        self.key = key
        self.reward_key = reward_key
        self.expires_at = expires_at
        self.run_calls: list[tuple] = []
        self._run = run or (lambda user_id, progress, report, recording: Outcome(completed=True))
        self._applies = applies
        self._initial = initial

    def applies(self, report, recording):
        return self._applies(report, recording) if callable(self._applies) else self._applies

    def initial_progress(self):
        return self._initial

    def run(self, user_id, progress, report, recording):
        self.run_calls.append((progress, user_id))
        return self._run(user_id, progress, report, recording)


class CounterChallenge(DemoChallenge):
    """Multistage challenge, completes after `target` matches.
    Progress is a plain int, the manager decodes it from the db string before calling run()"""

    def __init__(self, target=2, **kwargs):
        super().__init__('counter', 'counter_ach', initial='0', **kwargs)
        self.target = target

    def run(self, user_id, progress, report, recording):
        # keep the call tracking from DemoChallenge
        self.run_calls.append((progress, user_id))

        new_progress = progress + 1
        is_completed = new_progress >= self.target
        return Outcome(new_progress, is_completed)


class AchievementsManagerTest(unittest.IsolatedAsyncioTestCase):
    FINISHED = datetime(2026, 12, 1, 12, 0, 0, tzinfo=timezone.utc)
    FAR_FUTURE = datetime(2100, 1, 1, tzinfo=timezone.utc)
    LONG_AGO = datetime(2020, 1, 1, tzinfo=timezone.utc)

    async def asyncSetUp(self):
        self.config = Config()
        self.conn = DbConnector(':memory:', self.config)
        await self.conn.connect()

        self.winner = await self.conn.create_member('winner', b'password', '11111111111')
        self.loser = await self.conn.create_member('loser', b'password', '22222222222')
        await self.create_achievements('demo_ach', 'counter_ach', 'other_ach')

    async def asyncTearDown(self):
        await self.conn.close()

    async def create_achievements(self, *keys: str):
        # challenges reward achievements, so those have to exist in the db
        created_at = int(datetime(2026, 11, 7, tzinfo=timezone.utc).timestamp())
        async with self.conn._transaction('w') as c:
            for key in keys:
                await c.execute(
                    "insert into achievements (key, name, description, created_at) values (?, ?, ?, ?)",
                    (key, key, 'Test achievement.', created_at))

    def report(self, **overrides) -> DbMatchReport:
        fields = dict(
            match_id=str(uuid.uuid4()),
            winner_id=self.winner,
            loser_id=self.loser,
            winner_pieces_left=10,
            loser_pieces_left=5,
            move_counter=20,
            grid_size='small',
            squadron_size='medium',
            started_at=datetime(2026, 12, 1, 11, 0, 0, tzinfo=timezone.utc),
            finished_at=self.FINISHED,
            is_ranked=True,
            is_void=False,
        )
        fields.update(overrides)
        return DbMatchReport(**fields)

    def manager(self, *challenges: Challenge) -> AchievementsManager:
        return AchievementsManager(self.config, self.conn, list(challenges))

    async def dispatch(self, mgr: AchievementsManager, *, recording=None, **report_overrides):
        await mgr.dispatch(self.report(**report_overrides), recording or [])

    async def awarded(self, user_id) -> list[str]:
        return [a.achievement_key for a in await self.conn.get_user_achievements(user_id)]

    # registry
    def test_challenge_keys_are_unique(self):
        keys = [challenge_class().key for challenge_class in CHALLENGES]

        duplicates = [key for key, count in Counter(keys).items() if count > 1]
        self.assertEqual(duplicates, [])

    def test_challenges_define_key_and_reward_key(self):
        for challenge_class in CHALLENGES:
            challenge = challenge_class()
            self.assertTrue(challenge.key, challenge_class.__name__)
            self.assertTrue(challenge.reward_key, challenge_class.__name__)

    # construction
    def test_duplicate_keys_are_rejected(self):
        with self.assertRaises(ValueError):
            self.manager(DemoChallenge('same', 'a'), DemoChallenge('same', 'b'))

    def test_defaults_to_registry(self):
        mgr = AchievementsManager(self.config, self.conn)

        self.assertEqual(len(mgr.challenges), len(CHALLENGES))
        self.assertTrue(all(isinstance(c, Challenge) for c in mgr.challenges))

    # dispatch
    async def test_binary_challenge_awards_both_players(self):
        mgr = self.manager(DemoChallenge(expires_at=self.FAR_FUTURE))

        await self.dispatch(mgr)

        for user_id in (self.winner, self.loser):
            prog = await self.conn.get_challenge_progress(user_id, 'demo')
            self.assertEqual(prog.completed_at, self.FINISHED)
            self.assertEqual(prog.expires_at, self.FAR_FUTURE)
            self.assertEqual(await self.awarded(user_id), ['demo_ach'])

    async def test_multistage_challenge_saves_progress_without_award(self):
        mgr = self.manager(CounterChallenge(target=2, expires_at=self.FAR_FUTURE))

        await self.dispatch(mgr)

        prog = await self.conn.get_challenge_progress(self.winner, 'counter')
        self.assertEqual(prog.progress, '1')
        self.assertIsNone(prog.completed_at)
        self.assertEqual(prog.expires_at, self.FAR_FUTURE)  # set on every save, not just the last
        self.assertEqual(await self.awarded(self.winner), [])

    async def test_multistage_challenge_awards_both_players_on_completion(self):
        mgr = self.manager(CounterChallenge(target=2))

        await self.dispatch(mgr)
        await self.dispatch(mgr)

        prog = await self.conn.get_challenge_progress(self.winner, 'counter')
        self.assertEqual(prog.progress, '2')
        self.assertEqual(prog.completed_at, self.FINISHED)
        self.assertEqual(await self.awarded(self.winner), ['counter_ach'])
        self.assertEqual(await self.awarded(self.loser), ['counter_ach'])

    async def test_done_challenges_are_not_run_again(self):
        done = CounterChallenge(target=1)  # done after a single match
        mgr = self.manager(done)

        await self.dispatch(mgr)
        await self.dispatch(mgr)

        self.assertEqual(len(done.run_calls), 2)  # once per player, first match only
        self.assertEqual(await self.awarded(self.winner), ['counter_ach'])
        self.assertEqual(await self.awarded(self.loser), ['counter_ach'])

    async def test_expired_challenges_are_not_run(self):
        expired = DemoChallenge()
        mgr = self.manager(expired)
        # the winner's progress is already past its expiry date
        await self.conn.save_challenge_progress(self.winner, 'demo', 'null', expires_at=self.LONG_AGO)

        await self.dispatch(mgr)
        self.assertEqual([user for _, user in expired.run_calls], [self.loser])

        await self.dispatch(mgr)
        self.assertEqual(len(expired.run_calls), 1)  # loser is complete, winner is still expired
        self.assertEqual(await self.awarded(self.winner), [])
        self.assertEqual(await self.awarded(self.loser), ['demo_ach'])

    async def test_challenge_past_its_expiry_is_not_run(self):
        challenge = DemoChallenge(expires_at=self.LONG_AGO)
        mgr = self.manager(challenge)

        await self.dispatch(mgr)

        self.assertEqual(challenge.run_calls, [])
        self.assertIsNone(await self.conn.get_challenge_progress(self.winner, 'demo'))

    async def test_void_matches_are_skipped(self):
        challenge = DemoChallenge()
        mgr = self.manager(challenge)

        await self.dispatch(mgr, is_void=True)

        self.assertEqual(challenge.run_calls, [])
        self.assertIsNone(await self.conn.get_challenge_progress(self.winner, 'demo'))

    async def test_unranked_matches_are_skipped(self):
        challenge = DemoChallenge()
        mgr = self.manager(challenge)

        await self.dispatch(mgr, is_ranked=False)

        self.assertEqual(challenge.run_calls, [])
        self.assertIsNone(await self.conn.get_challenge_progress(self.winner, 'demo'))

    async def test_inapplicable_challenge_saves_nothing(self):
        challenge = DemoChallenge(applies=False)
        mgr = self.manager(challenge)

        await self.dispatch(mgr)

        self.assertEqual(challenge.run_calls, [])
        self.assertIsNone(await self.conn.get_challenge_progress(self.winner, 'demo'))

    async def test_challenge_without_outcome_saves_nothing(self):
        challenge = DemoChallenge(run=Mock(return_value=None))
        mgr = self.manager(challenge)

        await self.dispatch(mgr)

        self.assertEqual(len(challenge.run_calls), 2)
        self.assertIsNone(await self.conn.get_challenge_progress(self.winner, 'demo'))
        self.assertIsNone(await self.conn.get_challenge_progress(self.loser, 'demo'))

    async def test_progress_is_read_once_per_player(self):
        mgr = self.manager(
            DemoChallenge('a', 'demo_ach'), DemoChallenge('b', 'other_ach'), DemoChallenge('c', 'counter_ach'))

        with patch.object(self.conn, 'get_open_challenge_progress',
                          wraps=self.conn.get_open_challenge_progress) as read:
            await self.dispatch(mgr)

        self.assertEqual(read.await_count, 2)  # winner and loser, no matter how many challenges

    async def test_report_and_recording_are_passed_to_applies(self):
        recording = [DbRecordedMessage(self.FINISHED, self.winner, self.loser, 1, b'')]
        report = self.report()
        applies = Mock(return_value=True)
        mgr = self.manager(DemoChallenge(applies=applies, run=Mock(return_value=None)))

        await mgr.dispatch(report, recording)

        applies.assert_called_once_with(report, recording)

    async def test_report_and_recording_are_passed_to_run(self):
        recording = [DbRecordedMessage(self.FINISHED, self.winner, self.loser, 1, b'')]
        report = self.report()
        run = Mock(return_value=None)
        mgr = self.manager(DemoChallenge(run=run))

        await mgr.dispatch(report, recording)

        # no stored progress yet, so run() gets the decoded initial one ('null' -> None)
        run.assert_any_call(self.winner, None, report, recording)
        run.assert_any_call(self.loser, None, report, recording)

    # failures
    async def test_failing_run_does_not_affect_other_challenges(self):
        mgr = self.manager(
            DemoChallenge('bad_run', 'other_ach', run=Mock(side_effect=RuntimeError('boom'))),
            DemoChallenge('good', 'demo_ach'))

        with self.assertLogs(LOGGER, level='ERROR'):
            await self.dispatch(mgr)

        self.assertEqual(await self.awarded(self.winner), ['demo_ach'])
        self.assertIsNone(await self.conn.get_challenge_progress(self.winner, 'bad_run'))

    async def test_failing_applies_does_not_affect_other_challenges(self):
        mgr = self.manager(
            DemoChallenge('bad_applies', 'counter_ach', applies=Mock(side_effect=RuntimeError('boom'))),
            DemoChallenge('good', 'demo_ach'))

        with self.assertLogs(LOGGER, level='ERROR'):
            await self.dispatch(mgr)

        self.assertEqual(await self.awarded(self.winner), ['demo_ach'])
        self.assertIsNone(await self.conn.get_challenge_progress(self.winner, 'bad_applies'))

    async def test_read_failure_is_contained(self):
        challenge = DemoChallenge()
        mgr = self.manager(challenge)

        with patch.object(self.conn, 'get_open_challenge_progress', side_effect=RuntimeError('db down')), \
                self.assertLogs(LOGGER, level='ERROR'):
            await self.dispatch(mgr)

        self.assertEqual(challenge.run_calls, [])

    async def test_failed_save_means_no_award(self):
        mgr = self.manager(DemoChallenge())

        with patch.object(self.conn, 'save_challenge_progress', side_effect=RuntimeError('db down')), \
                self.assertLogs(LOGGER, level='ERROR'):
            await self.dispatch(mgr)

        self.assertIsNone(await self.conn.get_challenge_progress(self.winner, 'demo'))
        self.assertEqual(await self.awarded(self.winner), [])

    async def test_failed_award_keeps_completed_progress(self):
        mgr = self.manager(DemoChallenge())

        with patch.object(self.conn, 'award_achievement', side_effect=RuntimeError('db down')), \
                self.assertLogs(LOGGER, level='ERROR'):
            await self.dispatch(mgr)

        prog = await self.conn.get_challenge_progress(self.winner, 'demo')
        self.assertEqual(prog.completed_at, self.FINISHED)
        self.assertEqual(await self.awarded(self.winner), [])

    async def test_unknown_reward_key_is_logged(self):
        mgr = self.manager(DemoChallenge('demo', 'missing_ach'))

        with self.assertLogs(LOGGER, level='WARNING'):
            await self.dispatch(mgr)

        prog = await self.conn.get_challenge_progress(self.winner, 'demo')
        self.assertEqual(prog.completed_at, self.FINISHED)
        self.assertEqual(await self.awarded(self.winner), [])

    # reconciliation
    async def test_reconciliation_awards_completed_challenges(self):
        await self.conn.save_challenge_progress(self.winner, 'demo', 'null', completed_at=self.FINISHED)
        await self.conn.save_challenge_progress(self.loser, 'demo', 'null', completed_at=self.FINISHED)
        mgr = self.manager(DemoChallenge())

        await mgr.run_reconciliation()

        self.assertEqual(await self.awarded(self.winner), ['demo_ach'])
        self.assertEqual(await self.awarded(self.loser), ['demo_ach'])

    async def test_reconciliation_repairs_failed_award(self):
        mgr = self.manager(DemoChallenge())
        with patch.object(self.conn, 'award_achievement', side_effect=RuntimeError('db down')), \
                self.assertLogs(LOGGER, level='ERROR'):
            await self.dispatch(mgr)

        await mgr.run_reconciliation()

        self.assertEqual(await self.awarded(self.winner), ['demo_ach'])
        self.assertEqual(await self.awarded(self.loser), ['demo_ach'])

    async def test_reconciliation_is_idempotent(self):
        await self.conn.save_challenge_progress(self.winner, 'demo', 'null', completed_at=self.FINISHED)
        mgr = self.manager(DemoChallenge())

        await mgr.run_reconciliation()
        awarded_at = (await self.conn.get_user_achievements(self.winner))[0].awarded_at
        await mgr.run_reconciliation()

        self.assertEqual(await self.conn.get_user_achievements(self.winner),
                         [UserAchievement('demo_ach', awarded_at)])

    async def test_reconciliation_ignores_incomplete_and_unrelated_progress(self):
        await self.conn.save_challenge_progress(self.winner, 'demo', 'null')  # in progress
        await self.conn.save_challenge_progress(self.loser, 'unrelated', 'null', completed_at=self.FINISHED)
        mgr = self.manager(DemoChallenge())

        await mgr.run_reconciliation()

        self.assertEqual(await self.awarded(self.winner), [])
        self.assertEqual(await self.awarded(self.loser), [])

    async def test_reconciliation_logs_unknown_reward_key(self):
        await self.conn.save_challenge_progress(self.winner, 'demo', 'null', completed_at=self.FINISHED)
        mgr = self.manager(DemoChallenge('demo', 'missing_ach'))

        with self.assertLogs(LOGGER, level='WARNING'):
            await mgr.run_reconciliation()

        self.assertEqual(await self.awarded(self.winner), [])

    async def test_reconciliation_failure_is_contained(self):
        await self.conn.save_challenge_progress(self.winner, 'demo', 'null', completed_at=self.FINISHED)
        mgr = self.manager(DemoChallenge('broken', 'other_ach'), DemoChallenge())

        real = self.conn.get_unrewarded_challenge_user_ids

        # fails for one challenge only, the other one has to go through
        async def flaky(challenge_key, achievement_key):
            if challenge_key == 'broken':
                raise RuntimeError('db down')
            return await real(challenge_key, achievement_key)

        with patch.object(self.conn, 'get_unrewarded_challenge_user_ids', side_effect=flaky), \
                self.assertLogs(LOGGER, level='ERROR'):
            await mgr.run_reconciliation()

        self.assertEqual(await self.awarded(self.winner), ['demo_ach'])
