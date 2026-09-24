"""OpenAI Responses adapter with bounded requests and sanitized errors."""
from openai import OpenAI, AuthenticationError, RateLimitError, APIConnectionError, APITimeoutError, APIError
from config import Config
from avyra.providers.base import AIProvider, Message, ProviderError


class OpenAIProvider(AIProvider):
    def __init__(self, config: Config, client=None):
        self.model = config.model
        self.client = client if client is not None else OpenAI(api_key=config.api_key, timeout=30.0, max_retries=0)

    def generate(self, messages: list[Message], instructions: str) -> str:
        try:
            response = self.client.responses.create(model=self.model, instructions=instructions, input=messages, store=False, max_output_tokens=2048)
        except AuthenticationError:
            raise ProviderError("Authentication failed. Check OPENAI_API_KEY and account access.") from None
        except RateLimitError:
            raise ProviderError("OpenAI rate or quota limit reached. Check your quota or try again later.") from None
        except APITimeoutError:
            raise ProviderError("OpenAI request timed out. Please try again.") from None
        except APIConnectionError:
            raise ProviderError("Cannot connect to OpenAI. Check your connection and try again.") from None
        except APIError:
            raise ProviderError("OpenAI could not complete the request. Check model access or try again later.") from None
        except Exception:
            raise ProviderError("Unexpected AI service failure. Please try again.") from None
        if getattr(response, "status", None) != "completed":
            raise ProviderError("OpenAI returned an incomplete response. Please try again.")
        text = getattr(response, "output_text", None)
        if not isinstance(text, str) or not text.strip():
            raise ProviderError("OpenAI returned no usable text. Please try again.")
        return text.strip()

    def close(self) -> None:
        self.client.close()
