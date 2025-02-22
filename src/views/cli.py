from .abstract import AbstractView
from typing import List, Any
import os

class CLIView(AbstractView):
    def samples_header(self, headers: List[str]) -> None:
        print("=" * 72)
        header_format = "{:<30} {:>10} {:>10} {:>8} {:>8}"
        print(header_format.format(*headers))
        print("=" * 72)
    
    def samples_content(self, audio_meta: List[Any]) -> None:
        header_format = "{:<30} {:>10} {:>10} {:>8} {:>8}"
        for meta in audio_meta:
            size_mb = meta.bytes / (1024 * 1024)
            size_str = f"{size_mb:.2f} MB"
            
            if meta.duration < 60:
                duration_label = f"{meta.duration:.2f}s"
            elif meta.duration < 3600:
                duration_label = f"{(meta.duration / 60):.2f}min"
            else:
                duration_label = f"{(meta.duration / 3600):.2f}h"
                
            print(header_format.format(
                os.path.basename(meta.file)[:30],
                size_str,
                duration_label,
                meta.rate,
                meta.width
            ))
        print("=" * 72)
    
    def synthesizing(self) -> None:
        print("🎵 Synthesizing speech... Press Ctrl+C to stop. 🔊")
    
    def recording(self) -> None:
        print("🎤 Recording in progress... Press Ctrl+C to stop. 🔴")
    
    def transcribing(self) -> None:
        print("📝 Transcribing audio... Press Ctrl+C to stop. ✏️")
    
    def transcription(self, text: str) -> None:
        print(f"\n❝{text}❞\n")
    
    def success(self, command: str, artifact: str) -> None:
        print(f"✅ Service {command.title()} complete. Output saved to: {artifact}")
    
    def interrupt(self, command: str) -> None:
        print(f"\n⚠️ Service {command.title()} interrupted.")
    
    def throw(self, command: str, error: Exception) -> None:
        print(f"❌ Error in {command}: {error}")
    
    def get_tag(self) -> str:
        return input("Name the recording (ENTER for datetime): ")