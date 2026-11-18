from collections.abc import Hashable
from abc import abstractmethod
from typing import Generic

from QRServer.achievements.conditions.recordings.base import MessageType, BaseRecordingCondition
from QRServer.common.messages import Message, UsePowerMessage


class CounterCondition(BaseRecordingCondition, Generic[MessageType]):
    """Counts the user's messages of `message_type` that pass `counts()`.
    Subclass: set message_type, override counts() if you need additional checks."""
    message_type: type[MessageType]

    def __init__(self, min_count: int | None = None, max_count: int | None = None) -> None:
        self.min_count = min_count
        self.max_count = max_count
        self.count = 0

    def counts(self, message: MessageType) -> bool:
        """Override if you need to check anything other than message type (for example specific power use args)"""
        return True

    def _record(self, message: MessageType) -> None:
        self.count += 1

    def feed(self, message: Message) -> None:
        if isinstance(message, self.message_type) and self.counts(message):
            self._record(message)

    @property
    def met(self) -> bool:
        return ((self.min_count is None or self.count >= self.min_count)
                and (self.max_count is None or self.count <= self.max_count))

    @property
    def done(self) -> bool:
        if self.max_count is not None:
            return self.count > self.max_count  # Crossed the max threshold, feeding more messages won't change that
        return self.min_count is not None and self.count >= self.min_count


class UniqueCounterCondition(CounterCondition[MessageType]):
    """Counts unique key() values instead of messages."""

    def __init__(self, min_count: int | None = None, max_count: int | None = None) -> None:
        super().__init__(min_count, max_count)
        self._seen: set[Hashable] = set()

    @abstractmethod
    def key(self, message: MessageType) -> Hashable:
        pass

    def _record(self, message: MessageType) -> None:
        self._seen.add(self.key(message))
        self.count = len(self._seen)


class PowerUseCountCondition(CounterCondition[UsePowerMessage]):
    """Counts how many times a specified powerup was used."""
    message_type = UsePowerMessage

    def __init__(self, power: str | None = None,
                 min_count: int | None = None, max_count: int | None = None) -> None:
        super().__init__(min_count, max_count)
        self.power = power

    def counts(self, message: UsePowerMessage) -> bool:
        return self.power is None or message.get_power_name() == self.power


class UniquePowersUsedCondition(UniqueCounterCondition[UsePowerMessage]):
    """Counts how many unique powers were used (regardless of how many times)."""
    message_type = UsePowerMessage

    def key(self, message: UsePowerMessage) -> Hashable:
        return message.get_power_name()
