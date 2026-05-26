from .models.linguist import Linguist
from .commands import get_commands
from .views.abstract import AbstractView
from .views.lib import NoView
from .errors import LinguistError

class Controller:
    def __init__(
            self,
            view: AbstractView = NoView(),
            whisper_model="base",
            output_file="output.wav",
            archive="archive",
        ):
        self.linguist = Linguist(
            output_file=output_file,
            archive=archive,
            whisper_model=whisper_model
        )
        self.view = view
        self.commands = {}

    def __getattr__(self, name: str) -> callable:
        """Dynamically handle command calls as methods."""
        command = self.commands.get(name)
        if command:
            def command_wrapper(args):
                return command.execute(args, self.linguist)
            return command_wrapper
        raise AttributeError(f"Command '{name}' not found. Must be one of: " + ', '.join(self.services()))

    def init(self, debug) -> bool:
        try:
            self.linguist.init(debug)
            self.commands = get_commands(self.view)
            return True
        except (PermissionError, TypeError, LinguistError) as e:
            self.view.throw("init", e)
            return False

    def execute(self, command_name: str, args: dict):
        command = self.commands.get(command_name)
        if command:
            command.execute(args, self.linguist)
        else:
            self.view.throw("execute", ValueError(f"Command not found. Must be one of: {', '.join(self.services())}"))

    def services(self):
        if not self.commands:
            return []
        return list(self.commands.keys())

    def close(self):
        self.linguist.close()