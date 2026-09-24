import pytest
from avyra.core.assistant import Assistant
from avyra.providers.base import ProviderError

def test_composition(config,provider):
    assistant = Assistant(config,provider)
    assert assistant.respond("Hi") == "A useful answer"
    assert assistant.status()["messages"] == 2
    assert assistant.status()["tools"] == 0
    assert config.api_key not in str(assistant.status())
    assistant.clear()
    assert assistant.status()["messages"] == 0
    assistant.close()
    provider.close.assert_called_once()

def test_failure(config,provider):
    provider.generate.side_effect = ProviderError("Unavailable")
    assistant = Assistant(config,provider)
    with pytest.raises(ProviderError):
        assistant.respond("Hi")
    assert assistant.status()["messages"] == 0
