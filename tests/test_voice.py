from types import SimpleNamespace
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path
import numpy as np
import pytest
from config import Config, ConfigurationError
from avyra.core.assistant import Assistant
from avyra.voice.microphone import Microphone
from avyra.voice.recognition import SpeechRecognizer
from avyra.voice.speech import SpeechOutput
from avyra.voice.interaction import run_voice
from avyra.voice.errors import VoiceError
from avyra.providers.base import ProviderError


@pytest.mark.parametrize("changes", [{"stt_model":""}, {"stt_device":"invalid"}, {"stt_compute_type":"invalid"}, {"tts_voice":""}])
def test_voice_config_invalid(changes):
    with pytest.raises(ConfigurationError):
        Config("test-key", **changes)


def test_voice_config_environment(tmp_path):
    values = {"OPENAI_API_KEY":"test-key", "AVYRA_STT_MODEL":"medium", "AVYRA_STT_DEVICE":"auto",
              "AVYRA_STT_COMPUTE_TYPE":"float32", "AVYRA_TTS_VOICE":"en-GB-SoniaNeural"}
    with patch.dict("os.environ", values, clear=True):
        config = Config.from_env(tmp_path / "missing")
    assert (config.stt_model, config.stt_device, config.stt_compute_type, config.tts_voice) == ("medium", "auto", "float32", "en-GB-SoniaNeural")


def test_microphone_format_copy_and_close():
    block = np.ones((160,1),dtype=np.float32)
    with patch("sounddevice.InputStream") as stream:
        def stop(_):
            stream.call_args.kwargs["callback"](block,160,None,False)
            block[:] = 0
        result = Microphone().record(stop, Mock())
        assert result.shape == (160,)
        assert np.all(result == 1)
        assert stream.call_args.kwargs["samplerate"] == 16000
        assert stream.call_args.kwargs["channels"] == 1
        stream.return_value.__exit__.assert_called_once()


@pytest.mark.parametrize("problem", ["permission", "empty", "overflow", "interrupt", "eof"])
def test_microphone_errors_and_cleanup(problem):
    with patch("sounddevice.InputStream") as stream:
        if problem == "permission":
            stream.side_effect = RuntimeError("private device information")
        def read(_):
            if problem == "interrupt":
                raise KeyboardInterrupt
            if problem == "eof":
                raise EOFError
            if problem == "overflow":
                stream.call_args.kwargs["callback"](np.ones((10,1)),10,None,True)
        expected = KeyboardInterrupt if problem == "interrupt" else EOFError if problem == "eof" else VoiceError
        with pytest.raises(expected) as error:
            Microphone().record(read, Mock())
        assert "private device" not in str(error.value)
        if problem != "permission":
            stream.return_value.__exit__.assert_called_once()


def test_microphone_duration_cap():
    import sounddevice as sd
    mic = Microphone()
    mic.MAX_SECONDS = 1
    with patch("sounddevice.InputStream") as stream:
        def read(_):
            with pytest.raises(sd.CallbackStop):
                stream.call_args.kwargs["callback"](np.ones((17000,1)),17000,None,False)
        audio = mic.record(read,Mock())
    assert len(audio) == 16000


def test_model_reused_multilingual(config):
    with patch("faster_whisper.WhisperModel") as factory:
        factory.return_value.transcribe.side_effect = [
            (iter([SimpleNamespace(text=" Hello "),SimpleNamespace(text="world")]),None),
            (iter([SimpleNamespace(text="Hola")]),None)]
        recognizer = SpeechRecognizer(config)
        audio = np.ones(16000,dtype=np.float32)
        assert recognizer.transcribe(audio) == "Hello world"
        assert recognizer.transcribe(audio) == "Hola"
        factory.assert_called_once_with("small", device="cpu", compute_type="int8")
        assert factory.return_value.transcribe.call_args.kwargs["language"] is None
        assert factory.return_value.transcribe.call_args.kwargs["vad_filter"] is True


def test_lazy_segment_failure(config):
    def broken():
        yield SimpleNamespace(text="partial")
        raise RuntimeError("private detail")
    with patch("faster_whisper.WhisperModel") as factory:
        factory.return_value.transcribe.return_value = (broken(),None)
        with pytest.raises(VoiceError,match="Speech recognition failed"):
            SpeechRecognizer(config).transcribe(np.ones(10))


