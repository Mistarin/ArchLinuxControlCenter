# CachyOS Control Center

A minimalist, high-performance personal GUI cockpit for **CachyOS / Arch Linux**.

## Features

- **Pure Minimalist Design**: White canvas, high-contrast black typography, hard sharp geometric borders, soft drop shadows, and clean SVG vector icons (no emojis).
- **Dashboard & Dev Cockpit**: Live CPU, RAM, Swap & ZRAM allocation meters, quick launchers for `nvtop` and `btop`, local HTTP/Vite dev server with recent project memory, Java version checker, and timed system shutdown.
- **Updates & Package Management**: Full system update (Pacman + AUR + Flatpak) or granular separate updates, universal multi-source package search with source origin tags (`[core]`, `[extra]`, `[AUR]`, `[flatpak]`), CachyOS mirror rating, drag-and-drop `.pkg.tar.zst` installer, and 32-bit dependency conflict resolver.
- **One-Click System Cleanup**: Dolphin file manager config reset, Steam shader cache & texture cleaner, Pacman & Yay cache wipes, unused Flatpak runtimes remover, systemd journal log vacuum, and EasyEffects locale override.
- **Storage, Cloud & AppData**: Rclone Google Drive VFS mounter with Dolphin integration, partition health meters, and Steam Proton AppData shortcuts (No Man's Sky saves, compatdata prefixes).
- **Audio & Bluetooth**: Controller restart, device scan, pair & connect, user systemd auto-connect service generator, and PipeWire audio node switcher.
- **Network & Virtual Machines**: Libvirt / Virsh default network bridge controller, open listening ports inspector (`ss -tulpn`), ping and DNS latency diagnostics.
- **Gaming & Runners**: UMU launcher with setup wizard detector, Minecraft dedicated server launcher with Java RAM settings and process killer, Sherlock username OSINT container tool, and local `./run.sh` script runner.
- **Memory & ZRAM Tuner**: Live ZRAM monitor, `/etc/systemd/zram-generator.conf` generator, and dynamic `vm.swappiness` and `vm.page-cluster` tuner.
- **Security & Auditing**: Howdy face authentication tester, SDDM manager, auditd real-time file watch rules, `inotifywait` monitor, and SUID/SGID file scanner.
- **Live Terminal Log Drawer**: Non-blocking `QProcess` runner with real-time log streaming, cancel process support, copy to clipboard, and clear controls.

## Running

```bash
python3 main.py
```
