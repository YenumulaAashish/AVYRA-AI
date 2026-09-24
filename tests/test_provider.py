from types import SimpleNamespace
from unittest.mock import Mock, patch
import httpx
import pytest
from openai import AuthenticationError, RateLimitError, APIConnectionError, APITimeoutError, BadRequestError
from avyra.providers.openai_provider import OpenAIProvider
from avyra.providers.base import ProviderError


def test_success(config):
    client = Mock()
    client.responses.create.return_value = SimpleNamespace(status="completed", output_text=" Answer ")
    adapter = OpenAIProvider(config, client)
    messages = [{"role":"user","content":"Hello"}]
    assert adapter.generate(messages, "Instructions") == "Answer"
    client.responses.create.assert_called_once_with(model="gpt-4.1-mini",instructions="Instructions",input=messages,store=False,max_output_tokens=2048)
    adapter.close()
    client.close.assert_called_once()


def test_sdk_configuration(config):
    with patch("avyra.providers.openai_provider.OpenAI") as sdk:
        OpenAIProvider(config)
    sdk.assert_called_once_with(api_key=config.api_key,timeout=30.0,max_retries=0)

@pytest.mark.parametrize("kind,expected", [(AuthenticationError,"Authentication"),(RateLimitError,"quota"),(APIConnectionError,"connect"),(APITimeoutError,"timed out"),(BadRequestError,"model access"),(RuntimeError,"Unexpected")])
def test_errors_sanitized(config, kind, expected):
    req = httpx.Request("POST", "https://example.invalid")
    if kind in (AuthenticationError, RateLimitError, BadRequestError):
        error = kind("SECRET", response=httpx.Response(400,request=req), body=None)
    elif kind is APITimeoutError:
        error = kind(request=req)
    elif kind is APIConnectionError:
        error = kind(message="SECRET",request=req)
    else:
        error = kind("SECRET")
    client = Mock()
    client.responses.create.side_effect = error
    with pytest.raises(ProviderError) as caught:
        OpenAIProvider(config,client).generate([], "instructions")
    assert expected in str(caught.value)
    assert "SECRET" not in str(caught.value)
    assert caught.value.__suppress_context__

@pytest.mark.parametrize("response", [None, SimpleNamespace(status="incomplete",output_text="partial"),SimpleNamespace(status="completed",output_text=" "),SimpleNamespace(status="completed",output_text=None),SimpleNamespace(status="completed")])
def test_unusable_response(config,response):
    client = Mock()
    client.responses.create.return_value = response
    with pytest.raises(ProviderError):
        OpenAIProvider(config,client).generate([], "instructions")


def test_real_sdk_with_mock_http_transport(config):
    """Exercise SDK serialization and output_text without any real network."""
    import json
    from openai import OpenAI
    captured = []
    def handler(request):
        captured.append(json.loads(request.content))
        return httpx.Response(200, json={
            "id":"resp_test", "object":"response", "created_at":0,
            "status":"completed", "model":"gpt-4.1-mini",
            "output":[{"id":"msg_test", "type":"message", "role":"assistant",
                       "status":"completed", "content":[{"type":"output_text",
                       "text":"SDK response", "annotations":[]}]}]
        })
    client = OpenAI(api_key=config.api_key, max_retries=0,
                    http_client=httpx.Client(transport=httpx.MockTransport(handler)))
    adapter = OpenAIProvider(config, client)
    try:
        assert adapter.generate([{"role":"user","content":"Hi"}], "AVYRA") == "SDK response"
        assert captured[0]["store"] is False
        assert captured[0]["input"] == [{"role":"user","content":"Hi"}]
    finally:
        adapter.close()
