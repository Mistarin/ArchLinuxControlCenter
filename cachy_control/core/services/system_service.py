"""
System Service implementation.
Gathers hardware and kernel statistics, ZRAM details, power commands,
desktop application menu integration, and autostart configuration.
"""

import sys
import os
import subprocess
import shutil
from pathlib import Path
from typing import List
import psutil
from cachy_control.core.contracts.system_contract import ISystemService, SystemMetrics

class SystemService(ISystemService):
    def get_metrics(self) -> SystemMetrics:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_cores = psutil.cpu_count(logical=True) or 1

        # Memory
        mem = psutil.virtual_memory()
        ram_total = mem.total / (1024 ** 3)
        ram_used = mem.used / (1024 ** 3)
        ram_pct = mem.percent

        # Swap
        swap = psutil.swap_memory()
        swap_total = swap.total / (1024 ** 3)
        swap_used = swap.used / (1024 ** 3)
        swap_pct = swap.percent

        # Swappiness
        swappiness = 60
        try:
            with open("/proc/sys/vm/swappiness", "r") as f:
                swappiness = int(f.read().strip())
        except Exception:
            pass

        # ZRAM details
        zram_info = "Not active"
        if shutil.which("zramctl"):
            try:
                res = subprocess.run(["zramctl", "--output-all"], capture_output=True, text=True, timeout=1)
                if res.returncode == 0 and res.stdout.strip():
                    lines = res.stdout.strip().split("\n")
                    if len(lines) > 1:
                        zram_info = f"{len(lines)-1} device(s) active"
            except Exception:
                pass

        return SystemMetrics(
            cpu_percent=cpu_percent,
            cpu_cores=cpu_cores,
            ram_total_gb=round(ram_total, 2),
            ram_used_gb=round(ram_used, 2),
            ram_percent=ram_pct,
            swap_total_gb=round(swap_total, 2),
            swap_used_gb=round(swap_used, 2),
            swap_percent=swap_pct,
            zram_info=zram_info,
            swappiness=swappiness
        )

    def get_java_versions(self) -> List[str]:
        if not shutil.which("archlinux-java"):
            return ["archlinux-java not installed"]
        try:
            res = subprocess.run(["archlinux-java", "status"], capture_output=True, text=True, timeout=2)
            lines = [l.strip() for l in res.stdout.split("\n") if l.strip()]
            return lines if lines else ["No Java environments detected"]
        except Exception as e:
            return [f"Error checking java: {e}"]

    def schedule_shutdown(self, minutes: int) -> str:
        return f"sudo shutdown -P +{minutes}"

    def cancel_shutdown(self) -> str:
        return "sudo shutdown -c"

    # --- Desktop Application Menu & Autostart Management ---

    def _get_main_script_path(self) -> str:
        return str(Path(__file__).parent.parent.parent.parent / "main.py")

    def _get_icon_path(self) -> str:
        icon_path = Path(__file__).parent.parent.parent / "ui" / "assets" / "logo_256.png"
        if not icon_path.exists():
            icon_path = Path(__file__).parent.parent.parent / "ui" / "assets" / "logo.png"
        return str(icon_path)

    def _generate_desktop_entry(self) -> str:
        script = self._get_main_script_path()
        icon = self._get_icon_path()
        return f"""[Desktop Entry]
Name=CachyOS Control Center
Comment=Personal GUI Cockpit for CachyOS and Arch Linux
Exec={sys.executable} {script}
Icon={icon}
Terminal=false
Type=Application
Categories=System;Settings;Utility;
StartupNotify=true
"""

    def is_app_menu_installed(self) -> bool:
        dest = Path.home() / ".local" / "share" / "applications" / "cachy-control-center.desktop"
        return dest.exists()

    def install_app_menu(self) -> bool:
        try:
            app_dir = Path.home() / ".local" / "share" / "applications"
            app_dir.mkdir(parents=True, exist_ok=True)
            desktop_file = app_dir / "cachy-control-center.desktop"
            
            with open(desktop_file, "w", encoding="utf-8") as f:
                f.write(self._generate_desktop_entry())

            # Also copy icon to hicolor icons
            icon_dir = Path.home() / ".local" / "share" / "icons" / "hicolor" / "256x256" / "apps"
            icon_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self._get_icon_path(), icon_dir / "cachy-control-center.png")
            
            # Update desktop database
            if shutil.which("update-desktop-database"):
                subprocess.run(["update-desktop-database", str(app_dir)], capture_output=True)
            return True
        except Exception as e:
            print(f"[SystemService] install_app_menu failed: {e}")
            return False

    def uninstall_app_menu(self) -> bool:
        try:
            desktop_file = Path.home() / ".local" / "share" / "applications" / "cachy-control-center.desktop"
            if desktop_file.exists():
                desktop_file.unlink()
            return True
        except Exception as e:
            print(f"[SystemService] uninstall_app_menu failed: {e}")
            return False

    def is_autostart_enabled(self) -> bool:
        dest = Path.home() / ".config" / "autostart" / "cachy-control-center.desktop"
        return dest.exists()

    def enable_autostart(self) -> bool:
        try:
            auto_dir = Path.home() / ".config" / "autostart"
            auto_dir.mkdir(parents=True, exist_ok=True)
            desktop_file = auto_dir / "cachy-control-center.desktop"
            
            with open(desktop_file, "w", encoding="utf-8") as f:
                f.write(self._generate_desktop_entry())
            return True
        except Exception as e:
            print(f"[SystemService] enable_autostart failed: {e}")
            return False

    def disable_autostart(self) -> bool:
        try:
            desktop_file = Path.home() / ".config" / "autostart" / "cachy-control-center.desktop"
            if desktop_file.exists():
                desktop_file.unlink()
            return True
        except Exception as e:
            print(f"[SystemService] disable_autostart failed: {e}")
            return False
