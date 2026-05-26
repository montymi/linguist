import os
from datetime import datetime

import pyttsx3
import soundfile as sf
from faster_whisper import WhisperModel

from .microphone import Microphone, AudioMeta
from ..errors import ModelLoadError, SynthesisError, TranscriptionError


class Linguist:
    def __init__(
            self,
            whisper_model="base",
            output_file="output.wav",
            archive="archive"
        ):
        self.default_output = output_file
        self.archive = archive
        self.whisper_model_size = whisper_model

    def init(self, debug: bool=False):
        if not os.path.exists(self.archive):
            os.makedirs(self.archive)
        try:
            os.chmod(self.archive, 0o755)
        except PermissionError as e:
            raise ModelLoadError(f"Could not set archive permissions: {e}") from e
        self.debug = debug
        try:
            self.tts_engine = pyttsx3.init()
        except (RuntimeError, OSError) as e:
            raise ModelLoadError(f"Failed to initialize TTS engine: {e}") from e
        self.set_voice("Samantha")
        self.tts_engine.setProperty('rate', 230)
        self.mic: Microphone = Microphone()
        try:
            self.stt_model = WhisperModel(self.whisper_model_size, device="cpu", compute_type="int8")
        except (RuntimeError, OSError, ValueError) as e:
            raise ModelLoadError(f"Failed to load Whisper model: {e}") from e

    def set_voice(self, voice: str):
        voices = self.tts_engine.getProperty('voices')
        for v in voices:
            if voice.lower() in v.id.lower() or voice.lower() in v.name.lower():
                self.tts_engine.setProperty('voice', v.id)
                return
        if voices:
            self.tts_engine.setProperty('voice', voices[0].id)

    def stamp(self):
        return datetime.now().strftime("%Y-%m-%d@%H%M%S")

    def samples(self) -> list:
        return self.mic.samples(self.archive)

    def speak(self, text: str, tag: str=None, voice: str=None):
        """Convert text to speech and save to file."""
        if voice:
            self.set_voice(voice)
        if not tag:
            tag = self.default_output
        if not tag.endswith(".wav"):
            path = os.path.join(self.archive, tag + ".wav")
        else:
            path = os.path.join(self.archive, tag)
        tmp_path = path + ".aiff"
        try:
            self.tts_engine.save_to_file(text, tmp_path)
            self.tts_engine.runAndWait()
            self._aiff_to_wav(tmp_path, path)
        except (RuntimeError, OSError) as e:
            raise SynthesisError(f"Speech synthesis failed: {e}") from e
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        return path

    @staticmethod
    def _aiff_to_wav(aiff_path: str, wav_path: str):
        data, samplerate = sf.read(aiff_path)
        sf.write(wav_path, data, samplerate)

    def transcribe(self, file: str, tag: str=None) -> tuple[str, str]:
        """Transcribe recorded audio to text."""
        try:
            segments, _ = self.stt_model.transcribe(file)
            text = " ".join(seg.text for seg in segments).strip()
        except (RuntimeError, OSError, ValueError) as e:
            raise TranscriptionError(f"Transcription failed for {file}: {e}") from e

        if tag:
            if not tag.endswith(".txt"):
                tag += ".txt"
            output_path = os.path.join(self.archive, tag)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            tag = output_path

        return text, tag

    def close(self):
        if hasattr(self, 'mic'):
            self.mic.close()
        if hasattr(self, 'tts_engine'):
            self.tts_engine.stop()
        self.stt_model = None
