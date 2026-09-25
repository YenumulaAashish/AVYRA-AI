# Architecture

`main.py` owns terminal input/output, commands, safe startup failure, logger setup and client cleanup. `config.py` validates dotenv/environment values and hides the API key from its representation. Python versions older than 3.11 are rejected before dependency imports in the entry point.

`Assistant` builds a SessionMemory, ConversationManager, Brain, provider and empty ToolRegistry. Its public interface is `respond(text)`, `clear()`, `status()` and `close()`. A provider may be injected for tests or future backends. Call `close()` when a frontend finishes.

`Brain` validates and trims text, requests conversation context, calls the provider with the dedicated AVYRA system instructions, and records a complete turn only after a valid response. It has no terminal dependencies. Errors propagate to the frontend; failed requests never alter history. Retrying a failed input therefore does not duplicate it. Intentionally repeated successful input remains a distinct turn.

`ConversationManager` owns turn semantics and request context policy. It commits user/assistant pairs together and reserves two slots before preparing new context, retaining complete turns. `SessionMemory` owns storage, chronological ordering, capacity, validation, clearing and defensive copies. These responsibilities are distinct: storage does not call an AI service or decide when a reply is successful. Its batch interface supports future alternative storage; persistence is not implemented.

`AIProvider` defines synchronous `generate(messages, instructions)` and resource cleanup. Providers must return complete nonempty text or a sanitized ProviderError. `OpenAIProvider` translates this contract to `client.responses.create`, using model, instructions, ordered input, store=False and a 2048-token output cap. It extracts `output_text` only for completed responses, sanitizes SDK failures and uses a 30-second timeout with no automatic retry. API account access is not verified by startup.

`ToolRegistry` registers immutable ToolDefinition metadata: unique name, description, explicit permissions and confirmation flag. There are no executable handlers or dispatch paths. A future executor must enforce access policy independently and require confirmation before sensitive actions; registration is not authorization.

Session state is local to each assistant instance. The implementation is synchronous and not thread-safe. Serialize calls per instance. Input has a character cap; history uses message counts, not token estimates. A model-specific context-limit rejection is reported safely without altering memory.

Tests replace providers or SDK clients with unittest.mock and prohibit socket connections. CLI tests use injected input/output functions. No live API success is asserted.


## V1.1 voice frontend

`main.py --mode voice` composes the same Assistant with Microphone, SpeechRecognizer and SpeechOutput; the default remains text mode. `voice/interaction.py` owns the explicit Enter-to-start loop and shared CLI commands. No second brain or provider exists. Voice imports are lazy so text mode does not require loading Whisper or audio devices.

`voice/microphone.py` opens a scoped SoundDevice InputStream only after start input, copies float32 mono blocks at 16 kHz, closes it on stop/interruption, rejects capture errors and caps capture at 120 seconds. Input remains in memory. `voice/recognition.py` lazily loads one WhisperModel per session and consumes its segment iterator locally with automatic language detection and VAD. Failed loads are retryable.

`voice/speech.py` synthesizes only the successful AI reply using Edge TTS, with a 60-second deadline, into a temporary MP3. SoundFile decodes it and SoundDevice plays it synchronously. Playback is stopped and temporary files are removed on normal completion, errors and KeyboardInterrupt. TTS failure does not roll back an already successful AI turn. STT failure or silence never calls the brain. No audio is sent to OpenAI.

There is no background microphone listener or shell execution. Microsoft receives reply text for speech synthesis; OpenAI receives text conversation context. Model files may be downloaded on first transcription. Existing model system instructions and provider code remain unchanged.
