import socket
from unittest.mock import Mock
import pytest
from config import Config
from avyra.providers.base import AIProvider

@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Network is forbidden in tests")
    monkeypatch.setattr(socket.socket, "connect", blocked)

@pytest.fixture
def config():
    return Config("test-only-not-a-real-key")

@pytest.fixture
def provider():
    result = Mock(spec=AIProvider)
    result.generate.return_value = "A useful answer"
    return result
