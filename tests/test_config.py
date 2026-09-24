from unittest.mock import patch
import pytest
from config import Config, ConfigurationError

@pytest.mark.parametrize("values", [{}, {"OPENAI_API_KEY":""}, {"OPENAI_API_KEY":"your_api_key_here"}])
def test_missing_key(values, tmp_path):
    with patch.dict("os.environ", values, clear=True), pytest.raises(ConfigurationError):
        Config.from_env(tmp_path / "absent")

def test_defaults_and_secret_repr(tmp_path):
    with patch.dict("os.environ", {"OPENAI_API_KEY":"private-test-value"}, clear=True):
        config = Config.from_env(tmp_path / "absent")
    assert config.model == "gpt-4.1-mini"
    assert config.max_history == 20
    assert not config.debug
    assert "private-test-value" not in repr(config)

@pytest.mark.parametrize("key,value", [("AVYRA_DEBUG","maybe"),("AVYRA_MAX_HISTORY","bad"),("AVYRA_MAX_HISTORY","0"),("AVYRA_MAX_HISTORY","3"),("AVYRA_MAX_HISTORY","202"),("OPENAI_MODEL", "")])
def test_invalid_values(key, value, tmp_path):
    with patch.dict("os.environ", {"OPENAI_API_KEY":"test-key",key:value}, clear=True), pytest.raises(ConfigurationError):
        Config.from_env(tmp_path / "absent")

def test_dotenv_and_environment_precedence(tmp_path):
    env = tmp_path / ".env"
    env.write_text("OPENAI_API_KEY=file-test-key\nOPENAI_MODEL=file-model\nAVYRA_DEBUG=true\nAVYRA_MAX_HISTORY=4\n")
    with patch.dict("os.environ", {"OPENAI_MODEL":"environment-model"}, clear=True):
        config = Config.from_env(env)
    assert (config.model, config.debug, config.max_history) == ("environment-model", True, 4)
