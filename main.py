import argparse
from src.controller import Controller
from src.views.cli import CLIView
from src.views.gui import GUIView
import logging

def main():
    # Debug command
    parser = argparse.ArgumentParser(description="CLI for TTS and STT using Linguist")
    # Configuration
    parser.add_argument("--gui", action="store_true", help="Toggle GUI mode")
    parser.add_argument("--output_file", type=str, default="output.wav", help="Output file for TTS")
    parser.add_argument("--archive", type=str, default="archive", help="Archive directory for TTS")
    parser.add_argument("--whisper_model", type=str, default="base", help="Whisper model for STT")
    parser.add_argument("--debug", action="store_true", help="Toggle debugging mode")
    
    subparsers = parser.add_subparsers(dest="command")

    # Speak command
    speak_parser = subparsers.add_parser("speak", help="Convert text to speech")
    speak_parser.add_argument("--text", type=str, help="Text to convert to speech")
    speak_parser.add_argument("--tag", type=str, help="Tag the recorded audio file")
    speak_parser.add_argument("--language", type=str, help="Language for TTS")
    speak_parser.add_argument("--speaker", type=str, help="Speaker for TTS")

    # Listen command
    listen_parser = subparsers.add_parser("listen", help="Convert speech to text")
    listen_parser.add_argument("--print", action="store_true", default=True, help="Flag to print the recognized text")
    listen_parser.add_argument("--tag", type=str, help="Tag the recorded audio file")

    # Transcribe command
    transcribe_parser = subparsers.add_parser("transcribe", help="Transcribe audio file to text")
    transcribe_parser.add_argument("--path", type=str, required=True, help="Path to the audio file to transcribe")
    transcribe_parser.add_argument("--print", action="store_true", default=True, help="Flag to print the transcribed text")
    transcribe_parser.add_argument("--tag", type=str, help="Tag the transcribed audio file")

    # Archive command
    archive_parser = subparsers.add_parser("list", help="List all recorded audio samples")

    # Help command
    help_parser = subparsers.add_parser("help", help="Show help message")
    help_parser.set_defaults(func=lambda _: parser.print_help())

    args = parser.parse_args()

    view = GUIView() if args.gui else CLIView()

    lc = Controller(
            view=view,
            output_file=args.output_file,
            archive=args.archive,
            whisper_model=args.whisper_model
        )

    lc.init(args.debug)
    if args.gui:
        lc.start()
    elif args.command in lc.services():
        lc.execute(args.command, args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()