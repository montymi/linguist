from prompt_toolkit import HTML
from prompt_toolkit.shortcuts import button_dialog, input_dialog, message_dialog
from prompt_toolkit.styles import Style
from .abstract import AbstractView
from typing import List, Any
import os

class GUIView(AbstractView):
    def __init__(self):
        self.style = Style.from_dict({
            'dialog': 'bg:#2b2b2b',
            'button': 'bg:#666666 #ffffff',
            'dialog.body': 'bg:#2b2b2b #ffffff',
            'dialog shadow': 'bg:#000000',
        })

    def samples_header(self, headers: List[str]) -> None:
        self._display_table_header = headers

    def samples_content(self, audio_meta: List[Any]) -> None:
        content = []
        for meta in audio_meta:
            size_mb = meta.bytes / (1024 * 1024)
            
            if meta.duration < 60:
                duration = f"{meta.duration:.2f}s"
            elif meta.duration < 3600:
                duration = f"{(meta.duration / 60):.2f}min"
            else:
                duration = f"{(meta.duration / 3600):.2f}h"
                
            row = [
                os.path.basename(meta.file)[:30],
                f"{size_mb:.2f} MB",
                duration,
                str(meta.rate),
                str(meta.width)
            ]
            content.append(row)

        self._show_table(content)

    def _show_table(self, content: List[List[str]]) -> None:
        table_html = "<table>"
        # Add header
        table_html += "<tr>"
        for header in self._display_table_header:
            table_html += f"<th>{header}</th>"
        table_html += "</tr>"
        
        # Add content
        for row in content:
            table_html += "<tr>"
            for cell in row:
                table_html += f"<td>{cell}</td>"
            table_html += "</tr>"
        table_html += "</table>"
        
        message_dialog(
            title="Audio Samples",
            text=HTML(table_html),
            style=self.style
        ).run()

    def synthesizing(self) -> None:
        message_dialog(
            title="Synthesizing",
            text="🎵 Synthesizing speech... Press Ctrl+C to stop.",
            style=self.style
        ).run()

    def recording(self) -> None:
        message_dialog(
            title="Recording",
            text="🎤 Recording in progress... Press Enter to stop. 🔴",
            style=self.style
        ).run()

    def transcribing(self) -> None:
        message_dialog(
            title="Transcribing",
            text="📝 Transcribing audio... Press Ctrl+C to stop. 🔊",
            style=self.style
        ).run()

    def transcription(self, text: str) -> None:
        message_dialog(
            title="Transcription Result",
            text=f"\n❝{text}❞\n",
            style=self.style
        ).run()

    def success(self, command: str, artifact: str) -> None:
        message_dialog(
            title="Success",
            text=f"✅ {command.title()} complete.\nOutput saved to: {artifact}",
            style=self.style
        ).run()

    def interrupt(self, command: str) -> None:
        message_dialog(
            title="Interrupted",
            text=f"⚠️ {command.title()} interrupted.",
            style=self.style
        ).run()

    def throw(self, command: str, error: Exception) -> None:
        message_dialog(
            title="Error",
            text=f"❌ Error in {command}: {error}",
            style=self.style
        ).run()

    def get_tag(self) -> str:
        result = input_dialog(
            title="Tag Recording",
            text="Enter a tag for the recording (or press Enter for timestamp):",
            style=self.style
        ).run()
        
        return result