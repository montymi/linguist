import os
import wave
import pyaudio
import threading

class Microphone:
    def __init__(self, device_index=None):
        self.device_index = device_index  # Optional: Use a specific microphone device
        self.sample_rate = 16000
        self.chunk_size = 1024  # Buffer size for audio chunks
        self.format = pyaudio.paInt32  # Audio format
        self.channels = 1  # Mono audio
        self.p = pyaudio.PyAudio()

    def record(self, output_file: str):
        """Record audio from the microphone until user input is detected."""
        print("🎤 Recording in progress... Press Enter to stop. 🔴")
        stream = self.p.open(format=self.format,
                             channels=self.channels,
                             rate=self.sample_rate,
                             input=True,
                             frames_per_buffer=self.chunk_size,
                             input_device_index=self.device_index)

        frames = []

        def stop_recording():
            input()
            nonlocal recording
            recording = False

        recording = True
        stop_thread = threading.Thread(target=stop_recording)
        stop_thread.start()

        while recording:
            data = stream.read(self.chunk_size)
            frames.append(data)

        stop_thread.join()

        stream.stop_stream()
        stream.close()

        # Save the recorded audio to the specified file
        with wave.open(output_file, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.p.get_sample_size(self.format))
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(frames))

    def samples(self, output_file: str):
        """List all recorded audio samples in the archive directory, including additional audio quality info."""
        if not os.path.isdir(output_file):
            print("No directory found.")
            return

        print(f"Dumping contents of '{output_file}'")
        print("=" * 72)
        header_format = "{:<30} {:>10} {:>10} {:>8} {:>8}"
        print(header_format.format("SAMPLES", "SIZE", "DURATION", "RATE", "BITS"))
        print("=" * 72)

        for file in sorted(os.listdir(output_file)):
            if not file.lower().endswith(".wav"):
                continue
            file_path = os.path.join(output_file, file)
            size_bytes = os.path.getsize(file_path)
            size_mb = size_bytes / (1024 * 1024)
            size_str = f"{size_mb:.2f} MB"
            with wave.open(file_path, 'rb') as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                sample_width = wf.getsampwidth() * 8
                duration = frames / float(rate)

            if duration < 60:
                duration_label = f"{duration:.2f}s"
            elif duration < 3600:
                duration_label = f"{(duration / 60):.2f}min"
            else:
                duration_label = f"{(duration / 3600):.2f}h"

            print(f"{file:<30} {size_str:>10} {duration_label:>10} {rate:>8} {sample_width:>8}")
        print("=" * 72)


    def __del__(self):
        """Ensure proper cleanup of resources."""
        self.p.terminate()
