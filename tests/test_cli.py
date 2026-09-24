from unittest.mock import Mock, patch
import pytest
from config import ConfigurationError
from avyra.core.assistant import Assistant
from avyra.providers.base import ProviderError
from main import run_cli, main

def test_commands_and_recovery(config,provider):
    provider.generate.side_effect = [ProviderError("Temporary failure"), "Recovered"]
    assistant = Assistant(config,provider)
    read = Mock(side_effect=["", "/help", "/model", "/status", "/unknown", "hello", "retry", "/clear", "/exit"])
    output = []
    assert run_cli(assistant,read,output.append) == 0
    assert provider.generate.call_count == 2
    assert assistant.status()["messages"] == 0
    combined = "\n".join(output)
    for expected in ["/help",config.model,"session only","Unknown command","Temporary failure","Recovered","cleared","Goodbye"]:
        assert expected in combined
    assert config.api_key not in combined
    provider.close.assert_called_once()

@pytest.mark.parametrize("interruption",[EOFError,KeyboardInterrupt])
def test_exit_interrupt(config,provider,interruption):
    assert run_cli(Assistant(config,provider),Mock(side_effect=interruption),Mock()) == 0
    provider.close.assert_called_once()

def test_missing_config(capsys):
    with patch("config.Config.from_env",side_effect=ConfigurationError("Set OPENAI_API_KEY")):
        assert main() == 1
    assert "Setup error" in capsys.readouterr().err
