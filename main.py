"""AVYRA terminal interface. Run with Python 3.11 or newer."""
import logging
import sys

HELP = "/help  Show commands\n/clear Clear conversation\n/model Show model\n/status Show status\n/exit  Exit"


def run_cli(assistant, read=input, write=print) -> int:
    from avyra.providers.base import ProviderError
    write("AVYRA AI V1\nAVYRA: Hello! I'm AVYRA. How can I assist you?")
    try:
        while True:
            text = read("You: ").strip()
            if not text:
                continue
            if text == "/exit":
                break
            if text == "/help":
                write(HELP)
            elif text == "/clear":
                assistant.clear()
                write("Conversation cleared.")
            elif text == "/model":
                write(assistant.config.model)
            elif text == "/status":
                write(" | ".join(f"{k}: {v}" for k, v in assistant.status().items()))
            elif text.startswith("/"):
                write("Unknown command. Use /help.")
            else:
                try:
                    write("AVYRA: " + assistant.respond(text))
                except (ProviderError, ValueError) as exc:
                    write("Error: " + str(exc))
                except Exception:
                    write("Error: Unexpected request failure. Please try again.")
    except (KeyboardInterrupt, EOFError):
        pass
    finally:
        assistant.close()
    write("AVYRA: Goodbye!")
    return 0


def main() -> int:
    if sys.version_info < (3, 11):
        print("AVYRA requires Python 3.11 or newer.", file=sys.stderr)
        return 1
    from config import Config, ConfigurationError
    from avyra.core.assistant import Assistant
    try:
        config = Config.from_env()
    except ConfigurationError as exc:
        print(f"Setup error: {exc}", file=sys.stderr)
        return 1
    # Only our logger emits debug events; SDK/HTTP logging can contain private data.
    for name in ("openai", "httpx", "httpcore"):
        logging.getLogger(name).disabled = True
    logger = logging.getLogger("avyra")
    logger.setLevel(logging.DEBUG if config.debug else logging.INFO)
    logger.propagate = False
    if not logger.handlers:
        logger.addHandler(logging.StreamHandler())
    try:
        assistant = Assistant(config)
    except Exception:
        print("Setup error: Could not initialize OpenAI. Check configuration and dependencies.", file=sys.stderr)
        return 1
    return run_cli(assistant)


if __name__ == "__main__":
    raise SystemExit(main())
