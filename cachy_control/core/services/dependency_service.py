"""
Dependency Service: Detects installed binaries and generates installation commands for missing tools.
"""

import shutil
from typing import Dict, Optional

# Map binary name -> (package_name, is_aur)
BINARY_PACKAGE_MAP: Dict[str, tuple[str, bool]] = {
    "nvtop": ("nvtop", False),
    "btop": ("btop", False),
    "cachyos-rate-mirrors": ("cachyos-rate-mirrors", False),
    "yay": ("yay", True),
    "paru": ("paru", True),
    "flatpak": ("flatpak", False),
    "rclone": ("rclone", False),
    "dolphin": ("dolphin", False),
    "bluetoothctl": ("bluez-utils", False),
    "pactl": ("pipewire-pulse", False),
    "virsh": ("libvirt", False),
    "inotifywait": ("inotify-tools", False),
    "auditctl": ("audit", False),
    "ausearch": ("audit", False),
    "howdy": ("howdy", True),
    "umu-run": ("umu-launcher", True),
    "docker": ("docker", False),
    "java": ("jdk-openjdk", False),
    "zramctl": ("util-linux", False),
    "dig": ("bind", False),
}

class DependencyService:
    def is_installed(self, binary_name: str) -> bool:
        return shutil.which(binary_name) is not None

    def get_install_command(self, binary_name: str) -> str:
        pkg_info = BINARY_PACKAGE_MAP.get(binary_name, (binary_name, False))
        pkg_name, is_aur = pkg_info
        
        if is_aur:
            aur_tool = "yay" if shutil.which("yay") else ("paru" if shutil.which("paru") else "pacman")
            return f"{aur_tool} -S --noconfirm {pkg_name}"
        else:
            return f"sudo pacman -S --needed --noconfirm {pkg_name}"
