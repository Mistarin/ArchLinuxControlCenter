"""Authenticate administrator actions through sudo's normal timestamp cache."""

import os
import subprocess
import shlex
import re
from typing import Tuple, Optional
from PyQt6.QtCore import QObject

class SudoService(QObject):
    _instance: Optional['SudoService'] = None

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)

    @classmethod
    def get_instance(cls) -> 'SudoService':
        if cls._instance is None:
            cls._instance = SudoService()
        return cls._instance

    @classmethod
    def cleanup_legacy_credentials(cls) -> None:
        """Remove plaintext credentials created by older application versions."""
        legacy_dir = os.path.join(os.path.expanduser("~"), ".cache", "cachy_control")
        for filename in (".pass_vault", "cachy-askpass.sh"):
            try:
                os.unlink(os.path.join(legacy_dir, filename))
            except FileNotFoundError:
                pass
            except OSError:
                # Cleanup should not prevent the control center from opening.
                pass

    @classmethod
    def is_sudo_needed(cls, command) -> bool:
        """Detect explicit privileged command prefixes without substring guesses."""
        if isinstance(command, (list, tuple)):
            words = [str(word) for word in command]
        else:
            try:
                words = shlex.split(str(command), comments=False)
            except ValueError:
                words = re.findall(r"[A-Za-z0-9_./+-]+", str(command))
        privileged = {"sudo", "pkexec", "yay", "paru"}
        return any(os.path.basename(word) in privileged for word in words)

    @classmethod
    def is_sudo_cached(cls) -> bool:
        """Returns True if sudo timestamp is already active and valid."""
        try:
            res = subprocess.run(["sudo", "-n", "true"], capture_output=True, timeout=2)
            return res.returncode == 0
        except Exception:
            return False

    @classmethod
    def validate_and_cache_password(cls, password: str) -> Tuple[bool, str]:
        """
        Validates the password with `sudo -S -v`.
        If valid, sudo records its normal timestamp for this user session. The password
        is never retained by the application.
        """
        try:
            proc = subprocess.run(
                ["sudo", "-S", "-v"],
                input=password + "\n",
                capture_output=True,
                text=True,
                timeout=5
            )
            if proc.returncode == 0:
                return True, "Authenticated"
            else:
                err = proc.stderr.strip() or "Incorrect password."
                return False, err
        except subprocess.TimeoutExpired:
            return False, "Authentication timed out."
        except Exception as e:
            return False, str(e)
