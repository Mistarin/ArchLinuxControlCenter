"""Runner Service Contract."""
from typing import Callable, Optional

class IRunnerService:
    def run_command(
        self,
        command: str,
        on_output: Optional[Callable[[str], None]] = None,
        on_finish: Optional[Callable[[int], None]] = None,
        use_pkexec: bool = False,
        cwd: Optional[str] = None,
    ) -> None:
        """Executes a command asynchronously."""
        raise NotImplementedError

    def cancel_current(self) -> None:
        """Terminates currently executing process."""
        raise NotImplementedError

    def is_running(self) -> bool:
        """Returns whether a command is currently active."""
        raise NotImplementedError
