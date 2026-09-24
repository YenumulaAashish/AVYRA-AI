import pytest
from avyra.core.conversation import ConversationManager
from avyra.memory.session_memory import SessionMemory

def test_order_limits_and_context():
    manager = ConversationManager(SessionMemory(4))
    manager.record_turn("one","first")
    manager.record_turn("two","second")
    assert [m["content"] for m in manager.context_for("three")] == ["two","second","three"]
    manager.record_turn("three","third")
    assert [m["content"] for m in manager.history()] == ["two","second","three","third"]
    manager.clear()
    assert manager.history() == []

def test_defensive_copies_and_atomic_validation():
    memory = SessionMemory(2)
    messages = [{"role":"user","content":"hello"}]
    memory.add_messages(messages)
    messages[0]["content"] = "changed"
    memory.get_messages()[0]["content"] = "changed again"
    assert memory.get_messages()[0]["content"] == "hello"
    with pytest.raises(ValueError):
        memory.add_messages([{"role":"assistant","content":"valid"},{"role":"system","content":"invalid"}])
    assert len(memory.get_messages()) == 1

def test_minimum_limit():
    manager = ConversationManager(SessionMemory(2))
    manager.record_turn("old", "answer")
    assert manager.context_for("new") == [{"role":"user","content":"new"}]

@pytest.mark.parametrize("limit",[0,1,3,True])
def test_invalid_limits(limit):
    with pytest.raises(ValueError):
        SessionMemory(limit)
