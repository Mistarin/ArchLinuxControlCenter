# CachyOS Control Center

[![Linux](https://img.shields.io/badge/Linux-FCC624?style=flat&logo=linux&logoColor=black)](https://kernel.org)
[![Arch Linux](https://img.shields.io/badge/Arch%20Linux-1793D1?style=flat&logo=archlinux&logoColor=white)](https://archlinux.org)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/GUI-PyQt6-41CD52?style=flat&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)

<img width="2560" height="1440" alt="Snímek obrazovky_20260821_015737" src="https://github.com/user-attachments/assets/74e2d8d2-55bd-4436-8be3-bb85ec0913c1" />

A desktop utility for managing common **CachyOS / Arch Linux** tasks.

## Features

- **Dashboard**: CPU, memory, swap, and ZRAM status; launchers for `nvtop` and `btop`; local development servers; Java selection; and shutdown scheduling.
- **Packages and updates**: Search Arch repositories, AUR, and Flatpak; review pending updates; manage packages; and install local package files.
- **Cleanup**: Reset Dolphin settings, clear package and shader caches, remove unused Flatpak runtimes, vacuum system logs, and change the EasyEffects locale.
- **Storage and cloud**: Mount configured rclone remotes, inspect mounted filesystems, and open Steam Proton data folders.
- **Audio and Bluetooth**: Discover and connect Bluetooth devices, restart Bluetooth, and choose a PipeWire playback output.
- **Network and virtual machines**: Manage the default libvirt network, inspect listening ports, and run basic network diagnostics.
- **Gaming tools**: Launch Windows executables with UMU, manage a local Minecraft server, and inspect or stop processes.
- **Memory and security**: View and configure ZRAM, adjust selected kernel memory settings, inspect permissions, and manage audit watches.
- **Command output**: Review command output, respond to interactive package manager prompts, and stop long-running commands.

## Running

Requires Python 3.10+, PyQt6, and psutil. Install those dependencies for your distribution before starting the app. The generated AppImage uses the target system's Python, PyQt6, and psutil; it does not bundle them. Building it requires `appimagetool` installed separately.

```bash
python3 main.py
```
