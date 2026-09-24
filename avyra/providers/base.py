"""Provider contract independent of transport and terminal UI."""
from abc import ABC, abstractmethod
from typing import Literal, TypedDict


class Message(TypedDict):
    role: Literal["user", "assistant"]
    content: str


class ProviderError(RuntimeError):
    """A sanitized error safe to display to the user."""


class AIProvider(ABC):
    @abstractmethod
    def generate(self, messages: list[Message], instructions: str) -> str:
        """Return a complete reply or raise ProviderError with no sensitive data."""

    def close(self) -> None:
        """Release resources, if any."""
