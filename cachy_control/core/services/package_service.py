"""
Package Service implementation.
Ultra-fast native in-memory search using pyalpm / ALPM with fallbacks,
plus pending updates inspection with download sizes and build dates.
Includes safe quoting and accurate Flatpak installation state detection.
"""

import os
import glob
import subprocess
import shutil
import re
import shlex
import logging
from typing import List, Set, Optional
from cachy_control.core.contracts.package_contract import IPackageService, PackageItem, PendingUpdate

logger = logging.getLogger(__name__)

class PackageService(IPackageService):
    def __init__(self):
        self._alpm_handle = None
        self._syncdbs = []
        self._localdb = None
        self._installed_cache: Set[str] = set()
        self._init_alpm()

    def _init_alpm(self):
        try:
            import pyalpm
            self._alpm_handle = pyalpm.Handle('/', '/var/lib/pacman')
            # Auto-register all sync databases found in /var/lib/pacman/sync/*.db
            for db_path in glob.glob('/var/lib/pacman/sync/*.db'):
                db_name = os.path.basename(db_path)[:-3]
                try:
                    self._alpm_handle.register_syncdb(db_name, 0)
                except Exception as exc:
                    logger.warning("Could not register ALPM sync database %s: %s", db_name, exc)
            self._syncdbs = self._alpm_handle.get_syncdbs()
            self._localdb = self._alpm_handle.get_localdb()
            self._installed_cache = {pkg.name for pkg in self._localdb.pkgcache}
        except Exception as e:
            self._alpm_handle = None
            logger.warning("ALPM unavailable; using command-line package fallbacks: %s", e)

    def get_installed_sources(self, refresh: bool = False) -> dict[str, Set[str]]:
        """Return installed package IDs, populated once per store refresh.

        Store cards must only read this snapshot; package-manager commands are
        deliberately kept out of individual widget construction.
        """
        if refresh or not hasattr(self, "_installed_source_cache"):
            arch = set(self._get_installed_set())
            if not arch and not self._localdb and shutil.which("pacman"):
                try:
                    result = subprocess.run(
                        ["pacman", "-Qq"], capture_output=True, text=True, timeout=2,
                    )
                    if result.returncode == 0:
                        arch = {line.strip() for line in result.stdout.splitlines() if line.strip()}
                    else:
                        logger.warning("pacman -Qq failed with exit code %s", result.returncode)
                except (OSError, subprocess.SubprocessError) as exc:
                    logger.warning("Could not read installed Arch packages: %s", exc)
            flatpak = set()
            if shutil.which("flatpak"):
                try:
                    result = subprocess.run(
                        ["flatpak", "list", "--columns=application"],
                        capture_output=True, text=True, timeout=2,
                    )
                    if result.returncode == 0:
                        flatpak = {line.strip() for line in result.stdout.splitlines() if line.strip()}
                    else:
                        logger.warning("flatpak list failed with exit code %s", result.returncode)
                except (OSError, subprocess.SubprocessError) as exc:
                    logger.warning("Could not read installed Flatpaks: %s", exc)
            self._installed_source_cache = {"arch": arch, "flatpak": flatpak}
        return self._installed_source_cache

    def is_source_installed(self, source_type: str, package: str) -> bool:
        installed = self.get_installed_sources()
        return package in installed["flatpak" if source_type == "flatpak" else "arch"]

    def _get_installed_set(self) -> Set[str]:
        if self._localdb:
            try:
                self._installed_cache = {pkg.name for pkg in self._localdb.pkgcache}
            except Exception as exc:
                logger.warning("Could not refresh the ALPM installed package cache: %s", exc)
        return self._installed_cache

    def get_pending_updates(self) -> List[PendingUpdate]:
        updates: List[PendingUpdate] = []
        seen_names = set()

        # 1. Official Arch / CachyOS checkupdates
        if shutil.which("checkupdates"):
            try:
                res = subprocess.run(["checkupdates"], capture_output=True, text=True, timeout=4)
                lines = [l.strip() for l in res.stdout.split("\n") if l.strip()]
                
                pkg_map = {}
                for line in lines:
                    parts = line.split()
                    if len(parts) >= 4 and parts[2] == "->":
                        pkg_map[parts[0]] = (parts[1], parts[3])

                if pkg_map:
                    pkg_names = list(pkg_map.keys())
                    for i in range(0, len(pkg_names), 80):
                        chunk = pkg_names[i:i+80]
                        info_res = subprocess.run(
                            ["env", "LC_ALL=C", "pacman", "-Si"] + chunk,
                            capture_output=True, text=True, timeout=5
                        )
                        blocks = re.split(r'\n(?=Repository\s*:)', info_res.stdout)
                        for block in blocks:
                            name_match = re.search(r'Name\s*:\s*(.+)', block)
                            repo_match = re.search(r'Repository\s*:\s*(.+)', block)
                            size_match = re.search(r'Download Size\s*:\s*(.+)', block)
                            date_match = re.search(r'Build Date\s*:\s*(.+)', block)

                            if name_match:
                                name = name_match.group(1).strip()
                                if name in pkg_map and name not in seen_names:
                                    seen_names.add(name)
                                    old_v, new_v = pkg_map[name]
                                    repo = repo_match.group(1).strip() if repo_match else "Official"
                                    size = size_match.group(1).strip() if size_match else "-"
                                    date_raw = date_match.group(1).strip() if date_match else "-"
                                    date_clean = re.sub(r'^[A-Za-z]{3}\s+', '', date_raw)
                                    updates.append(PendingUpdate(
                                        name=name,
                                        old_version=old_v,
                                        new_version=new_v,
                                        repo_or_source=repo,
                                        download_size=size,
                                        build_date=date_clean
                                    ))
            except Exception as e:
                logger.warning("checkupdates error: %s", e)

        # 2. AUR Updates
        aur_tool = "yay" if shutil.which("yay") else ("paru" if shutil.which("paru") else None)
        if aur_tool:
            try:
                res = subprocess.run([aur_tool, "-Qua"], capture_output=True, text=True, timeout=4)
                if res.returncode == 0:
                    for line in res.stdout.strip().split("\n"):
                        match = re.match(r'^([^\s]+)\s+([^\s]+)\s+->\s+([^\s]+)(?:\s+\[(.*)\])?', line.strip())
                        if match:
                            name, old_v, new_v, date_rel = match.groups()
                            if name not in seen_names:
                                seen_names.add(name)
                                date_str = f"{date_rel} ago" if date_rel else "AUR"
                                updates.append(PendingUpdate(
                                    name=name,
                                    old_version=old_v,
                                    new_version=new_v,
                                    repo_or_source="AUR",
                                    download_size="Source (AUR)",
                                    build_date=date_str
                                ))
            except Exception as e:
                logger.warning("AUR check error: %s", e)

        # 3. Flatpak Updates with exact download size & version extraction
        if shutil.which("flatpak"):
            try:
                res_f = subprocess.run(
                    ["flatpak", "remote-ls", "--updates", "--columns=name,application,version,download-size"],
                    capture_output=True,
                    text=True,
                    timeout=4
                )
                if res_f.returncode == 0:
                    flines = [l.strip() for l in res_f.stdout.strip().splitlines() if l.strip()]
                    for fline in flines:
                        parts = [p.strip() for p in fline.split("\t") if p.strip()]
                        if len(parts) >= 2:
                            app_name = parts[0]
                            app_id = parts[1]
                            new_v = parts[2] if len(parts) >= 3 and parts[2] else "update"
                            size_raw = parts[3] if len(parts) >= 4 and parts[3] else "Remote binary"
                            size_clean = size_raw.replace("\xa0", " ")
                            
                            if app_id not in seen_names:
                                seen_names.add(app_id)
                                updates.append(PendingUpdate(
                                    name=f"{app_name} ({app_id})",
                                    old_version="installed",
                                    new_version=new_v,
                                    repo_or_source="Flatpak",
                                    download_size=size_clean,
                                    build_date="Flathub"
                                ))
            except Exception as e:
                logger.warning("Flatpak check error: %s", e)

        return updates

    def search_all(self, query: str, limit: int = 80) -> List[PackageItem]:
        q = query.strip().lower()
        results: List[PackageItem] = []
        seen_names = set()
        installed_set = self._get_installed_set()

        # Popular default curated packages when search box is empty
        if not q:
            popular_names = [
                'cachyos-gaming-meta', 'discord', 'steam', 'vlc', 'heroic-games-launcher',
                'obs-studio', 'easyeffects', 'fastfetch', 'btop', 'nvtop', 'firefox',
                'gimp', 'lutris', 'spotify-launcher', 'visual-studio-code-bin', 'alacritty'
            ]
            if self._syncdbs:
                for name in popular_names:
                    for db in self._syncdbs:
                        pkg = db.get_pkg(name)
                        if pkg and pkg.name not in seen_names:
                            seen_names.add(pkg.name)
                            results.append(PackageItem(
                                name=pkg.name,
                                version=pkg.version,
                                repo_or_source=db.name,
                                description=pkg.desc or '',
                                installed=pkg.name in installed_set
                            ))
                            break
            return results

        # 1. Native Ultra-Fast In-Memory Search (pyalpm)
        if self._syncdbs:
            temp_results = []
            for db in self._syncdbs:
                for pkg in db.pkgcache:
                    name_lower = pkg.name.lower()
                    name_match = q in name_lower
                    desc_match = bool(pkg.desc and q in pkg.desc.lower())
                    if name_match or desc_match:
                        score = 0 if name_lower == q else (1 if name_lower.startswith(q) else (2 if name_match else 3))
                        temp_results.append((score, len(pkg.name), db.name, pkg))
                        if len(temp_results) >= limit * 3:
                            break

            # Sort by match score & shortest name
            temp_results.sort(key=lambda x: (x[0], x[1]))
            for _, _, db_name, pkg in temp_results[:limit]:
                if pkg.name not in seen_names:
                    seen_names.add(pkg.name)
                    results.append(PackageItem(
                        name=pkg.name,
                        version=pkg.version,
                        repo_or_source=db_name,
                        description=pkg.desc or '',
                        installed=pkg.name in installed_set
                    ))
        else:
            # Fallback to pacman CLI if pyalpm not registered
            try:
                res = subprocess.run(["pacman", "-Ss", q], capture_output=True, text=True, timeout=4)
                if res.returncode == 0:
                    lines = res.stdout.strip().split("\n")
                    i = 0
                    while i < len(lines) and len(results) < limit:
                        line = lines[i]
                        match = re.match(r"^(\w+)/([^\s]+)\s+([^\s]+)(.*)$", line)
                        if match:
                            repo, name, ver, extra = match.groups()
                            installed = "[installed" in extra
                            desc = lines[i+1].strip() if i+1 < len(lines) else ""
                            if name not in seen_names:
                                seen_names.add(name)
                                results.append(PackageItem(
                                    name=name,
                                    version=ver,
                                    repo_or_source=repo,
                                    description=desc,
                                    installed=installed
                                ))
                            i += 2
                        else:
                            i += 1
            except (OSError, subprocess.SubprocessError) as exc:
                logger.warning("AUR search failed: %s", exc)

        # 2. AUR Search (Append top results if needed)
        aur_tool = "yay" if shutil.which("yay") else ("paru" if shutil.which("paru") else None)
        if aur_tool and len(results) < limit:
            try:
                res = subprocess.run([aur_tool, "-Ss", "--aur", q], capture_output=True, text=True, timeout=4)
                if res.returncode == 0:
                    lines = res.stdout.strip().split("\n")
                    i = 0
                    while i < len(lines) and len(results) < limit:
                        line = lines[i]
                        match = re.match(r"^aur/([^\s]+)\s+([^\s]+)(.*)$", line)
                        if match:
                            name, ver, extra = match.groups()
                            installed = "[installed" in extra or name in installed_set
                            desc = lines[i+1].strip() if i+1 < len(lines) else ""
                            if name not in seen_names:
                                seen_names.add(name)
                                results.append(PackageItem(
                                    name=name,
                                    version=ver,
                                    repo_or_source="AUR",
                                    description=desc,
                                    installed=installed
                                ))
                            i += 2
                        else:
                            i += 1
            except Exception as exc:
                logger.warning("AUR search parsing failed: %s", exc)

        # 3. Flatpak Search (with live installed check)
        if shutil.which("flatpak") and len(results) < limit:
            try:
                installed_flatpaks = set()
                try:
                    res_flist = subprocess.run(["flatpak", "list", "--columns=application"], capture_output=True, text=True, timeout=2)
                    if res_flist.returncode == 0:
                        installed_flatpaks = {line.strip() for line in res_flist.stdout.splitlines() if line.strip()}
                except (OSError, subprocess.SubprocessError) as exc:
                    logger.warning("Could not read installed Flatpaks for search: %s", exc)

                res = subprocess.run(["flatpak", "search", "--columns=name,application,version,description", q], capture_output=True, text=True, timeout=3)
                if res.returncode == 0:
                    lines = [l for l in res.stdout.strip().split("\n") if l.strip()]
                    for line in lines:
                        parts = [p.strip() for p in line.split("\t") if p.strip()]
                        if len(parts) >= 2:
                            name = parts[1]
                            ver = parts[2] if len(parts) >= 3 else "latest"
                            desc = parts[3] if len(parts) >= 4 else (parts[0] if parts else "")
                            if name not in seen_names:
                                seen_names.add(name)
                                results.append(PackageItem(
                                    name=name,
                                    version=ver,
                                    repo_or_source="Flatpak",
                                    description=desc,
                                    installed=(name in installed_flatpaks)
                                ))
                                if len(results) >= limit:
                                    break
            except (OSError, subprocess.SubprocessError) as exc:
                logger.warning("Flatpak search failed: %s", exc)

        return results[:limit]

    def get_update_command(self, manager: str) -> str:
        aur_tool = "yay" if shutil.which("yay") else ("paru" if shutil.which("paru") else "pacman")
        
        if manager == "all":
            cmds = []
            if shutil.which(aur_tool):
                cmds.append(f"{aur_tool} -Syu --noconfirm")
            else:
                cmds.append("sudo pacman -Syu --noconfirm")
            if shutil.which("flatpak"):
                cmds.append("flatpak update -y")
            return " && ".join(cmds)
        elif manager == "pacman":
            return "sudo pacman -Syu --noconfirm"
        elif manager == "yay":
            return "yay -Syu --noconfirm"
        elif manager == "paru":
            return "paru -Syu --noconfirm"
        elif manager == "flatpak":
            return "flatpak update -y"
        elif manager == "rate_mirrors":
            return "sudo cachyos-rate-mirrors"
        return "sudo pacman -Syu --noconfirm"

    def get_install_command(self, pkg: PackageItem) -> str:
        safe_name = shlex.quote(pkg.name)
        if pkg.repo_or_source.lower() == "flatpak":
            return f"flatpak install flathub {safe_name} -y"
        elif pkg.repo_or_source.lower() == "aur":
            aur = "yay" if shutil.which("yay") else "paru"
            return f"{aur} -S --noconfirm {safe_name}"
        else:
            return f"sudo pacman -S --needed --noconfirm {safe_name}"

    def get_single_update_command(self, update: PendingUpdate) -> str:
        if update.repo_or_source.lower() == "flatpak":
            match = re.search(r'\(([^)]+)\)', update.name)
            app_id = match.group(1) if match else update.name
            safe_id = shlex.quote(app_id)
            return f"flatpak update {safe_id} -y"
        elif update.repo_or_source.lower() == "aur":
            aur = "yay" if shutil.which("yay") else "paru"
            safe_name = shlex.quote(update.name)
            return f"{aur} -S --noconfirm {safe_name}"
        else:
            safe_name = shlex.quote(update.name)
            return f"sudo pacman -S --noconfirm {safe_name}"

    def get_remove_command(self, pkg: PackageItem) -> str:
        safe_name = shlex.quote(pkg.name)
        if pkg.repo_or_source.lower() == "flatpak":
            return f"flatpak uninstall -y {safe_name}"
        elif pkg.repo_or_source.lower() == "aur":
            aur = "yay" if shutil.which("yay") else ("paru" if shutil.which("paru") else "pacman")
            return f"{aur} -Rns --noconfirm {safe_name}"
        else:
            return f"sudo pacman -Rns --noconfirm {safe_name}"

    def get_local_install_command(self, file_path: str) -> str:
        safe_path = shlex.quote(file_path)
        return f"sudo pacman -U --noconfirm {safe_path}"
