"""
Process Runner Service using PyQt6 QProcess.
Provides asynchronous, non-blocking execution with real-time log output,
stdin piping, cancellation, safe exception boundaries, upfront sudo permission verification,
and graphical terminal launcher fallback.
"""

import re
import os
import signal
import shutil
import subprocess
import shlex
from typing import Callable, Optional
from PyQt6.QtCore import QObject, QProcess, QProcessEnvironment, QTimer, pyqtSignal
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
        self._uses_process_group = False
        self._cancel_timer = QTimer(self)
        self._cancel_timer.setSingleShot(True)
        self._cancel_timer.timeout.connect(self._kill_process_group)

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
                    subprocess.Popen(
                        cmd_args,
                        start_new_session=True,
                        stdin=subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        close_fds=True,
                    )
                    self.log(f"> Launched '{command}' in {term_name}\n")
                    return
                except Exception as e:
                    print(f"[RunnerService] Failed to launch {term_name}: {e}")

        # Fallback to standard runner
        self.run_command(command)

    def launch_detached(self, argv: list[str], cwd: Optional[str] = None) -> bool:
        """Launch a GUI application without occupying the shared command runner."""
        if not argv:
            raise ValueError("argv must contain an executable")
        try:
            subprocess.Popen(
                argv,
                cwd=cwd if cwd and os.path.isdir(cwd) else None,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
                close_fds=True,
            )
            self.log(f"> Launched {shlex.join(argv)}")
            return True
        except OSError as exc:
            self.log(f"Could not launch {argv[0]}: {exc}")
            return False

    def run_command(
        self,
        command: str,
        on_output: Optional[Callable[[str], None]] = None,
        on_finish: Optional[Callable[[int], None]] = None,
        use_pkexec: bool = False,
        cwd: Optional[str] = None,
    ) -> None:
        if self.is_running():
            self.log("[Another task is running. Stop it before starting a new one.]\n")
            if on_finish:
                try:
                    on_finish(1)
                except Exception as exc:
                    print(f"[RunnerService] on_finish error: {exc}")
            return

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

        # Keep process output predictable without retaining credentials in the environment.
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PAGER", "cat")
        env.insert("PYTHONUNBUFFERED", "1")
        env.insert("DEBIAN_FRONTEND", "noninteractive")
        self._process.setProcessEnvironment(env)

        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._handle_output)
        self._process.finished.connect(self._handle_finished)
        self._process.errorOccurred.connect(self._handle_process_error)

        if use_pkexec:
            if shutil.which("pkexec"):
                program, args = "pkexec", ["bash", "-c", command]
            elif shutil.which("sudo"):
                program, args = "sudo", ["bash", "-c", command]
            else:
                program, args = "bash", ["-c", command]
        else:
            program, args = "bash", ["-c", command]

        self.process_started.emit(command)
        if self._on_output:
            try:
                self._on_output(f"> {command}\n")
            except Exception as e:
                print(f"[RunnerService] _on_output error: {e}")
        self.output_received.emit(f"> {command}\n")

        # A separate process group lets cancellation stop pipelines and their children.
        if shutil.which("setsid"):
            self._uses_process_group = True
            self._process.start("setsid", [program, *args])
        else:
            self._uses_process_group = False
            self._process.start(program, args)

    def run_argv(
        self,
        argv: list[str],
        on_output: Optional[Callable[[str], None]] = None,
        on_finish: Optional[Callable[[int], None]] = None,
        cwd: Optional[str] = None,
    ) -> None:
        """Run one executable with separate arguments, without invoking a shell."""
        if not argv:
            raise ValueError("argv must contain an executable")
        if self.is_running():
            self.log("[Another task is running. Stop it before starting a new one.]\n")
            if on_finish:
                try:
                    on_finish(1)
                except Exception as exc:
                    print(f"[RunnerService] on_finish error: {exc}")
            return
        preview = shlex.join(argv)
        if SudoService.is_sudo_needed(argv):
            from cachy_control.ui.components.sudo_dialog import request_upfront_sudo
            if not request_upfront_sudo(preview):
                self.output_received.emit("\n[Action cancelled: Administrator authentication required]\n")
                if on_finish:
                    try:
                        on_finish(1)
                    except Exception as exc:
                        print(f"[RunnerService] on_finish error: {exc}")
                return

        self._current_command = preview
        self._on_output = on_output
        self._on_finish = on_finish
        self._process = QProcess(self)
        if cwd and os.path.isdir(cwd):
            self._process.setWorkingDirectory(cwd)
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PAGER", "cat")
        env.insert("PYTHONUNBUFFERED", "1")
        self._process.setProcessEnvironment(env)
        self._process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self._process.readyReadStandardOutput.connect(self._handle_output)
        self._process.finished.connect(self._handle_finished)
        self._process.errorOccurred.connect(self._handle_process_error)
        self.process_started.emit(preview)
        self.output_received.emit(f"> {preview}\n")
        if self._on_output:
            try:
                self._on_output(f"> {preview}\n")
            except Exception as exc:
                print(f"[RunnerService] _on_output error: {exc}")
        if shutil.which("setsid"):
            self._uses_process_group = True
            self._process.start("setsid", argv)
        else:
            self._uses_process_group = False
            self._process.start(argv[0], argv[1:])

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
        self._cancel_timer.stop()
        process = self._process
        if process:
            self._handle_output()
        self._process = None
        if process:
            process.deleteLater()
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

    def _handle_process_error(self, error) -> None:
        if error == QProcess.ProcessError.FailedToStart:
            self._handle_finished(127)

    def _kill_process_group(self) -> None:
        process = self._process
        if process and process.state() != QProcess.ProcessState.NotRunning:
            pid = int(process.processId())
            try:
                if self._uses_process_group and pid > 0:
                    os.killpg(pid, signal.SIGKILL)
                else:
                    process.kill()
            except (OSError, ValueError):
                process.kill()

    def cancel_current(self) -> None:
        if self._process and self.is_running():
            pid = int(self._process.processId())
            try:
                if self._uses_process_group and pid > 0:
                    os.killpg(pid, signal.SIGTERM)
                else:
                    self._process.terminate()
            except (OSError, ValueError):
                self._process.terminate()
            self._cancel_timer.start(2000)
            self.output_received.emit("\n[Process cancelled by user]\n")
