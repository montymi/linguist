import os
import whisper
import warnings
from datetime import datetime

from ..packages.tts.controller import Controller as tts
from .microphone import Microphone, AudioInfo

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead") # Ignore FP16 warning because it defaults to FP32

class Linguist:
    def __init__(
            self, 
            whisper_model="base",
            output_file="output.wav",
            archive="archive"
        ):
        self.default_output = output_file
        self.archive = archive
        self.whisper_model = whisper_model

    def init(self, debug: bool=False):
        if not os.path.exists(self.archive):
            os.makedirs(self.archive)
        # Set permissions on Windows
        try:
            os.chmod(self.archive, 0o777)
        except PermissionError as e:
            raise (f"Warning: Could not set archive permissions: {e}")
        self.debug = debug
        self.tts = tts(debug=debug)
        self.tts.load()
        self.mic: Microphone = Microphone()
        self.whisper_model = whisper.load_model(self.whisper_model)

    def set_voice(self, voice: str):
        self.tts.handle_set_voice(voice)

    def stamp(self):
        return datetime.now().strftime("%Y-%m-%d@%H%M%S")
    
    def samples(self) -> AudioInfo:
        """List all recorded audio samples with formatted output."""
        return self.mic.samples(self.archive)

    def generate(self, words: str, tag=None):
        """Generate speech from text with optional language and speaker embedding."""
        if not tag:
            tag = self.default_output
        if not tag.endswith(".wav"):
            output_file = tag + ".wav"
        else:
            output_file = tag
        self.tts.handle_generate_speech(words, output_file)
    
    def speak(self, text: str, tag: str=None, voice: str=None):
        """Convert text to speech and play it."""
        if voice:
            self.set_voice(voice)
        if not tag.endswith(".wav"):
            path = os.path.join(self.archive, tag + ".wav")
        else:
            path = os.path.join(self.archive, tag)
        self.generate(text, path)

    def transcribe(self, file: str, tag: str=None) -> str:
        """Transcribe recorded audio to text."""
        result = self.whisper_model.transcribe(file)
        text = result["text"]
                    
        if tag:
            if not tag.endswith(".txt"):
                tag += ".txt"
            output_path = os.path.join(self.archive, tag)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text)
            tag = output_path

        return text, tag


# if __name__ == '__main__':
#     try:
#         main()
#     except KeyboardInterrupt:
#         selection = input("\nAborted session. Would you like to restart? (y/N): ")
#         if selection.lower() not in ['y', 'yes']:
#             print("Exiting program.")
#             exit()   
#         print("Restarting Linguist and Microphone")
#         main()