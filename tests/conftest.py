import socket
from unittest.mock import Mock, patch
import pytest
from config import Config
from avyra.providers.base import AIProvider

@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Network is forbidden in tests")
    # Windows asyncio creates its internal wakeup socket pair through loopback.
    # Permit only that stdlib operation, while service connections stay blocked.
    original_connect = socket.socket.connect
    original_socketpair = socket.socketpair
    def internal_socketpair(*args, **kwargs):
        with patch.object(socket.socket, "connect", original_connect):
            return original_socketpair(*args, **kwargs)
    monkeypatch.setattr(socket, "socketpair", internal_socketpair)
    monkeypatch.setattr(socket.socket, "connect", blocked)

@pytest.fixture
def config():
    return Config("test-only-not-a-real-key")

@pytest.fixture
def provider():
    result = Mock(spec=AIProvider)
    result.generate.return_value = "A useful answer"
    return result
