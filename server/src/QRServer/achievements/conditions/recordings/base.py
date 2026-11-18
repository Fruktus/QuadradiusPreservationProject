from abc import ABC, abstractmethod
from typing import TypeVar

from QRServer.common.messages import Message

MessageType = TypeVar('MessageType', bound=Message)


class BaseRecordingCondition(ABC):
    """Stateful recording analysis helper, used to detect specific condition.
    Fed one message at a time.
    One fresh instance per run() (per user per match)."""

    @abstractmethod
    def feed(self, message: Message) -> None:
        """Used to analyze consecutive messages. Order may matter - it is expected to be the same as in recording"""
        pass

    @property
    @abstractmethod
    def met(self) -> bool:
        """Whether the condition of this analyzer would be met in its current state.
        Feeding more messages may change that."""

    @property
    def done(self) -> bool:
        """True if feeding more messages won't change the outcome (for example exceeded max condition).
        Allows early stopping."""
        return False
