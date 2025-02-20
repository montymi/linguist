from .packages.tts.controller import Controller as tts
import shutil
import subprocess
import os
import sys
from .microphone import Microphone
from datetime import datetime
import whisper
import warnings

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
        except Exception as e:
            print(f"Warning: Could not set archive permissions: {e}")
        self.debug = debug
        self.tts = tts(debug=debug)
        self.tts.load()
        self.mic = Microphone()
        self.whisper_model = whisper.load_model(self.whisper_model)

    def set_voice(self, voice: str):
        self.tts.handle_set_voice(voice)

    def stamp(self):
        return datetime.now().strftime("%Y-%m-%d@%H%M%S")
    
    def samples(self):
        self.mic.samples(self.archive)

    def generate(self, words: str, tag=None):
        """Generate speech from text with optional language and speaker embedding."""
        if not tag:
            tag = self.default_output
        if not tag.endswith(".wav"):
            output_file = tag + ".wav"
        else:
            output_file = tag
        try:
            self.tts.handle_generate_speech(words, output_file)
            print(f"📂 Speech saved to: {tag} ✅\n")
        except Exception as e:
            print(f"Error during recording: {e}")
    
    def speak(self, text: str, tag: str=None, voice: str=None):
        """Convert text to speech and play it."""
        if voice:
            self.set_voice(voice)
        try:
            if not tag:
                tag = input("Name the recording (ENTER for datetime): ") or self.stamp()
            if not tag.endswith(".wav"):
                path = os.path.join(self.archive, tag + ".wav")
            else:
                path = os.path.join(self.archive, tag)
            self.generate(text, path)
        except KeyboardInterrupt:
            print("Speaker interrupted. Exiting...")

    def listen(self, tag: str=None) -> str:
        """Record audio for a given duration."""
        try:
            if not tag:
                tag = input("Name the recording (ENTER for datetime): ") or self.stamp()
            
            # Ensure proper Windows path handling
            name = os.path.join(self.archive, f"{tag}.wav" if not tag.endswith(".wav") else tag)
            name = os.path.normpath(name)  # Normalize path separators
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(name), exist_ok=True)
            
            self.mic.record(output_file=name)
            return name
        except KeyboardInterrupt:
            print("Recording interrupted. Exiting...")
            return ""
        except Exception as e:
            print(f"Error during recording: {e}")
            return ""

    def transcribe(self, file: str, show_text: bool, tag: str=None) -> str:
        """Transcribe recorded audio to text."""
        try:
            file_path = os.path.abspath(file)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Audio file not found: {file_path}")
                
            print(f"📝 Transcribing audio from {file_path}... Press Ctrl+C to stop. 🔊")
            result = self.whisper_model.transcribe(file_path)
            text = result["text"]
            
            if text:
                print(f"\n📜 Transcription successful ✅")
                if show_text:
                    print(f"\n❝{text} ❞\n")
                    
            if tag:
                if not tag.endswith(".txt"):
                    tag += ".txt"
                output_path = os.path.join(self.archive, tag)
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(text)
                print(f"📂 Transcription saved to: {output_path} ✅\n")
                
            return text
            
        except FileNotFoundError as e:
            print(f"File error: {e}")
            return ""
        except KeyboardInterrupt:
            print("Transcription interrupted. Exiting...")
            return ""
        except Exception as e:
            print(f"Error during transcription: {e}")
            return ""
    

def main():
    linguist = Linguist()

    while True:
        # Step 0: Record User for Voice Cloning
        try:
            selection = input("Record audio clip for voice cloning? (y/N): ") or 'N'
            if selection.lower() in ['y', 'yes']:
                name = input("Name the audio clip (ENTER for datetime): ") or datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                linguist.mic.record(file=name)
        except Exception as e:
            print(f"Error during recording: {e}")

        # Step 1: Set Language
        try:
            print("Available Languages:")
            languages = linguist.list_languages()
            if languages:
                [print(lang) for lang in languages]
                selected_language = input("Select a language (ENTER for Default): ")
                if selected_language in languages:
                    linguist.set_language(selected_language)
                else:
                    print("Invalid language selected. Defaulting to first available language.")
                    linguist.set_language(languages[0])
            else:
                print("No languages available for this model.")
        except Exception as e:
            print(f"Error during language selection: {e}")

        # Step 2: Set Speaker (Optional)
        try:
            print("Available Speakers:")
            speakers = [speaker for speaker in linguist.list_speakers() if speaker]
            if speakers:
                [print(speaker) for speaker in speakers]
                selected_speaker = input(f"Select a speaker (ENTER for Default '{speakers[0]}'): ") or speakers[0]
                linguist.set_speaker(selected_speaker)
            else:
                print("No speakers available for this model. Defaulting to the first available speaker.")
                linguist.set_speaker(speakers[0] if speakers else None)
        except Exception as e:
            print(f"Error during speaker selection: {e}")

        # Step 3: Set Speaker Embedding (Optional)
        try:
            linguist.mic.samples()
            ref_audio = input("Provide path to reference audio for voice cloning (ENTER to skip): ")
            if ref_audio:
                linguist.set_speaker_embedding(ref_audio)
        except Exception as e:
            print(f"Error during speaker embedding: {e}")

        # Step 4: Record Speech
        try:
            text = input("Enter text to convert to speech: ")
            linguist.record(text)
        except Exception as e:
            print(f"Error during speech recording: {e}")

        # Step 5: Play the Audio
        try:
            linguist.say()
        except Exception as e:
            print(f"Error during audio playback: {e}")

        # Ask if the user wants to repeat the process
        again = input("\nWould you like to do another? (y/N): ").lower()
        if again.lower() not in ['y', 'yes']:
            print("Exiting program.")
            break


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        selection = input("\nAborted session. Would you like to restart? (y/N): ")
        if selection.lower() not in ['y', 'yes']:
            print("Exiting program.")
            exit()   
        print("Restarting Linguist and Microphone")
        main()