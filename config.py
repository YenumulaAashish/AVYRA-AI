"""Validated configuration; environment variables override the project .env."""
from dataclasses import dataclass, field
import os
from pathlib import Path

from dotenv import load_dotenv


class ConfigurationError(ValueError):
    """A safe, user-facing configuration error."""


@dataclass(frozen=True)
class Config:
    api_key: str = field(repr=False)
    model: str = "gpt-4.1-mini"
    debug: bool = False
    max_history: int = 20
    stt_model: str = "small"
    stt_device: str = "cpu"
    stt_compute_type: str = "int8"
    tts_voice: str = "en-US-AriaNeural"

    def __post_init__(self):
        for value in (self.stt_model, self.tts_voice):
            if not isinstance(value, str) or not value.strip() or any(c.isspace() for c in value):
                raise ConfigurationError("STT model and TTS voice must be nonempty identifiers without whitespace.")
        if self.stt_device not in {"cpu", "cuda", "auto"}:
            raise ConfigurationError("AVYRA_STT_DEVICE must be cpu, cuda, or auto.")
        if self.stt_compute_type not in {"int8", "int8_float32", "int8_float16", "int8_bfloat16", "int16", "float16", "float32", "bfloat16", "default", "auto"}:
            raise ConfigurationError("AVYRA_STT_COMPUTE_TYPE is not supported.")
        if not isinstance(self.api_key, str) or not self.api_key.strip() or self.api_key.strip() == "your_api_key_here":
            raise ConfigurationError("Set OPENAI_API_KEY in your environment or copy .env.example to .env and enter your key.")
        if not isinstance(self.model, str) or not self.model.strip() or any(c.isspace() for c in self.model):
            raise ConfigurationError("OPENAI_MODEL must be a nonempty model identifier without whitespace.")
        if type(self.debug) is not bool:
            raise ConfigurationError("AVYRA_DEBUG must be true or false.")
        if type(self.max_history) is not int or not 2 <= self.max_history <= 200 or self.max_history % 2:
            raise ConfigurationError("AVYRA_MAX_HISTORY must be an even integer between 2 and 200 (messages).")

    @classmethod
    def from_env(cls, env_file: Path | None = None):
        load_dotenv(env_file if env_file is not None else Path(__file__).with_name(".env"), override=False)
        debug = os.getenv("AVYRA_DEBUG", "false").strip().lower()
        if debug not in {"true", "false"}:
            raise ConfigurationError("AVYRA_DEBUG must be true or false.")
        try:
            limit = int(os.getenv("AVYRA_MAX_HISTORY", "20"))
        except ValueError:
            raise ConfigurationError("AVYRA_MAX_HISTORY must be an even integer between 2 and 200.") from None
        return cls(os.getenv("OPENAI_API_KEY", "").strip(), os.getenv("OPENAI_MODEL", "gpt-4.1-mini").strip(), debug == "true", limit,
                   os.getenv("AVYRA_STT_MODEL", "small").strip(),
                   os.getenv("AVYRA_STT_DEVICE", "cpu").strip(),
                   os.getenv("AVYRA_STT_COMPUTE_TYPE", "int8").strip(),
                   os.getenv("AVYRA_TTS_VOICE", "en-US-AriaNeural").strip())
