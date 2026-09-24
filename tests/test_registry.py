import pytest
from avyra.tools.registry import ToolRegistry, ToolDefinition

def test_registry():
    registry = ToolRegistry()
    assert registry.list_tools() == ()
    tool = ToolDefinition("example", "Metadata only", ("example.read",))
    registry.register(tool)
    assert registry.get("example") == tool
    assert registry.list_tools() == (tool,)
    assert tool.requires_confirmation
    with pytest.raises(ValueError):
        registry.register(tool)
    with pytest.raises(KeyError):
        registry.get("missing")
    assert not hasattr(registry,"execute")

@pytest.mark.parametrize("name,permissions",[("bad name",("read",)),("valid",()),("valid",("",))])
def test_invalid_metadata(name,permissions):
    with pytest.raises(ValueError):
        ToolDefinition(name,"Description",permissions)
