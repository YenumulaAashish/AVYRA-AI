"""Push-to-talk orchestration using the existing Assistant instance."""
from avyra.voice.errors import VoiceError
from avyra.providers.base import ProviderError


def run_voice(assistant, microphone, recognizer, speech, read=input, write=print):
    write("AVYRA AI V1.1 - Voice mode")
    write("Press Enter to start, then Enter to stop. Type /help for commands. Microphone is off while idle.")
    try:
        while True:
            command = read("Voice> ").strip()
            if command == "/exit":
                break
            if command:
                from main import handle_command
                if not handle_command(assistant, command, write):
                    write("Press Enter to record, or use /help.")
                continue
            try:
                audio = microphone.record(read, write)
                write("Transcribing locally (first use may download the Whisper model)...")
                text = recognizer.transcribe(audio)
                if not text:
                    write("No speech detected. Press Enter to try again.")
                    continue
                write("You: " + text)
                reply = assistant.respond(text)
                write("AVYRA: " + reply)
                write("Speaking...")
                speech.speak(reply)
            except (KeyboardInterrupt, EOFError):
                raise
            except (VoiceError, ProviderError, ValueError) as exc:
                write("Error: " + str(exc))
            except Exception:
                write("Error: Voice interaction failed. Please try again or restart in text mode.")
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        assistant.close()
    write("AVYRA: Goodbye!")
    return 0
