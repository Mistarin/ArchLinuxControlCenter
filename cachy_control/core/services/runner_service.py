"""
Process Runner Service using PyQt6 QProcess.
Provides asynchronous, non-blocking execution with real-time log output,
stdin piping, cancellation, safe exception boundaries, upfront sudo permission verification,
and graphical terminal launcher fallback.
"""

import re
import os
import shutil
import subprocess
from typing import Callable, Optional
from PyQt6.QtCore import QObject, QProcess, QProcessEnvironment, pyqtSignal
from cachy_control.core.contracts.runner_contract import IRunnerService
from cachy_control.core.services.sudo_service import SudoService

ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

def clean_ansi(text: str) -> str:
    """Removes ANSI color and formatting escape codes from text."""
    return ANSI_ESCAPE.sub('', text)

class RunnerService(QObject, IRunnerService):
    output_received = pyqtSignal(str)
    process_started = pyqtSignal(str) # command
    process_finished = pyqtSignal(int) # exit code

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._process: Optional[QProcess] = None
        self._current_command: str = ""
        self._on_output: Optional[Callable[[str], None]] = None
        self._on_finish: Optional[Callable[[int], None]] = None

    def is_running(self) -> bool:
        return self._process is not None and self._process.state() != QProcess.ProcessState.NotRunning

    def log(self, message: str) -> None:
        """Emits a log message to the terminal drawer output channel."""
        if not message.endswith("\n"):
            message += "\n"
        self.output_received.emit(message)

    def run_in_terminal(self, command: str) -> None:
        """
        Executes a command inside an external terminal emulator window (e.g. for btop, nvtop).
        Falls back cleanly to the built-in docked runner if no external emulator is found.
        """
        terms = [
            ("ghostty", ["ghostty", "-e", "bash", "-c", command]),
            ("alacritty", ["alacritty", "-e", "bash", "-c", command]),
            ("kitty", ["kitty", "bash", "-c", command]),
            ("konsole", ["konsole", "-e", "bash", "-c", command]),
            ("foot", ["foot", "bash", "-c", command]),
            ("xterm", ["xterm", "-e", "bash", "-c", command]),
        ]
        for term_name, cmd_args in terms:
            if shutil.which(term_name):
                try:
                    subprocess.Popen(cmd_args)
                    self.log(f"> Launched '{command}' in {term_name}\n")
                    return
                except Exception as e:
                    print(f"[RunnerService] Failed to launch {term_name}: {e}")

        # Fallback to standard runner
        self.run_command(command)

    def run_command(
        self,
        command: str,
        on_output: Optional[Callable[[str], None]] = None,
        on_finish: Optional[Callable[[int], None]] = None,
        use_pkexec: bool = False,
        cwd: Optional[str] = None,
    ) -> None:
        if self.is_running():
            self.cancel_current()

        # Check if root/sudo permissions are needed and ask upfront
        if SudoService.is_sudo_needed(command):
            from cachy_control.ui.components.sudo_dialog import request_upfront_sudo
            if not request_upfront_sudo(command):
                self.output_received.emit("\n[Action cancelled: Administrator authentication required]\n")
                if on_finish:
                    try:
                        on_finish(1)
                    except Exception as e:
                        print(f"[RunnerService] on_finish error: {e}")
                return

        self._current_command = command
        self._on_output = on_output
        self._on_finish = on_finish

        self._process = QProcess(self)
        if cwd and os.path.isdir(cwd):
            self._process.setWorkingDirectory(cwd)

        # Set process environment variables
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PAGER", "cat")
        env.insert("PYTHONUNBUFFERED", "1")
        env.insert("DEBIAN_FRONTEND", "noninteractive")
        if SudoService.get_cached_password():
            env.insert("SUDO_ASKPASS", SudoService.get_askpass_path())
            env.insert("SUDO_ASKPASS_REQUIRE", "force")
            env.insert("SSH_ASKPASS", SudoService.get_askpass_path())
            env.insert("SSH_ASKPASS_REQUIRE", "force")
        self._process.setProcessEnvironment(env)

        # Merge stderr into stdout channel for seamless log capture
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._handle_output)
        self._process.finished.connect(self._handle_finished)

        # Prepare final execution string
        exec_cmd = command
        if use_pkexec:
            if shutil.which("pkexec"):
                exec_cmd = f"pkexec bash -c '{command}'"
            elif shutil.which("sudo"):
                exec_cmd = f"sudo bash -c '{command}'"

        self.process_started.emit(command)
        if self._on_output:
            try:
                self._on_output(f"> {command}\n")
            except Exception as e:
                print(f"[RunnerService] _on_output error: {e}")
        self.output_received.emit(f"> {command}\n")

        self._process.start("bash", ["-c", exec_cmd])

    def write_input(self, text: str) -> None:
        """Sends user input to the running process's stdin channel."""
        if self._process and self.is_running():
            self.output_received.emit(f"{text}\n")
            self._process.write((text + "\n").encode("utf-8"))

    def _handle_output(self) -> None:
        if not self._process:
            return
        data = self._process.readAllStandardOutput().data().decode("utf-8", errors="replace")
        cleaned = clean_ansi(data)
        if self._on_output:
            try:
                self._on_output(cleaned)
            except Exception as e:
                print(f"[RunnerService] _on_output error: {e}")
        self.output_received.emit(cleaned)

    def _handle_finished(self, exit_code: int) -> None:
        status_msg = f"\n[Process exited with code {exit_code}]\n"
        if self._on_output:
            try:
                self._on_output(status_msg)
            except Exception as e:
                print(f"[RunnerService] _on_output error: {e}")
        self.output_received.emit(status_msg)
        self.process_finished.emit(exit_code)
        if self._on_finish:
            try:
                self._on_finish(exit_code)
            except Exception as e:
                print(f"[RunnerService] _on_finish error: {e}")
        self._process = None

    def cancel_current(self) -> None:
        if self._process and self.is_running():
            self._process.terminate()
            if not self._process.waitForFinished(1000):
                self._process.kill()
            self.output_received.emit("\n[Process cancelled by user]\n")
