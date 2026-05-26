class LinguistError(Exception):
    """Base exception for all Linguist application errors."""

class TranscriptionError(LinguistError):
    """Whisper transcription failures."""

class SynthesisError(LinguistError):
    """TTS model or speech generation failures."""

class ModelLoadError(LinguistError):
    """Model initialization or loading failures."""
