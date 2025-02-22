from abc import ABC, abstractmethod
import inspect
import sys
import os
from dataclasses import fields
from typing import Optional, Dict
from dataclasses import dataclass
from wave import Error as WaveError

from .models.linguist import Linguist
from .models.microphone import AudioInfo
from .views.abstract import AbstractView

@dataclass
class CommandSession:       
    """Manages the command session state"""
    running: bool = False
    commands: Dict = None
    linguist: Optional[Linguist] = None
    view: Optional[AbstractView] = None

    def __bool__(self):
        return self.running

# Add at module level
_session = CommandSession()

def get_commands(view: AbstractView):
    """Dynamically get all command classes defined in this module"""
    if not isinstance(view, AbstractView):
        raise TypeError("View must be an instance of AbstractView")
    
    return {
        cls(view).name: cls(view)
        for _, cls in inspect.getmembers(sys.modules[__name__], inspect.isclass)
        if issubclass(cls, command) and cls != command
    }

class command(ABC):
    def __init__(self, view: AbstractView):
        self.view = view

    @abstractmethod
    def execute(self, args, linguist: Linguist):
        """Execute a command using given args and a Linguist instance."""
        pass

    @property
    def name(self):
        return self.__class__.__name__


class list(command):
    def __init__(self, view: AbstractView):
        super().__init__(view)

    def execute(self, args, linguist):
        # print(f"Dumping contents of '{linguist.archive}'")
        # print("=" * 72)
        # header_format = "{:<30} {:>10} {:>10} {:>8} {:>8}"
        # print(header_format.format("SAMPLES", "SIZE", "DURATION", "RATE", "BITS"))
        # print("=" * 72)        
        headers = [field.name.upper() for field in fields(AudioInfo)]
        self.view.samples_header(headers)
        try:
            audio_meta = self.linguist.samples()
            self.view.samples_content(audio_meta)
        except FileNotFoundError as e:
            self.view.throw(f"Archive directory not found: {e}")
        except WaveError as e:
            self.view.throw(f"Invalid or corrupted WAV file: {e}")
        except PermissionError as e:
            self.view.throw(f"Permission denied accessing audio files: {e}")
        except Exception as e:
            self.view.throw(f"Unexpected error reading audio files: {e}")
        # for meta in audio_meta:
        #     # Format size
        #     size_mb = meta.bytes / (1024 * 1024)
        #     size_str = f"{size_mb:.2f} MB"

        #     # Format duration
        #     if meta.duration < 60:
        #         duration_label = f"{meta.duration:.2f}s"
        #     elif meta.duration < 3600:
        #         duration_label = f"{(meta.duration / 60):.2f}min"
        #     else:
        #         duration_label = f"{(meta.duration / 3600):.2f}h"

        #     # Print formatted row
        #     formatted = header_format.format(
        #         os.path.basename(meta.file)[:30],  # Truncate long filenames
        #         size_str,
        #         duration_label,
        #         meta.rate,
        #         meta.width
        #     )

    @property
    def name(self):
        return "list"


class speak(command):
    default_text = "Hello, World! You seem to have forgotten to provide text to speak."
    
    def __init__(self, view: AbstractView):
        super().__init__(view)

    def execute(self, args, linguist):
        if not args.tag:
            args.tag = self.view.get_tag() or linguist.stamp()
        if args.speaker:
            linguist.set_voice(args.speaker)
        try:
            self.view.synthesizing()
            artifact = linguist.speak(args.text or self.default_text, tag=args.tag)
            self.view.success(self.name, artifact)
        except KeyboardInterrupt:
            self.view.interrupt(self.name)
        except Exception as e:
            self.view.throw(self.name, e)

    @property
    def name(self):
        return "speak"

from threading import Event, Thread

