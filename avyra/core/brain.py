"""UI-independent request orchestration."""
import logging
from avyra.core.conversation import ConversationManager
from avyra.providers.base import AIProvider, ProviderError
from avyra.prompts.system import SYSTEM_PROMPT

logger = logging.getLogger("avyra")
MAX_INPUT_CHARACTERS = 16000


class Brain:
    def __init__(self, provider: AIProvider, conversation: ConversationManager):
        self.provider = provider
        self.conversation = conversation

    def respond(self, text: str) -> str:
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Please enter a nonempty message.")
        text = text.strip()
        if len(text) > MAX_INPUT_CHARACTERS:
            raise ValueError("Message is too long; use at most 16000 characters.")
        reply = self.provider.generate(self.conversation.context_for(text), SYSTEM_PROMPT)
        if not isinstance(reply, str) or not reply.strip():
            raise ProviderError("The AI service returned no usable text.")
        reply = reply.strip()
        self.conversation.record_turn(text, reply)
        logger.debug("Completed one conversation turn.")
        return reply
