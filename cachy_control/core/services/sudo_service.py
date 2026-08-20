"""
Sudo Service: Upfront authentication manager for root/sudo command execution.
Maintains session password caching, background non-blocking keepalive timer,
and secure SUDO_ASKPASS bridge with restricted permissions.
"""

import os
import stat
import subprocess
import threading
from typing import Tuple, Optional
from PyQt6.QtCore import QObject, QTimer, QProcess

class SudoService(QObject):
    _instance: Optional['SudoService'] = None
    _session_password: Optional[str] = None
    _cache_dir: str = os.path.expanduser("~/.cache/cachy_control")
    _askpass_path: str = os.path.join(_cache_dir, "cachy-askpass.sh")
    _pass_file_path: str = os.path.join(_cache_dir, ".pass_vault")

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._keepalive_timer = QTimer(self)
        self._keepalive_timer.setInterval(45 * 1000) # every 45 seconds
        self._keepalive_timer.timeout.connect(self._keepalive_tick)

    @classmethod
    def get_instance(cls) -> 'SudoService':
        if cls._instance is None:
            cls._instance = SudoService()
        return cls._instance

    @classmethod
    def is_sudo_needed(cls, command: str) -> bool:
        """Returns True if the command contains sudo or commands requiring root."""
        cmd_lower = command.lower()
        sudo_indicators = [
            "sudo", "yay", "paru", "pacman -s", "pacman -r", "pacman -u", "pacman -d",
            "systemctl start", "systemctl stop", "systemctl restart", "systemctl enable",
            "systemctl disable", "cachyos-rate-mirrors", "swapon", "swapoff", "zramctl",
            "btrfs", "auditctl", "rm -f /var", "rm -rf /var"
        ]
        for ind in sudo_indicators:
            if ind in cmd_lower:
                return True
        return False

    @classmethod
    def is_sudo_cached(cls) -> bool:
        """Returns True if sudo timestamp is already active and valid."""
        try:
            res = subprocess.run(["sudo", "-n", "true"], capture_output=True, timeout=2)
            return res.returncode == 0
        except Exception:
            return False

    @classmethod
    def get_cached_password(cls) -> str:
        return cls._session_password or ""

    @classmethod
    def get_askpass_path(cls) -> str:
        return cls._askpass_path

    @classmethod
    def setup_askpass_script(cls) -> None:
        """Writes secure askpass script and password vault with 0700/0600 file permissions."""
        os.makedirs(cls._cache_dir, exist_ok=True)
        os.chmod(cls._cache_dir, stat.S_IRWXU) # 0700

        # Write password vault with 0600 (owner read/write only)
        if cls._session_password:
            with open(cls._pass_file_path, "w", encoding="utf-8") as f:
                f.write(cls._session_password)
            os.chmod(cls._pass_file_path, stat.S_IRUSR | stat.S_IWUSR)

        # Write helper askpass executable
        script_content = f"""#!/bin/sh
if [ -f "{cls._pass_file_path}" ]; then
    cat "{cls._pass_file_path}"
else
    echo "$CACHY_SUDO_PASS"
fi
"""
        with open(cls._askpass_path, "w", encoding="utf-8") as f:
            f.write(script_content)
        # Set 0700 permissions (user executable only)
        os.chmod(cls._askpass_path, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

    @classmethod
    def clear_credentials(cls) -> None:
        """Securely clears session password and unlinks temporary vault files."""
        cls._session_password = None
        if os.path.exists(cls._pass_file_path):
            try:
                os.remove(cls._pass_file_path)
            except Exception:
                pass

    @classmethod
    def validate_and_cache_password(cls, password: str) -> Tuple[bool, str]:
        """
        Validates the password with `sudo -S -v`.
        If valid, caches session credentials, creates askpass helper, and starts keepalive.
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
                cls._session_password = password
                cls.setup_askpass_script()
                # Start keepalive timer
                inst = cls.get_instance()
                if not inst._keepalive_timer.isActive():
                    inst._keepalive_timer.start()
                return True, "Authenticated"
            else:
                err = proc.stderr.strip() or "Incorrect password."
                return False, err
        except subprocess.TimeoutExpired:
            return False, "Authentication timed out."
        except Exception as e:
            return False, str(e)

    def _keepalive_tick(self) -> None:
        """Non-blocking sudo keepalive to prevent timestamp expiry without stalling UI."""
        def _run_bg():
            pwd = SudoService.get_cached_password()
            if pwd:
                try:
                    subprocess.run(
                        ["sudo", "-S", "-v"],
                        input=pwd + "\n",
                        capture_output=True,
                        timeout=3
                    )
                except Exception:
                    pass
            elif SudoService.is_sudo_cached():
                try:
                    subprocess.run(["sudo", "-n", "-v"], capture_output=True, timeout=2)
                except Exception:
                    pass

        t = threading.Thread(target=_run_bg, daemon=True)
        t.start()
