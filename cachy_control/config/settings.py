"""
Settings manager for CachyOS Control Center.
Handles persistent user configurations, recent project directories, and tool preferences.
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any

DEFAULT_CONFIG_DIR = Path.home() / ".config" / "cachy-control-center"
CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"

DEFAULT_SETTINGS = {
    "recent_projects": [
        str(Path.home()),
    ],
    "default_http_port": 8000,
    "last_tab": "dashboard",
    "minecraft_server_path": str(Path.home() / "Main" / "Other" / "Minecraft" / "MCserver" / "server-1.1.4"),
    "minecraft_memory_gb": 2,
    "rclone_remotes": ["GoogleDrive", "gdrive"],
    "steam_app_ids": ["275850"],
}

class SettingsManager:
    def __init__(self, config_path: Path = CONFIG_FILE):
        self.config_path = config_path
        self._data: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        if not self.config_path.exists():
            self._data = DEFAULT_SETTINGS.copy()
            self.save()
            return
        
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._data = {**DEFAULT_SETTINGS, **json.load(f)}
        except Exception:
            self._data = DEFAULT_SETTINGS.copy()

    def save(self) -> None:
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2)
        except Exception as e:
            print(f"[SettingsManager] Failed to save config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
        self.save()

    def add_recent_project(self, path: str) -> None:
        path_str = str(Path(path).expanduser().resolve())
        projects: List[str] = self._data.get("recent_projects", [])
        if path_str in projects:
            projects.remove(path_str)
        projects.insert(0, path_str)
        self._data["recent_projects"] = projects[:10]  # keep top 10
        self.save()

    def get_recent_projects(self) -> List[str]:
        return self._data.get("recent_projects", [str(Path.home())])
