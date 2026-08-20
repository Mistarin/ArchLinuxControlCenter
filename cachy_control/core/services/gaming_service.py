"""
Gaming, UMU Launcher, Minecraft Dedicated Server & Process Doctor.
Safe, quoted execution strings for Wine/Proton and Java game servers.
"""

import shlex
import shutil
import psutil
from typing import List, Dict, Any, Optional

class GamingService:
    def is_umu_installed(self) -> bool:
        return shutil.which("umu-run") is not None

    def get_umu_install_command(self) -> str:
        aur = "yay" if shutil.which("yay") else ("paru" if shutil.which("paru") else "pacman")
        return f"{aur} -S --noconfirm umu-launcher"

    def get_umu_run_command(self, game_executable: str) -> str:
        safe_exe = shlex.quote(game_executable)
        if game_executable.lower().endswith(".msi"):
            return f"umu-run msiexec /i {safe_exe}"
        return f"umu-run {safe_exe}"

    def get_umu_launch_command(self, game_executable: str, appid: str = "0") -> str:
        clean_appid = "".join(c for c in appid if c.isdigit())
        safe_exe = shlex.quote(game_executable)
        if clean_appid and clean_appid != "0":
            return f"GAMEID={clean_appid} umu-run {safe_exe}"
        return self.get_umu_run_command(game_executable)

    def get_minecraft_start_command(self, server_dir: str, min_ram: int = 4, max_ram: int = 8) -> str:
        safe_dir = shlex.quote(server_dir)
        safe_min = max(1, min(128, int(min_ram)))
        safe_max = max(safe_min, min(128, int(max_ram)))
        return f"cd {safe_dir} && java -Xms{safe_min}G -Xmx{safe_max}G -jar server.jar nogui"

    def get_running_java_processes(self) -> List[Dict[str, Any]]:
        java_procs = []
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_percent']):
            try:
                name = proc.info['name'] or ""
                cmd = " ".join(proc.info['cmdline'] or [])
                if "java" in name.lower() or "java" in cmd.lower():
                    java_procs.append({
                        "pid": proc.info['pid'],
                        "cmd": cmd[:80],
                        "memory": round(proc.info['memory_percent'] or 0, 1)
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return java_procs

    def get_running_processes(self, query: str = "") -> List[Dict[str, Any]]:
        procs = []
        q = query.lower()
        for proc in psutil.process_iter(['pid', 'username', 'name', 'cmdline', 'cpu_percent', 'memory_percent']):
            try:
                name = proc.info['name'] or ""
                cmd = " ".join(proc.info['cmdline'] or [])
                user = proc.info['username'] or "-"
                if not q or q in name.lower() or q in cmd.lower() or q in str(proc.info['pid']):
                    procs.append({
                        "pid": proc.info['pid'],
                        "user": user,
                        "cpu": f"{proc.info['cpu_percent'] or 0:.1f}%",
                        "command": cmd[:90] if cmd else name,
                        "memory": round(proc.info['memory_percent'] or 0, 1)
                    })
                    if len(procs) >= 50:
                        break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return procs

    def get_kill_process_command(self, pid: int) -> str:
        safe_pid = int(pid)
        return f"kill -9 {safe_pid}"

    def get_sherlock_pull_command(self) -> str:
        return "docker pull sherlock/sherlock"

    def get_sherlock_run_command(self, username: str) -> str:
        safe_user = shlex.quote(username.strip())
        return f"docker run --rm -t sherlock/sherlock {safe_user}"
