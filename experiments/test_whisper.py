import sounddevice as sd
import soundfile as sf

from faster_whisper import WhisperModel


# Audio configuration
SAMPLE_RATE = 16000
DURATION = 5
AUDIO_FILE = "experiments/recording.wav"


print("Loading Whisper model...")

model = WhisperModel(
    "small",
    device="cpu",
    compute_type="int8"
)

print("Whisper model loaded successfully!")

print("Recording starts now. Speak for 5 seconds.")

audio = sd.rec(
    int(DURATION * SAMPLE_RATE),
    samplerate=SAMPLE_RATE,
    channels=1,
    dtype="float32"
)

sd.wait()

sf.write(
    AUDIO_FILE,
    audio,
    SAMPLE_RATE
)

print("Recording completed.")

print("Converting speech to text...")

segments, info = model.transcribe(
    AUDIO_FILE,
    beam_size=5,
    vad_filter=True
)

print("\nDetected language:", info.language)

print("\nYou said:")

for segment in segments:
    print(segment.text.strip())