"""One lazily loaded Faster-Whisper model per voice session."""
from avyra.voice.errors import VoiceError


class SpeechRecognizer:
    def __init__(self, config):
        self.config = config
        self._model = None

    def transcribe(self, audio):
        try:
            if self._model is None:
                from faster_whisper import WhisperModel
                self._model = WhisperModel(self.config.stt_model,
                                           device=self.config.stt_device,
                                           compute_type=self.config.stt_compute_type)
            # language=None auto-detects English and multilingual speech.
            segments, _ = self._model.transcribe(audio, language=None,
                                                 vad_filter=True, beam_size=5)
            return " ".join(segment.text.strip() for segment in segments).strip()
        except Exception:
            raise VoiceError("Speech recognition failed. Check the Whisper model download, device and compute-type settings.") from None
