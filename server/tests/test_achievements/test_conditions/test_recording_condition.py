import unittest

from QRServer.achievements.conditions import BaseRecordingCondition, CounterCondition
from QRServer.achievements.conditions.recordings import (
    OrbPickupCountCondition,
    PowerUseCountCondition,
    RemovalBurstCondition,
    PiecesDestroyedCountCondition,
    UniqueCounterCondition,
    UniquePowersUsedCondition,
)
from QRServer.common.messages import (
    GetPowerSquareMessage, GrabPieceMessage, Message, NewGridCoordMessage, RemovePlayerMessage, UsePowerMessage,
)


class Moves(CounterCondition[NewGridCoordMessage]):
    message_type = NewGridCoordMessage


class RecordingCounterTest(unittest.TestCase):
    @staticmethod
    def feed(condition: BaseRecordingCondition, *messages: Message) -> BaseRecordingCondition:
        for message in messages:
            condition.feed(message)
        return condition

    @staticmethod
    def power_msg(name: str = 'INVERT') -> UsePowerMessage:
        return UsePowerMessage.new(name, 3)

    def test_counts_only_its_message_type(self):
        moves = Moves()

        self.feed(moves, self.power_msg(), NewGridCoordMessage.new(1, 2, 3, 4), GrabPieceMessage.new(1))

        self.assertEqual(moves.count, 1)

    def test_min_only(self):
        counter = Moves(min_count=2)

        self.assertFalse(counter.met)
        self.assertFalse(counter.done)
        self.feed(counter, NewGridCoordMessage.new(1, 2, 3, 4))
        self.assertFalse(counter.met)
        self.feed(counter, NewGridCoordMessage.new(1, 2, 3, 4))
        self.assertTrue(counter.met)
        self.assertTrue(counter.done)  # more messages can't undo it

    def test_max_only(self):
        counter = Moves(max_count=1)

        self.assertTrue(counter.met)
        self.assertFalse(counter.done)
        self.feed(counter, NewGridCoordMessage.new(1, 2, 3, 4))
        self.assertTrue(counter.met)
        self.assertFalse(counter.done)
        self.feed(counter, NewGridCoordMessage.new(1, 2, 3, 4))
        self.assertFalse(counter.met)
        self.assertTrue(counter.done)  # failed for good

    def test_max_zero_means_never(self):
        counter = Moves(max_count=0)

        self.assertTrue(counter.met)
        self.assertFalse(counter.done)
        self.feed(counter, NewGridCoordMessage.new(1, 2, 3, 4))
        self.assertFalse(counter.met)
        self.assertTrue(counter.done)

    def test_min_and_max_window(self):
        counter = Moves(min_count=2, max_count=3)
        move_msg = NewGridCoordMessage.new(1, 2, 3, 4)

        expected = [(False, False), (True, False), (True, False), (False, True)]  # (met, done) after 1..4 moves
        seen = []
        for _ in range(4):
            self.feed(counter, move_msg)
            seen.append((counter.met, counter.done))

        self.assertEqual(seen, expected)

    def test_without_limits_it_is_met_and_never_done(self):
        counter = Moves()

        self.feed(counter, NewGridCoordMessage.new(1, 2, 3, 4))

        self.assertTrue(counter.met)
        self.assertFalse(counter.done)

    def test_instances_do_not_share_state(self):
        a, b = Moves(), Moves()

        self.feed(a, NewGridCoordMessage.new(1, 2, 3, 4))

        self.assertEqual((a.count, b.count), (1, 0))

    def test_power_uses_all_or_specific(self):
        anything = PowerUseCountCondition()
        only_invert = PowerUseCountCondition('INVERT')

        for condition in (anything, only_invert):
            self.feed(condition, self.power_msg('INVERT'), self.power_msg('INVERT'), self.power_msg('ORBSPY'),
                      NewGridCoordMessage.new(1, 2, 3, 4))

        self.assertEqual(anything.count, 3)
        self.assertEqual(only_invert.count, 2)

    def test_unique_counter_counts_keys_not_messages(self):
        unique = UniquePowersUsedCondition(min_count=2)

        self.feed(unique, self.power_msg('INVERT'), self.power_msg('INVERT'), self.power_msg('INVERT'))
        self.assertEqual(unique.count, 1)
        self.assertFalse(unique.met)

        self.feed(unique, NewGridCoordMessage.new(1, 2, 3, 4), self.power_msg('ORBSPY'))
        self.assertEqual(unique.count, 2)
        self.assertTrue(unique.met)

    def test_unique_counter_requires_key(self):
        class NoKey(UniqueCounterCondition[GrabPieceMessage]):
            message_type = GrabPieceMessage

        with self.assertRaises(TypeError):
            NoKey().feed(GrabPieceMessage.new(1))