def test_model_loading_retry(config):
    with patch("faster_whisper.WhisperModel") as factory:
        factory.side_effect = [RuntimeError("offline"),Mock()]
        recognizer = SpeechRecognizer(config)
        with pytest.raises(VoiceError):
            recognizer.transcribe(np.ones(10))
        assert recognizer._model is None


@pytest.mark.parametrize("failure", [None,"network","decode","playback","interrupt"])
def test_tts_save_play_and_cleanup(failure):
    paths = []
    async def save(path):
        paths.append(Path(path))
        Path(path).write_bytes(b"mock mp3")
        if failure == "network":
            raise RuntimeError("private network detail")
    with patch("edge_tts.Communicate") as edge, patch("soundfile.read") as decode, patch("sounddevice.play") as play, patch("sounddevice.wait") as wait, patch("sounddevice.stop") as stop:
        edge.return_value.save = AsyncMock(side_effect=save)
        decode.return_value = (np.ones(100),24000)
        wait.return_value = None
        if failure == "decode":
            decode.side_effect = RuntimeError("decode")
        if failure == "playback":
            play.side_effect = RuntimeError("speaker")
        if failure == "interrupt":
            wait.side_effect = KeyboardInterrupt
        speech = SpeechOutput("en-US-AriaNeural")
        if failure:
            with pytest.raises(KeyboardInterrupt if failure == "interrupt" else VoiceError):
                speech.speak("Hello")
        else:
            speech.speak("Hello")
            edge.assert_called_once_with("Hello","en-US-AriaNeural")
            play.assert_called_once()
        assert paths and not paths[0].exists() and not paths[0].parent.exists()
        if failure not in ("network","decode"):
            stop.assert_called_once()


def test_voice_existing_brain_memory_and_tts_failure(config,provider):
    assistant = Assistant(config,provider)
    mic,recognizer,speech = Mock(),Mock(),Mock()
    recognizer.transcribe.side_effect = ["Hello", "Follow up"]
    speech.speak.side_effect = [VoiceError("Speech unavailable"),None]
    output = []
    read = Mock(side_effect=["", "", "/exit"])
    assert run_voice(assistant,mic,recognizer,speech,read,output.append) == 0
    assert assistant.status()["messages"] == 4
    context = provider.generate.call_args.args[0]
    assert [m["content"] for m in context] == ["Hello","A useful answer","Follow up"]
    assert "Error: Speech unavailable" in output
    provider.close.assert_called_once()


@pytest.mark.parametrize("failure", ["silence", "microphone", "stt", "provider"])
def test_voice_failed_input_not_saved(config,provider,failure):
    assistant = Assistant(config,provider)
    mic,recognizer,speech = Mock(),Mock(),Mock()
    recognizer.transcribe.return_value = "" if failure == "silence" else "Hello"
    if failure == "microphone":
        mic.record.side_effect = VoiceError("Microphone unavailable")
    if failure == "stt":
        recognizer.transcribe.side_effect = VoiceError("STT unavailable")
    if failure == "provider":
        provider.generate.side_effect = ProviderError("AI unavailable")
    run_voice(assistant,mic,recognizer,speech,Mock(side_effect=["","/exit"]),Mock())
    assert assistant.status()["messages"] == 0
    speech.speak.assert_not_called()
    if failure != "provider":
        provider.generate.assert_not_called()


def test_voice_commands_never_open_microphone(config,provider):
    mic, recognizer, speech = Mock(), Mock(), Mock()
    run_voice(Assistant(config,provider),mic,recognizer,speech,
              Mock(side_effect=["/help","/model","/status","/clear","/unknown","hello","/exit"]),Mock())
    mic.record.assert_not_called()
    provider.generate.assert_not_called()


@pytest.mark.parametrize("interrupt",[KeyboardInterrupt,EOFError])
def test_voice_interrupt_closes_assistant(config,provider,interrupt):
    mic = Mock()
    mic.record.side_effect = interrupt
    run_voice(Assistant(config,provider),mic,Mock(),Mock(),Mock(return_value=""),Mock())
    provider.close.assert_called_once()


@pytest.mark.parametrize("mode",["text","voice"])
def test_launch_modes(config,mode):
    from main import main
    with patch("config.Config.from_env",return_value=config), patch("avyra.core.assistant.Assistant") as assistant, patch("main.run_cli",return_value=0) as text, patch("avyra.voice.interaction.run_voice",return_value=0) as voice:
        assert main(["--mode",mode]) == 0
        target = text if mode == "text" else voice
        assert target.call_args.args[0] is assistant.return_value
        (voice if mode == "text" else text).assert_not_called()
