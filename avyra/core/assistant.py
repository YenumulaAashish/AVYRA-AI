"""Reusable composition root for terminal and future frontends."""
from config import Config
from avyra.core.brain import Brain
from avyra.core.conversation import ConversationManager
from avyra.memory.session_memory import SessionMemory
from avyra.providers.base import AIProvider
from avyra.providers.openai_provider import OpenAIProvider
from avyra.tools.registry import ToolRegistry


class Assistant:
    def __init__(self, config: Config, provider: AIProvider | None = None):
        self.config = config
        self.memory = SessionMemory(config.max_history)
        self.conversation = ConversationManager(self.memory)
        self.provider = provider if provider is not None else OpenAIProvider(config)
        self.brain = Brain(self.provider, self.conversation)
        self.tools = ToolRegistry()

    def respond(self, text: str) -> str:
        return self.brain.respond(text)

    def clear(self) -> None:
        self.conversation.clear()

    def status(self) -> dict:
        return {"model": self.config.model, "messages": len(self.conversation.history()), "history_limit": self.config.max_history, "memory": "session only", "tools": len(self.tools.list_tools())}

    def close(self) -> None:
        self.provider.close()
