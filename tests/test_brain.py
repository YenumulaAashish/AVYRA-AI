import pytest
from avyra.core.brain import Brain
from avyra.core.conversation import ConversationManager
from avyra.memory.session_memory import SessionMemory
from avyra.providers.base import ProviderError
from avyra.prompts.system import SYSTEM_PROMPT

def test_turns_and_context(provider):
    conversation = ConversationManager(SessionMemory())
    brain = Brain(provider,conversation)
    assert brain.respond(" Hello ") == "A useful answer"
    brain.respond("Follow up")
    messages, instructions = provider.generate.call_args.args
    assert messages == [{"role":"user","content":"Hello"},{"role":"assistant","content":"A useful answer"},{"role":"user","content":"Follow up"}]
    assert instructions == SYSTEM_PROMPT
    assert len(conversation.history()) == 4

@pytest.mark.parametrize("bad", ["", "   ", None, "x" * 16001])
def test_invalid_input(provider,bad):
    brain = Brain(provider,ConversationManager(SessionMemory()))
    with pytest.raises(ValueError):
        brain.respond(bad)
    provider.generate.assert_not_called()

def test_failure_then_retry(provider):
    conversation = ConversationManager(SessionMemory())
    brain = Brain(provider,conversation)
    provider.generate.side_effect = [ProviderError("Unavailable"), "Recovered"]
    with pytest.raises(ProviderError):
        brain.respond("Hello")
    assert conversation.history() == []
    assert brain.respond("Hello") == "Recovered"
    assert len(conversation.history()) == 2

@pytest.mark.parametrize("reply",["", " ",None])
def test_invalid_reply(provider,reply):
    provider.generate.return_value = reply
    conversation = ConversationManager(SessionMemory())
    with pytest.raises(ProviderError):
        Brain(provider,conversation).respond("Hi")
    assert conversation.history() == []
