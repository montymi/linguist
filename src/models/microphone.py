import os
import wave
import pyaudio
from enum import Enum
from threading import Event
from collections import namedtuple

class AudioInfo(Enum):
    FILE = 'file'
    SIZE_BYTES = 'size_bytes'
    DURATION = 'duration'
    RATE = 'rate'
    SAMPLE_WIDTH = 'sample_width'


class Microphone:
    def __init__(self, device_index=None):
        self.device_index = device_index  # Optional: Use a specific microphone device
        self.sample_rate = 16000
        self.chunk_size = 1024  # Buffer size for audio chunks
        self.format = pyaudio.paInt32  # Audio format
        self.channels = 1  # Mono audio
        self.p = pyaudio.PyAudio()
        self.recording_thread = None

    def record(self, output_file: str, stop_event: Event):
        """Start recording audio to a file until the stop_event is set."""
        """Records audio until the stop_event is set."""
        stream = self.p.open(format=self.format,
                             channels=self.channels,
                             rate=self.sample_rate,
                             input=True,
                             frames_per_buffer=self.chunk_size,
                             input_device_index=self.device_index)

        frames = []

        while not stop_event.is_set():
            data = stream.read(self.chunk_size)
            frames.append(data)

        stream.stop_stream()
        stream.close()

        with wave.open(output_file, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.p.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))

    def samples(self, output_file: str):
        """List all recorded audio samples in the archive directory, including additional audio quality info."""
        if not os.path.isdir(output_file):
            raise FileNotFoundError(f"'{output_file}' does not exist.")

        AudioMeta = namedtuple("AudioMeta", ["file", "bytes", "duration", "rate", "width"])
        audio_files = []

        try:
            for file in sorted(os.listdir(output_file)):
                if not file.lower().endswith(".wav"):
                    continue
                    
                file_path = os.path.join(output_file, file)
                size_bytes = os.path.getsize(file_path)
                
                with wave.open(file_path, 'rb') as wf:
                    frames = wf.getnframes()
                    rate = wf.getframerate()
                    sample_width = wf.getsampwidth() * 8
                    duration = frames / float(rate)
                    
                audio_files.append(AudioMeta(
                    file=file_path,
                    bytes=size_bytes,
                    duration=duration,
                    rate=rate,
                    width=sample_width
                ))
                
            return audio_files
            
        except FileNotFoundError or wave.Error or PermissionError as e:
            raise (f"Error reading audio files: {e}")


    def __del__(self):
        """Ensure proper cleanup of resources."""
        self.p.terminate()
