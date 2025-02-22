from abc import ABC, abstractmethod
from typing import List, Any
from datetime import datetime

class AbstractView(ABC):
    """Abstract base class defining the view interface for the application."""
    
    @abstractmethod
    def samples_header(self, headers: List[str]) -> None:
        """Display headers for audio samples listing."""
        pass
    
    @abstractmethod
    def samples_content(self, audio_meta: List[Any]) -> None:
        """Display content rows for audio samples."""
        pass
    
    @abstractmethod
    def synthesizing(self) -> None:
        """Show text-to-speech synthesis in progress."""
        pass
    
    @abstractmethod
    def recording(self) -> None:
        """Show recording in progress."""
        pass
    
    @abstractmethod
    def transcribing(self) -> None:
        """Show transcription in progress."""
        pass
    
    @abstractmethod
    def transcription(self, text: str) -> None:
        """Display transcribed text."""
        pass
    
    @abstractmethod
    def success(self, command: str, artifact: str) -> None:
        """Show success message with artifact path."""
        pass
    
    @abstractmethod
    def interrupt(self, command: str) -> None:
        """Handle command interruption."""
        pass
    
    @abstractmethod
    def throw(self, command: str, error: Exception) -> None:
        """Handle and display errors."""
        pass
    
    @abstractmethod
    def get_tag(self) -> None:
        """Get a tag for the current operation."""
        pass
    
    def stamp(self) -> str:
        """Generate a timestamp for tagging."""
        return datetime.now().strftime("%Y-%m-%d@%H%M%S")