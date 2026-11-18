import unittest

from QRServer.achievements.conditions import BaseRecordingCondition, CounterCondition
from QRServer.achievements.conditions.recordings import (
    PowerUseCountCondition,
    UniqueCounterCondition,
    UniquePowersUsedCondition,
)
from QRServer.common.messages import GrabPieceMessage, Message, NewGridCoordMessage, UsePowerMessage


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
