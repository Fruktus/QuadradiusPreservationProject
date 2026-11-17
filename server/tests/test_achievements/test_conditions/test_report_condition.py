from dataclasses import replace
from datetime import datetime, timezone
import unittest

from QRServer.achievements.conditions import ReportCondition, GridSize, SquadronSize
from QRServer.db.models import DbMatchReport


class ReportConditionTest(unittest.TestCase):
    def setUp(self):
        self.report = DbMatchReport(
            match_id='1234',
            winner_id='winner',
            loser_id='loser',
            winner_pieces_left=5,
            loser_pieces_left=0,
            move_counter=20,
            grid_size=GridSize.MEDIUM,
            squadron_size=SquadronSize.LARGE,
            started_at=datetime(2020, 1, 1, 0, 0, 0, tzinfo=timezone.utc),
            finished_at=datetime(2020, 1, 1, 1, 0, 0, tzinfo=timezone.utc),
            is_ranked=True,
            is_void=False,
        )

    def test_empty_condition_always_met(self):
        self.assertTrue(ReportCondition().met(self.report, 'winner'))
        self.assertTrue(ReportCondition().met(self.report, 'loser'))

    def test_won_is_evaluated_from_users_point_of_view(self):
        self.assertTrue(ReportCondition(won=True).met(self.report, 'winner'))
        self.assertFalse(ReportCondition(won=True).met(self.report, 'loser'))
        self.assertTrue(ReportCondition(won=False).met(self.report, 'loser'))
        self.assertFalse(ReportCondition(won=False).met(self.report, 'winner'))

    def test_grid_single_value(self):
        report = replace(self.report, grid_size=GridSize.SMALL)

        self.assertTrue(ReportCondition(grid=GridSize.SMALL).met(report, 'winner'))
        self.assertFalse(ReportCondition(grid=GridSize.LARGE).met(report, 'winner'))

    def test_grid_collection(self):
        report = replace(self.report, grid_size=GridSize.SMALL)

        self.assertTrue(ReportCondition(grid=[GridSize.SMALL, GridSize.LARGE]).met(report, 'winner'))
        self.assertFalse(ReportCondition(grid=[GridSize.MEDIUM, GridSize.LARGE]).met(report, 'winner'))

    def test_squadron_single_value_and_collection(self):
        report = replace(self.report, squadron_size=SquadronSize.SMALL)

        self.assertTrue(ReportCondition(squadron=SquadronSize.SMALL).met(report, 'winner'))
        self.assertFalse(ReportCondition(squadron=SquadronSize.LARGE).met(report, 'winner'))
        self.assertTrue(ReportCondition(squadron={SquadronSize.SMALL, SquadronSize.MEDIUM}).met(report, 'winner'))
        self.assertFalse(ReportCondition(squadron=(SquadronSize.LARGE,)).met(report, 'winner'))

    def test_move_bounds_are_inclusive(self):
        # move_counter is 20
        self.assertTrue(ReportCondition(min_moves=20, max_moves=20).met(self.report, 'winner'))
        self.assertFalse(ReportCondition(min_moves=21).met(self.report, 'winner'))
        self.assertFalse(ReportCondition(max_moves=19).met(self.report, 'winner'))

    def test_pieces_are_the_users_own(self):
        # winner has 5 pieces left, loser has 0
        self.assertTrue(ReportCondition(min_pieces=5).met(self.report, 'winner'))
        self.assertFalse(ReportCondition(min_pieces=5).met(self.report, 'loser'))
        self.assertTrue(ReportCondition(max_pieces=0).met(self.report, 'loser'))
        self.assertFalse(ReportCondition(max_pieces=0).met(self.report, 'winner'))

    def test_all_set_fields_must_be_met(self):
        condition = ReportCondition(won=True, grid=GridSize.MEDIUM, max_moves=30, min_pieces=5)

        self.assertTrue(condition.met(self.report, 'winner'))
        self.assertFalse(condition.met(replace(self.report, move_counter=31), 'winner'))
        self.assertFalse(condition.met(self.report, 'loser'))

    def test_seconds_bounds_are_inclusive(self):
        # started_at 00:00:00, finished_at 01:00:00, so 3600 seconds
        self.assertTrue(ReportCondition(min_seconds=3600, max_seconds=3600).met(self.report, 'winner'))
        self.assertFalse(ReportCondition(min_seconds=3601).met(self.report, 'winner'))
        self.assertFalse(ReportCondition(max_seconds=3599).met(self.report, 'winner'))

    def test_seconds_are_measured_between_start_and_finish(self):
        report = replace(self.report, finished_at=datetime(2020, 1, 1, 0, 0, 45, tzinfo=timezone.utc))

        self.assertTrue(ReportCondition(max_seconds=45).met(report, 'winner'))
        self.assertFalse(ReportCondition(min_seconds=46).met(report, 'winner'))

    def test_seconds_do_not_depend_on_user(self):
        condition = ReportCondition(min_seconds=3600)

        self.assertTrue(condition.met(self.report, 'winner'))
        self.assertTrue(condition.met(self.report, 'loser'))
