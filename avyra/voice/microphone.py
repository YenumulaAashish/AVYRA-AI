"""Explicitly started, bounded 16 kHz mono recording."""
from avyra.voice.errors import VoiceError


class Microphone:
    SAMPLE_RATE = 16000
    MAX_SECONDS = 120

    def record(self, read=input, write=print):
        """Caller obtains start consent; this method waits for Enter to stop."""
        import numpy as np
        import sounddevice as sd
        chunks = []
        frames_recorded = 0
        overflow = False
        limit_reached = False

        def callback(indata, frames, time_info, status):
            nonlocal frames_recorded, overflow, limit_reached
            if status:
                overflow = True
            remaining = self.SAMPLE_RATE * self.MAX_SECONDS - frames_recorded
            if remaining > 0:
                chunk = indata[:remaining, 0].copy()
                chunks.append(chunk)
                frames_recorded += len(chunk)
            if frames_recorded >= self.SAMPLE_RATE * self.MAX_SECONDS:
                limit_reached = True
                raise sd.CallbackStop

        try:
            with sd.InputStream(samplerate=self.SAMPLE_RATE, channels=1,
                                dtype="float32", callback=callback):
                write("Recording. Press Enter to stop (120-second maximum).")
                read("")
        except (KeyboardInterrupt, EOFError):
            raise
        except Exception:
            raise VoiceError("Microphone unavailable. Check Windows microphone permissions and the default input device.") from None
        finally:
            write("Recording stopped.")
        if overflow:
            raise VoiceError("Audio capture was interrupted or overflowed. Please record again.")
        if limit_reached:
            write("Recording reached the 120-second limit.")
        if not chunks:
            raise VoiceError("No audio captured. Check your microphone and try again.")
        return np.concatenate(chunks)