class listen(command):
    def __init__(self, view: AbstractView):
        super().__init__(view)
        self.recording_thread = None
        self.stop_event = Event()

    def execute(self, args, linguist: Linguist):
        try:
            if not args.tag:
                args.tag = self.view.get_tag() or linguist.stamp()
            
            # Ensure proper Windows path handling
            name = os.path.join(linguist.archive, f"{args.tag}.wav" if not args.tag.endswith(".wav") else args.tag)
            name = os.path.normpath(name)  # Normalize path separators
            os.makedirs(os.path.dirname(name), exist_ok=True) # Ensure directory exists

            self.start_recording(linguist, name)
            self.view.recording()

            try:
                while True:
                    pass  # Keep recording until interrupted
            except KeyboardInterrupt:
                self.stop_recording()
                self.view.success(self.name, name)
                text, artifact = linguist.transcribe(name)
                if text and args.print:
                    self.view.transcription(text)
                return text
        except KeyboardInterrupt:
            self.view.interrupt(self.name)
            return ""
        except Exception as e:
            self.view.throw(self.name, e)
            return ""
        except Exception as e:
            self.view.throw(self.name, e)
            return ""

    def start_recording(self, linguist: Linguist, name: str):
        if self.recording_thread and self.recording_thread.is_alive():
            return
        self.stop_event.clear()
        self.recording_thread = Thread(target=linguist.mic.record, args=(name, self.stop_event))
        self.recording_thread.start()
    
    def stop_recording(self):
        if self.recording_thread and self.recording_thread.is_alive():
            self.stop_event.set()
            self.recording_thread.join()

    @property
    def name(self):
        return "listen"


class transcribe(command):
    def __init__(self, view: AbstractView):
        super().__init__(view)

    def execute(self, args, linguist):
        try:
            file_path = os.path.abspath(args.path)
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Audio file not found at {file_path}")
                
            self.view.transcribing()
            text, artifact = linguist.transcribe(args.path, tag=args.tag)
            if text:
                if args.print:
                    self.view.transcription(text)

            if args.tag and artifact:
                self.view.success(self.name, artifact)


        except FileNotFoundError as e:
            self.view.throw(self.name, e)
        except KeyboardInterrupt:
            self.view.interrupt(self.name)
        except Exception as e:
            self.view.throw(self.name, e)
    
    @property
    def name(self):
        return "transcribe"
    
# class start(command):
#     def __init__(self, view: AbstractView):
#         super().__init__(view)
             
#     def execute(self, args, linguist):
#         global _session
        
#         if _session.running:
#             print("Session already running. Stopping current session...")
#             _session.running = False
#             return

#         try:
#             _session.running = True
#             _session.linguist = linguist
#             _session.commands = self._get_commands()
            
#             print("\nEnter commands (type 'exit' to quit, 'help' for available commands)")
#             while _session.running:
#                 try:
#                     command_input = input("\n> ").strip()
#                     if not command_input:
#                         continue
                        
#                     if command_input.lower() == 'exit':
#                         break
                        
#                     if command_input.lower() == 'help':
#                         self._show_help()
#                         continue
                        
#                     self._execute_command(command_input)
                        
#                 except KeyboardInterrupt:
#                     print("\nCommand interrupted.")
#                     continue
                    
#         except KeyboardInterrupt:
#             print("\nExiting session...")
#         finally:
#             _session.running = False
#             _session.commands = None

#     def _execute_command(self, command_input: str):
#         """Execute a single command with its arguments"""
#         parts = command_input.split()
#         command_name = parts[0].lower()
        
#         command = _session.commands.get(command_name)
#         if not command:
#             print(f"Unknown command: {command_name}")
#             self._show_help()
#             return
            
#         try:
#             args = type('Args', (), {
#                 'text': ' '.join(parts[1:]) if len(parts) > 1 else None,
#                 'tag': None,
#                 'print': True,
#                 'speaker': None,
#                 'path': None
#             })
#             command.execute(args, _session.linguist)
#         except Exception as e:
#             print(f"Error executing command: {e}")

#     def _show_help(self):
#         """Show available commands and their descriptions"""
#         print("\nAvailable commands:")
#         for name, cmd in _session.commands.items():
#             doc = cmd.__class__.__doc__ or "No description available"
#             print(f"  {name}: {doc}")

#     def _get_commands(self) -> Dict:
#         """Get all available commands except start"""
#         commands = get_commands(self.view)
#         # Remove start command to prevent recursion
#         commands.pop(self.name, None)
#         return commands

#     @property
#     def name(self):
#         return "start"