from .abstract import AbstractView
from typing import List, Any

class NoView(AbstractView):
    """A view that performs no output operations. Useful for testing or suppressing output."""
    
    def samples_header(self, headers: List[str]) -> None:
        pass
    
    def samples_content(self, audio_meta: List[Any]) -> None:
        pass
    
    def synthesizing(self) -> None:
        pass
    
    def recording(self) -> None:
        pass
    
    def transcribing(self) -> None:
        pass
    
    def transcription(self, text: str) -> None:
        pass
    
    def success(self, command: str, artifact: str) -> None:
        pass
    
    def interrupt(self, command: str) -> None:
        pass
    
    def throw(self, command: str, error: Exception) -> None:
        pass
    
    def get_tag(self) -> str:
        """Returns empty string instead of prompting for input"""
        return ""