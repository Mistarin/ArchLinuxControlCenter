"""
Storage, Dynamic Rclone Cloud Drives & Steam Shader Cache service.
Provides safe, quoted mount commands and dynamic remote resolution.
"""

import os
import shutil
import psutil
import subprocess
import shlex
from pathlib import Path
from typing import List
from cachy_control.core.contracts.storage_contract import IStorageService, DiskPartition, CloudMount

class StorageService(IStorageService):
    def get_disk_partitions(self) -> List[DiskPartition]:
        results: List[DiskPartition] = []
        try:
            for part in psutil.disk_partitions(all=False):
                # Filter out pseudo filesystems
                if part.fstype in ("", "squashfs", "tmpfs", "devtmpfs", "overlay"):
                    continue
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    results.append(DiskPartition(
                        device=part.device,
                        mountpoint=part.mountpoint,
                        fstype=part.fstype,
                        total_gb=round(usage.total / (1024**3), 1),
                        used_gb=round(usage.used / (1024**3), 1),
                        free_gb=round(usage.free / (1024**3), 1),
                        percent=usage.percent
                    ))
                except PermissionError:
                    continue
        except Exception:
            pass
        return results

    def get_available_remotes(self) -> List[str]:
        """Returns list of configured rclone remotes dynamically."""
        if not shutil.which("rclone"):
            return []
        try:
            res = subprocess.run(["rclone", "listremotes"], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                remotes = [r.strip().rstrip(":") for r in res.stdout.split("\n") if r.strip()]
                return remotes
        except Exception:
            pass
        return []

    def get_cloud_mounts(self) -> List[CloudMount]:
        """Checks status of configured and detected cloud mounts."""
        remotes = self.get_available_remotes()
        if not remotes:
            remotes = ["gdrive"]

        mounted_points = {p.mountpoint for p in psutil.disk_partitions(all=True)}
        
        mounts: List[CloudMount] = []
        for remote in remotes:
            mount_path = str(Path.home() / "Cloud" / remote)
            is_mounted = mount_path in mounted_points or os.path.ismount(mount_path)
            mounts.append(CloudMount(
                remote_name=remote,
                mount_point=mount_path,
                is_mounted=is_mounted
            ))
        return mounts

    def get_mount_command(self, remote_name: str, mount_point: str) -> str:
        remote_clean = remote_name.rstrip(":")
        expanded_path = str(Path(mount_point).expanduser())
        safe_path = shlex.quote(expanded_path)
        safe_remote = shlex.quote(f"{remote_clean}:")
        return f"mkdir -p {safe_path} && rclone mount {safe_remote} {safe_path} --vfs-cache-mode writes --daemon"

    def get_unmount_command(self, mount_point: str) -> str:
        expanded_path = str(Path(mount_point).expanduser())
        safe_path = shlex.quote(expanded_path)
        return f"fusermount -u {safe_path}"

    def get_reconnect_command(self, remote_name: str) -> str:
        remote_clean = remote_name.rstrip(":")
        safe_remote = shlex.quote(f"{remote_clean}:")
        for term in ["ghostty", "alacritty", "kitty", "konsole", "foot", "xterm"]:
            if shutil.which(term):
                return f"{term} -e rclone config reconnect {safe_remote} &"
        return f"rclone config reconnect {safe_remote}"

    def get_rclone_config_command(self) -> str:
        for term in ["ghostty", "alacritty", "kitty", "konsole", "foot", "xterm"]:
            if shutil.which(term):
                return f"{term} -e rclone config &"
        return "rclone config"

    def get_steam_shader_dirs(self, app_id: str = "275850") -> List[str]:
        clean_id = "".join(c for c in app_id if c.isdigit())
        if not clean_id:
            clean_id = "275850"
        steam_base = Path.home() / ".local" / "share" / "Steam" / "steamapps"
        paths = []
        
        shader_cache = steam_base / "shadercache" / clean_id
        if shader_cache.exists():
            paths.append(str(shader_cache))

        compat_data = steam_base / "compatdata" / clean_id
        if compat_data.exists():
            paths.append(str(compat_data))

        return paths

    def get_clean_shader_command(self, app_id: str = "275850") -> str:
        clean_id = "".join(c for c in app_id if c.isdigit())
        if not clean_id:
            clean_id = "275850"
        steam_base = str(Path.home() / ".local" / "share" / "Steam" / "steamapps" / "shadercache" / clean_id)
        safe_path = shlex.quote(steam_base)
        return f"rm -rf {safe_path} && echo 'Cleaned Steam shadercache for AppID {clean_id}'"
