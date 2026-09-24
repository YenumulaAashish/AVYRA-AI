"""Conversation policy: prepare context and commit successful turn pairs."""
from avyra.memory.session_memory import SessionMemory
from avyra.providers.base import Message


class ConversationManager:
    def __init__(self, memory: SessionMemory):
        self.memory = memory

    def context_for(self, text: str) -> list[Message]:
        # Reserve room for the new turn; never send an orphaned assistant reply.
        history = self.history()
        keep = self.memory.max_messages - 2
        return (history[-keep:] if keep else []) + [{"role": "user", "content": text}]

    def record_turn(self, user: str, assistant: str) -> None:
        self.memory.add_messages([{"role": "user", "content": user}, {"role": "assistant", "content": assistant}])

    def history(self) -> list[Message]:
        return self.memory.get_messages()

    def clear(self) -> None:
        self.memory.clear()
