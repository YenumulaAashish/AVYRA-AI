"""Edge speech synthesis with temporary MP3 playback and cleanup."""
import asyncio
from pathlib import Path
from tempfile import TemporaryDirectory
from avyra.voice.errors import VoiceError


class SpeechOutput:
    def __init__(self, voice):
        self.voice = voice

    async def _save(self, text, path):
        import edge_tts
        await asyncio.wait_for(edge_tts.Communicate(text, self.voice).save(str(path)), timeout=60)

    def speak(self, text):
        if not text.strip():
            return
        try:
            import sounddevice as sd
            import soundfile as sf
            with TemporaryDirectory(prefix="avyra-tts-") as directory:
                path = Path(directory) / "response.mp3"
                asyncio.run(self._save(text, path))
                audio, sample_rate = sf.read(str(path), dtype="float32")
                try:
                    sd.play(audio, sample_rate)
                    status = sd.wait()
                    if status:
                        raise VoiceError("Audio playback was interrupted.")
                finally:
                    sd.stop()
        except (KeyboardInterrupt, EOFError):
            raise
        except Exception:
            raise VoiceError("Speech output failed. Check internet access, AVYRA_TTS_VOICE and the default speaker device. The text reply is still available.") from None
