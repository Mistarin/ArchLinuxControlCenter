"""
Local Dev & Project Server Service.
Allows quick one-click launching of npm, pnpm, yarn, bun, Python, Vite, and custom dev servers.
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Tuple

class DevServerService:
    RUNNERS = [
        ("pnpm", "pnpm run dev", 3000),
        ("npm", "npm run dev", 3000),
        ("yarn", "yarn dev", 3000),
        ("bun", "bun dev", 3000),
        ("vite", "npx vite --port {port} --host 127.0.0.1", 5173),
        ("python_http", "python3 -m http.server {port} --bind 127.0.0.1", 8080),
        ("cargo", "cargo run", 8080),
        ("go", "go run .", 8080),
        ("custom", "{custom}", 3000),
    ]

    def detect_project_runner(self, directory: str) -> str:
        """Inspects directory for lockfiles / config to auto-suggest the best dev runner."""
        p = Path(directory).expanduser()
        if not p.is_dir():
            return "npm"

        if (p / "pnpm-lock.yaml").exists():
            return "pnpm"
        if (p / "bun.lockb").exists() or (p / "bun.lock").exists():
            return "bun"
        if (p / "yarn.lock").exists():
            return "yarn"
        if (p / "package.json").exists():
            if shutil.which("pnpm"):
                return "pnpm"
            elif shutil.which("npm"):
                return "npm"
            return "npm"
        if (p / "Cargo.toml").exists():
            return "cargo"
        if (p / "go.mod").exists():
            return "go"
        if (p / "vite.config.js").exists() or (p / "vite.config.ts").exists():
            return "vite"
        if (p / "index.html").exists():
            return "python_http"

        return "npm"

    def get_command(self, runner_key: str, directory: str, port: int = 3000, custom_cmd: str = "") -> str:
        dir_path = str(Path(directory).expanduser().resolve())
        cmd = ""
        if runner_key == "pnpm":
            cmd = "pnpm run dev"
        elif runner_key == "npm":
            cmd = "npm run dev"
        elif runner_key == "yarn":
            cmd = "yarn dev"
        elif runner_key == "bun":
            cmd = "bun dev"
        elif runner_key == "vite":
            cmd = f"npx vite --port {port} --host 127.0.0.1"
        elif runner_key == "python_http":
            cmd = f"python3 -m http.server {port} --bind 127.0.0.1"
        elif runner_key == "cargo":
            cmd = "cargo run"
        elif runner_key == "go":
            cmd = "go run ."
        elif runner_key == "custom":
            cmd = custom_cmd.strip() or "npm run dev"
        else:
            cmd = f"npm run dev"

        return f"cd '{dir_path}' && {cmd}"
