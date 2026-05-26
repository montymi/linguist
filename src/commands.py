from abc import ABC, abstractmethod
import os
from typing import Dict
from wave import Error as WaveError

from .models.linguist import Linguist
from .models.microphone import AudioMeta
from .views.abstract import AbstractView
from .errors import SynthesisError, TranscriptionError
from threading import Event, Thread


def get_commands(view: AbstractView) -> Dict[str, "command"]:
    if not isinstance(view, AbstractView):
        raise TypeError("View must be an instance of AbstractView")
    return {
        "list": list_samples(view),
        "speak": speak(view),
        "listen": listen(view),
        "transcribe": transcribe(view),
    }


class command(ABC):
    def __init__(self, view: AbstractView):
        self.view = view

    @abstractmethod
    def execute(self, args, linguist: Linguist):
        pass

    @property
    def name(self):
        return self.__class__.__name__


class list_samples(command):
    def __init__(self, view: AbstractView):
        super().__init__(view)

    def execute(self, args, linguist):
        headers = list(AudioMeta._fields)
        self.view.samples_header(headers)
        try:
            audio_meta = linguist.samples()
            self.view.samples_content(audio_meta)
        except (FileNotFoundError, WaveError, PermissionError, OSError) as e:
            self.view.throw(self.name, e)

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
        except (SynthesisError, OSError) as e:
            self.view.throw(self.name, e)

    @property
    def name(self):
        return "speak"


class listen(command):
    JOIN_TIMEOUT = 5

    def __init__(self, view: AbstractView):
        super().__init__(view)
        self.recording_thread = None
        self.stop_event = Event()

    def execute(self, args, linguist: Linguist):
        try:
            if not args.tag:
                args.tag = self.view.get_tag() or linguist.stamp()

            name = os.path.join(linguist.archive, f"{args.tag}.wav" if not args.tag.endswith(".wav") else args.tag)
            name = os.path.normpath(name)
            os.makedirs(os.path.dirname(name), exist_ok=True)

            duration = getattr(args, 'duration', None)
            self.start_recording(linguist, name)
            self.view.recording()

            try:
                if duration:
                    self.stop_event.wait(timeout=duration)
                    self.stop_recording()
                else:
                    self.stop_event.wait()
            except KeyboardInterrupt:
                pass
            finally:
                self.stop_recording()

            self.view.success(self.name, name)
            text, artifact = linguist.transcribe(name)
            if text and args.print:
                self.view.transcription(text)
            return text
        except KeyboardInterrupt:
            self.view.interrupt(self.name)
            return ""
        except (FileNotFoundError, PermissionError, WaveError) as e:
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
            self.recording_thread.join(timeout=self.JOIN_TIMEOUT)
            if self.recording_thread.is_alive():
                self.view.warn("Recording thread did not stop cleanly")

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
        except (TranscriptionError, OSError) as e:
            self.view.throw(self.name, e)

    @property
    def name(self):
        return "transcribe"
