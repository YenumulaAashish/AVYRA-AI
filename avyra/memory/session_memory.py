"""Session-only storage; owns ordering, limits, and defensive copies."""
from avyra.providers.base import Message


class SessionMemory:
    def __init__(self, max_messages: int = 20):
        if type(max_messages) is not int or max_messages < 2 or max_messages % 2:
            raise ValueError("History capacity must be an even integer of at least 2.")
        self.max_messages = max_messages
        self._messages: list[Message] = []

    def add_messages(self, messages: list[Message]) -> None:
        # Validate the entire batch before mutating storage.
        for message in messages:
            if message.get("role") not in {"user", "assistant"} or not isinstance(message.get("content"), str) or not message["content"].strip():
                raise ValueError("Messages require a user/assistant role and nonempty text.")
        self._messages = (self._messages + [m.copy() for m in messages])[-self.max_messages:]

    def get_messages(self) -> list[Message]:
        return [message.copy() for message in self._messages]

    def clear(self) -> None:
        self._messages.clear()