class PowerUseSetTest(unittest.TestCase):
    def test_a_collection_of_powers_counts_any_of_them(self):
        condition = PowerUseCountCondition({'INVERT', 'ORBSPY'}, min_count=3)

        for name in ('INVERT', 'ORBSPY', 'DESTROY', 'INVERT'):
            condition.feed(UsePowerMessage.new(name, 1))

        self.assertEqual(condition.count, 3)
        self.assertTrue(condition.met)

    def test_every_use_counts_not_only_unique_ones(self):
        condition = PowerUseCountCondition(['INVERT'], min_count=2)

        condition.feed(UsePowerMessage.new('INVERT', 1))
        condition.feed(UsePowerMessage.new('INVERT', 2))

        self.assertTrue(condition.met)

    def test_one_name_and_any_power_still_work(self):
        one = PowerUseCountCondition('INVERT')
        anything = PowerUseCountCondition(None)

        for name in ('INVERT', 'DESTROY'):
            for condition in (one, anything):
                condition.feed(UsePowerMessage.new(name, 1))

        self.assertEqual((one.count, anything.count), (1, 2))


class OrbPickupCountTest(unittest.TestCase):
    def test_counts_only_picked_up_orbs(self):
        condition = OrbPickupCountCondition(min_count=2)

        condition.feed(GetPowerSquareMessage.new(1, 2))
        condition.feed(UsePowerMessage.new('INVERT', 1))
        self.assertFalse(condition.met)

        condition.feed(GetPowerSquareMessage.new(3, 4))
        self.assertEqual(condition.count, 2)
        self.assertTrue(condition.met)


class RemovalConditionsTest(unittest.TestCase):
    @staticmethod
    def feed(condition, *pieces: int | None):
        """A piece is a removal of it, None is any other action of the user"""
        for piece in pieces:
            condition.feed(UsePowerMessage.new('INVERT', 1) if piece is None else RemovePlayerMessage.new(piece))
        return condition

    def test_count_includes_every_removed_piece_and_skips_the_kamikaze_filler(self):
        condition = self.feed(PiecesDestroyedCountCondition(min_count=3), 4, -1, 7, -1, -1, 9, None, 2)

        self.assertEqual(condition.count, 4)
        self.assertTrue(condition.met)

    def test_burst_counts_the_removals_in_a_row(self):
        condition = self.feed(RemovalBurstCondition(min_count=5), 39, 38, 35, 34, 32)

        self.assertEqual(condition.count, 5)
        self.assertTrue(condition.met)

    def test_burst_is_broken_by_any_other_action(self):
        condition = self.feed(RemovalBurstCondition(min_count=3), 1, 2, None, 3, 4, None, 5)

        self.assertEqual(condition.count, 2)
        self.assertFalse(condition.met)

    def test_burst_keeps_the_longest_row(self):
        condition = self.feed(RemovalBurstCondition(), 1, None, 2, 3, 4, None, 5, 6)

        self.assertEqual(condition.count, 3)

    def test_burst_skips_the_kamikaze_filler_without_breaking_the_row(self):
        condition = self.feed(RemovalBurstCondition(min_count=2), -1, -1, 22, -1, 10, -1)

        self.assertEqual(condition.count, 2)
        self.assertTrue(condition.met)

    def test_single_removal_is_a_burst_of_one(self):
        # a normal capture: the piece is removed, then the user moves on
        condition = self.feed(RemovalBurstCondition(), 12, None)

        self.assertEqual(condition.count, 1)

    def test_burst_instances_do_not_share_state(self):
        first = self.feed(RemovalBurstCondition(), 1, 2, 3)
        second = RemovalBurstCondition()

        self.assertEqual((first.count, second.count), (3, 0))
