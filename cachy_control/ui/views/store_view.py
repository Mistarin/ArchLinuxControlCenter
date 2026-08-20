"""
App Store View: Curated Linux Workaround Apps & Software Catalog.
Supports both Responsive Grid View and Sleek Banner List View,
with an above-modal popup dialog for source selection and live command inspection.
"""

from typing import List, Dict
import os
import shutil
import shlex
import subprocess

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QGridLayout, QScrollArea, QComboBox, QFrame, QApplication, QDialog
)
from PyQt6.QtCore import Qt, QSize, QTimer, pyqtSignal
from PyQt6.QtGui import QIcon, QPixmap, QCursor

from cachy_control.core.service_registry import ServiceRegistry
from cachy_control.ui.components.sharp_card import SharpCard
from cachy_control.ui.components.confirm_dialog import confirm_destructive_action
from cachy_control.ui.components.sharp_button import SharpButton
from cachy_control.ui.components.section_badge import SectionBadge
from cachy_control.ui.icons import get_pixmap, get_icon
from cachy_control.ui.theme import THEMES

# Helper to fetch real system/flatpak desktop icons
def get_app_icon(icon_names: List[str], fallback_icon: str = "package", size: int = 40, color: str = None) -> QPixmap:
    for name in icon_names:
        # 1. System Theme
        icon = QIcon.fromTheme(name)
        if not icon.isNull():
            pix = icon.pixmap(QSize(size, size))
            if not pix.isNull():
                return pix

        # 2. System and Flatpak directories
        search_dirs = [
            "/usr/share/pixmaps",
            "/usr/share/icons/hicolor/scalable/apps",
            "/usr/share/icons/hicolor/256x256/apps",
            "/usr/share/icons/hicolor/128x128/apps",
            "/usr/share/icons/hicolor/64x64/apps",
            "/usr/share/icons/hicolor/48x48/apps",
            "/var/lib/flatpak/exports/share/icons/hicolor/scalable/apps",
            "/var/lib/flatpak/exports/share/icons/hicolor/128x128/apps",
            "/var/lib/flatpak/exports/share/icons/hicolor/64x64/apps",
            os.path.expanduser("~/.local/share/flatpak/exports/share/icons/hicolor/128x128/apps"),
            os.path.expanduser("~/.local/share/icons/hicolor/128x128/apps"),
        ]
        for d in search_dirs:
            for ext in [".png", ".svg"]:
                p = os.path.join(d, name + ext)
                if os.path.exists(p):
                    ic = QIcon(p)
                    if not ic.isNull():
                        pix = ic.pixmap(QSize(size, size))
                        if not pix.isNull():
                            return pix
                            
    if not color:
        try:
            t_key = ServiceRegistry.get().settings.get("theme", "light")
            color = THEMES.get(t_key, THEMES["light"])["text"]
        except Exception:
            color = "#111111"
    return get_pixmap(fallback_icon, size=size, color=color)

CURATED_APPS = [
    # Communication & Workaround Clients
    {
        "id": "vesktop",
        "name": "Discord (Vesktop - Recommended)",
        "category": "Communication",
        "icon_names": ["vesktop", "vencord", "discord"],
        "fallback_icon": "external_link",
        "desc": "Recommended Discord client with native Wayland screen share audio & built-in Vencord.",
        "sources": [
            {"label": "AUR: vesktop-bin (Recommended)", "type": "aur", "pkg": "vesktop-bin"},
            {"label": "Flatpak: dev.vencord.Vesktop", "type": "flatpak", "pkg": "dev.vencord.Vesktop"}
        ],
        "check_bin": ["vesktop", "vencord"]
    },
    {
        "id": "discord",
        "name": "Discord (Official Alternative)",
        "category": "Communication",
        "icon_names": ["discord", "com.discordapp.Discord"],
        "fallback_icon": "external_link",
        "desc": "Stock Discord client (may have Wayland audio screenshare limitations).",
        "sources": [
            {"label": "Official Repo (pacman: discord)", "type": "pacman", "pkg": "discord"},
            {"label": "Flatpak (com.discordapp.Discord)", "type": "flatpak", "pkg": "com.discordapp.Discord"}
        ],
        "check_bin": ["discord"]
    },
    {
        "id": "caprine",
        "name": "Caprine (Messenger)",
        "category": "Communication",
        "icon_names": ["caprine", "facebook-messenger", "messenger"],
        "fallback_icon": "external_link",
        "desc": "Elegant Facebook Messenger desktop client with dark mode & privacy controls.",
        "sources": [
            {"label": "AUR (yay: caprine-bin)", "type": "aur", "pkg": "caprine-bin"},
            {"label": "Flatpak (com.sindresorhus.Caprine)", "type": "flatpak", "pkg": "com.sindresorhus.Caprine"}
        ],
        "check_bin": ["caprine"]
    },
    {
        "id": "cohesion",
        "name": "Cohesion (Notion)",
        "category": "Productivity",
        "icon_names": ["cohesion", "notion-app", "notion"],
        "fallback_icon": "code",
        "desc": "Lightweight native desktop wrapper for Notion workspace.",
        "sources": [
            {"label": "AUR (yay: cohesion)", "type": "aur", "pkg": "cohesion"},
            {"label": "Flatpak (com.github.bjarneo.cohesion)", "type": "flatpak", "pkg": "com.github.bjarneo.cohesion"}
        ],
        "check_bin": ["cohesion"]
    },
    {
        "id": "telegram",
        "name": "Telegram Desktop",
        "category": "Communication",
        "icon_names": ["telegram-desktop", "telegram", "org.telegram.desktop"],
        "fallback_icon": "external_link",
        "desc": "Fast and secure desktop messaging client.",
        "sources": [
            {"label": "Official Repo (pacman: telegram-desktop)", "type": "pacman", "pkg": "telegram-desktop"},
            {"label": "Flatpak (org.telegram.desktop)", "type": "flatpak", "pkg": "org.telegram.desktop"}
        ],
        "check_bin": ["telegram-desktop"]
    },
    {
        "id": "signal",
        "name": "Signal Desktop",
        "category": "Communication",
        "icon_names": ["signal-desktop", "signal", "org.signal.Signal"],
        "fallback_icon": "shield",
        "desc": "Private end-to-end encrypted messaging application.",
        "sources": [
            {"label": "Official Repo (pacman: signal-desktop)", "type": "pacman", "pkg": "signal-desktop"},
            {"label": "Flatpak (org.signal.Signal)", "type": "flatpak", "pkg": "org.signal.Signal"}
        ],
        "check_bin": ["signal-desktop"]
    },

    # Gaming & Compatibility Tools
    {
        "id": "heroic",
        "name": "Heroic Games Launcher",
        "category": "Gaming",
        "icon_names": ["heroic", "com.heroicgameslauncher.hgl", "heroicgameslauncher"],
        "fallback_icon": "gaming",
        "desc": "Native launcher for Epic Games, GOG & Amazon games via Proton/Wine.",
        "sources": [
            {"label": "Official / Extra (pacman: heroic-games-launcher-bin)", "type": "pacman", "pkg": "heroic-games-launcher-bin"},
            {"label": "Flatpak (com.heroicgameslauncher.hgl)", "type": "flatpak", "pkg": "com.heroicgameslauncher.hgl"}
        ],
        "check_bin": ["heroic"]
    },
    {
        "id": "protonplus",
        "name": "ProtonPlus",
        "category": "Gaming",
        "icon_names": ["protonplus", "com.vysp3r.ProtonPlus"],
        "fallback_icon": "sliders",
        "desc": "Manage Wine-GE, Proton-GE, DXVK and VKD3D runners across Steam & Heroic.",
        "sources": [
            {"label": "AUR (yay: protonplus)", "type": "aur", "pkg": "protonplus"},
            {"label": "Flatpak (com.vysp3r.ProtonPlus)", "type": "flatpak", "pkg": "com.vysp3r.ProtonPlus"}
        ],
        "check_bin": ["protonplus"]
    },
    {
        "id": "bottles",
        "name": "Bottles",
        "category": "Gaming",
        "icon_names": ["com.usebottles.bottles", "bottles"],
        "fallback_icon": "gaming",
        "desc": "Run Windows software & games in isolated, customized Wine prefixes.",
        "sources": [
            {"label": "Flatpak (com.usebottles.bottles)", "type": "flatpak", "pkg": "com.usebottles.bottles"},
            {"label": "AUR (yay: bottles)", "type": "aur", "pkg": "bottles"}
        ],
        "check_bin": ["bottles"]
    },
    {
        "id": "lutris",
        "name": "Lutris",
        "category": "Gaming",
        "icon_names": ["lutris", "net.lutris.Lutris"],
        "fallback_icon": "gaming",
        "desc": "Open gaming platform to install and manage games from all sources.",
        "sources": [
            {"label": "Official Repo (pacman: lutris)", "type": "pacman", "pkg": "lutris"},
            {"label": "Flatpak (net.lutris.Lutris)", "type": "flatpak", "pkg": "net.lutris.Lutris"}
        ],
        "check_bin": ["lutris"]
    },
    {
        "id": "mangohud",
        "name": "MangoHud & Goverlay",
        "category": "Gaming",
        "icon_names": ["mangohud", "goverlay", "io.github.benjamimgois.goverlay"],
        "fallback_icon": "cpu",
        "desc": "Vulkan & OpenGL performance overlay HUD and graphical configuration tool.",
        "sources": [
            {"label": "Official Repo (pacman: mangohud goverlay)", "type": "pacman", "pkg": "mangohud goverlay"}
        ],
        "check_bin": ["mangohud", "goverlay"]
    },
    {
        "id": "steam",
        "name": "Steam",
        "category": "Gaming",
        "icon_names": ["steam", "com.valvesoftware.Steam"],
        "fallback_icon": "gaming",
        "desc": "Valve digital distribution gaming platform with native Proton support.",
        "sources": [
            {"label": "Official Repo (pacman: steam)", "type": "pacman", "pkg": "steam"},
            {"label": "Flatpak (com.valvesoftware.Steam)", "type": "flatpak", "pkg": "com.valvesoftware.Steam"}
        ],
        "check_bin": ["steam"]
    },

    # Audio & Media Tools
    {
        "id": "easyeffects",
        "name": "EasyEffects",
        "category": "Audio & Media",
        "icon_names": ["easyeffects", "com.github.wwmm.easyeffects"],
        "fallback_icon": "volume",
        "desc": "System-wide PipeWire audio effects, parametric EQ, and loudness limiter.",
        "sources": [
            {"label": "Official Repo (pacman: easyeffects)", "type": "pacman", "pkg": "easyeffects"},
            {"label": "Flatpak (com.github.wwmm.easyeffects)", "type": "flatpak", "pkg": "com.github.wwmm.easyeffects"}
        ],
        "check_bin": ["easyeffects"]
    },
    {
        "id": "obs",
        "name": "OBS Studio",
        "category": "Audio & Media",
        "icon_names": ["obs", "obs-studio", "com.obsproject.Studio"],
        "fallback_icon": "camera",
        "desc": "Professional video recording and live streaming software.",
        "sources": [
            {"label": "Official Repo (pacman: obs-studio)", "type": "pacman", "pkg": "obs-studio"},
            {"label": "Flatpak (com.obsproject.Studio)", "type": "flatpak", "pkg": "com.obsproject.Studio"}
        ],
        "check_bin": ["obs"]
    },
    {
        "id": "spotify",
        "name": "Spotify",
        "category": "Audio & Media",
        "icon_names": ["spotify", "spotify-client", "com.spotify.Client"],
        "fallback_icon": "volume",
        "desc": "Music streaming platform with native Linux integration.",
        "sources": [
            {"label": "Official Repo (pacman: spotify-launcher)", "type": "pacman", "pkg": "spotify-launcher"},
            {"label": "Flatpak (com.spotify.Client)", "type": "flatpak", "pkg": "com.spotify.Client"},
            {"label": "AUR (yay: spotify)", "type": "aur", "pkg": "spotify"}
        ],
        "check_bin": ["spotify", "spotify-launcher"]
    },
    {
        "id": "vlc",
        "name": "VLC Media Player",
        "category": "Audio & Media",
        "icon_names": ["vlc", "org.videolan.VLC"],
        "fallback_icon": "play",
        "desc": "Universal media player supporting nearly all audio & video codecs.",
        "sources": [
            {"label": "Official Repo (pacman: vlc)", "type": "pacman", "pkg": "vlc"},
            {"label": "Flatpak (org.videolan.VLC)", "type": "flatpak", "pkg": "org.videolan.VLC"}
        ],
        "check_bin": ["vlc"]
    },

    # Utilities & Local Tools
    {
        "id": "localsend",
        "name": "LocalSend",
        "category": "Utilities",
        "icon_names": ["localsend", "localsend_app", "org.localsend.localsend_app"],
        "fallback_icon": "wifi",
        "desc": "Open-source AirDrop alternative to share files locally without cloud/internet.",
        "sources": [
            {"label": "Official / Extra (pacman: localsend_app)", "type": "pacman", "pkg": "localsend_app"},
            {"label": "Flatpak (org.localsend.localsend_app)", "type": "flatpak", "pkg": "org.localsend.localsend_app"}
        ],
        "check_bin": ["localsend_app", "localsend"]
    },
    {
        "id": "btrfs_assistant",
        "name": "Btrfs Assistant",
        "category": "Utilities",
        "icon_names": ["btrfs-assistant", "btrfs-assistant-launcher"],
        "fallback_icon": "storage",
        "desc": "GUI management for Btrfs subvolumes, Snapper snapshots and maintenance.",
        "sources": [
            {"label": "Official Repo (pacman: btrfs-assistant)", "type": "pacman", "pkg": "btrfs-assistant"}
        ],
        "check_bin": ["btrfs-assistant"]
    },
    {
        "id": "vscode",
        "name": "Visual Studio Code",
        "category": "Productivity",
        "icon_names": ["code", "visual-studio-code", "com.visualstudio.code"],
        "fallback_icon": "code",
        "desc": "Code editor with extensions, debugging, Git integration and AI tooling.",
        "sources": [
            {"label": "AUR (yay: visual-studio-code-bin)", "type": "aur", "pkg": "visual-studio-code-bin"},
            {"label": "Official Open-Source (pacman: code)", "type": "pacman", "pkg": "code"},
            {"label": "Flatpak (com.visualstudio.code)", "type": "flatpak", "pkg": "com.visualstudio.code"}
        ],
        "check_bin": ["code"]
    },
    {
        "id": "brave",
        "name": "Brave Browser",
        "category": "Utilities",
        "icon_names": ["brave-browser", "brave", "com.brave.Browser"],
        "fallback_icon": "network",
        "desc": "Privacy-focused web browser with built-in ad and tracker blocker.",
        "sources": [
            {"label": "AUR (yay: brave-bin)", "type": "aur", "pkg": "brave-bin"},
            {"label": "Flatpak (com.brave.Browser)", "type": "flatpak", "pkg": "com.brave.Browser"}
        ],
        "check_bin": ["brave", "brave-browser"]
    }
]

class AppInstallDialog(QDialog):
    """Above-modal installation popup dialog."""
    def __init__(self, app_data: dict, is_installed: bool, parent: QWidget = None):
        super().__init__(parent)
        self.app_data = app_data
        self.is_installed = is_installed
        self.services = ServiceRegistry.get()

        self.setWindowTitle(f"Install {app_data['name']}")
        self.setModal(True)
        self.parent_view = parent
        self.setFixedSize(520, 320)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        theme_key = self.services.settings.get("theme", "light")
        t = THEMES.get(theme_key, THEMES["light"])
        self.setStyleSheet(f"""
            AppInstallDialog {{
                background-color: {t['card_bg']};
                border: 2px solid {t['border']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Row
        h_row = QHBoxLayout()
        h_row.setSpacing(14)

        icon_lbl = QLabel()
        icon_lbl.setFixedSize(44, 44)
        pix = get_app_icon(app_data.get("icon_names", []), app_data.get("fallback_icon", "package"), size=44)
        icon_lbl.setPixmap(pix.scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        h_row.addWidget(icon_lbl)

        t_box = QVBoxLayout()
        t_box.setSpacing(3)
        t_row = QHBoxLayout()
        t_row.setSpacing(8)
        title_lbl = QLabel(app_data["name"])
        title_lbl.setStyleSheet(f"font-size: 16px; font-weight: 800; color: {t['text']};")
        t_row.addWidget(title_lbl)

        cat_badge = QLabel(f" {app_data['category']} ")
        cat_badge.setStyleSheet(f"font-size: 10px; font-weight: 700; color: {t['subtext']}; border: 1px solid {t['border']}; padding: 1px 5px;")
        t_row.addWidget(cat_badge)
        t_row.addStretch()
        t_box.addLayout(t_row)

        desc_lbl = QLabel(app_data["desc"])
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(f"font-size: 11px; color: {t['subtext']};")
        t_box.addWidget(desc_lbl)
        h_row.addLayout(t_box, 1)

        close_btn = SharpButton("", icon_name="cross", variant="outline")
        close_btn.setFixedSize(24, 24)
        close_btn.clicked.connect(self.reject)
        h_row.addWidget(close_btn)
        layout.addLayout(h_row)

        # Source Selection Row
        src_row = QHBoxLayout()
        src_row.setSpacing(10)
        src_title = QLabel("Choose Source:")
        src_title.setStyleSheet(f"font-size: 12px; font-weight: 700; color: {t['text']};")
        src_row.addWidget(src_title)

        self.source_combo = QComboBox()
        self.source_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {t['input_bg']};
                border: 1px solid {t['border']};
                color: {t['text']};
                padding: 6px 10px;
                font-size: 12px;
                font-weight: 600;
            }}
        """)
        best_idx = 0
        for idx, src in enumerate(app_data.get("sources", [])):
            self.source_combo.addItem(src["label"], src)
            stype = src.get("type", "")
            pkg = src.get("pkg", "")
            if is_installed:
                if stype == "flatpak" and self.services.packages.is_source_installed(stype, pkg):
                    best_idx = idx
                elif stype in ("pacman", "aur") and self.services.packages.is_source_installed(stype, pkg):
                    best_idx = idx
        self.source_combo.setCurrentIndex(best_idx)
        self.source_combo.currentIndexChanged.connect(self._update_command_preview)
        src_row.addWidget(self.source_combo, 1)
        layout.addLayout(src_row)

        # Command Preview Box
        cmd_row = QHBoxLayout()
        cmd_row.setSpacing(8)

        self.cmd_box = QLabel()
        self.cmd_box.setTextFormat(Qt.TextFormat.PlainText)
        self.cmd_box.setStyleSheet(f"""
            QLabel {{
                background-color: {t['input_bg']};
                color: {t['text']};
                border: 1px solid {t['border']};
                font-family: 'JetBrains Mono', 'Fira Code', monospace;
                font-size: 11px;
                font-weight: 600;
                padding: 6px 10px;
            }}
        """)
        cmd_row.addWidget(self.cmd_box, 1)

        copy_btn = SharpButton("", icon_name="external_link", variant="outline")
        copy_btn.setToolTip("Copy command to clipboard")
        copy_btn.setFixedSize(30, 30)
        copy_btn.clicked.connect(self._copy_command)
        cmd_row.addWidget(copy_btn)
        layout.addLayout(cmd_row)

        layout.addStretch()

        # Bottom Actions Row
        b_row = QHBoxLayout()
        b_row.setSpacing(10)

        if is_installed:
            self.uninstall_action_btn = SharpButton("Uninstall / Remove", icon_name="trash", variant="danger")
            self.uninstall_action_btn.clicked.connect(self._do_uninstall)
            b_row.addWidget(self.uninstall_action_btn)

        b_row.addStretch()

        cancel_btn = SharpButton("Close", icon_name="cross", variant="outline")
        cancel_btn.clicked.connect(self.reject)
        b_row.addWidget(cancel_btn)

        act_text = "Reinstall Application" if is_installed else "Install Application"
        self.install_action_btn = SharpButton(act_text, icon_name="download", variant="primary")
        self.install_action_btn.clicked.connect(self._do_install)
        b_row.addWidget(self.install_action_btn)

        layout.addLayout(b_row)
        self._update_command_preview()

    def _get_current_command(self) -> str:
        src = self.source_combo.currentData()
        if not src:
            return ""
        stype = src.get("type", "pacman")
        pkg = src.get("pkg", "")

        if stype == "flatpak":
            return f"flatpak install flathub {shlex.quote(pkg)} -y"
        elif stype == "aur":
            aur = "yay" if shutil.which("yay") else ("paru" if shutil.which("paru") else "pacman")
            return f"{aur} -S --noconfirm {shlex.quote(pkg)}"
        else: # pacman
            return f"sudo pacman -S --needed --noconfirm {shlex.quote(pkg)}"

    def _update_command_preview(self):
        cmd = self._get_current_command()
        self.cmd_box.setText(f"> {cmd}")

    def _copy_command(self):
        cmd = self._get_current_command()
        cb = QApplication.clipboard()
        if cb:
            cb.setText(cmd)

    def _get_current_uninstall_command(self) -> str:
        src = self.source_combo.currentData()
        if not src:
            return ""
        stype = src.get("type", "pacman")
        pkg = src.get("pkg", "")
        if stype == "flatpak":
            return f"flatpak uninstall -y {shlex.quote(pkg)}"
        elif stype == "aur":
            aur = "yay" if shutil.which("yay") else ("paru" if shutil.which("paru") else "pacman")
            return f"{aur} -Rns --noconfirm {shlex.quote(pkg)}"
        else:
            return f"sudo pacman -Rns --noconfirm {shlex.quote(pkg)}"

    def _do_uninstall(self):
        cmd = self._get_current_uninstall_command()
        if not cmd:
            return
        if not confirm_destructive_action(
            self,
            f"Uninstall {self.app_data['name']}",
            f"Are you sure you want to completely remove {self.app_data['name']} and its unneeded dependencies?\n\nCommand: {cmd}",
            "Yes, Uninstall"
        ):
            return
        self.accept()
        parent_view = self.parent_view
        def on_done(code):
            if parent_view and hasattr(parent_view, '_refresh_all_cards'):
                parent_view._refresh_all_cards()
            elif parent_view and hasattr(parent_view, '_render_view'):
                parent_view._render_view()
        self.services.runner.run_command(cmd, on_finish=on_done)

    def _do_install(self):
        cmd = self._get_current_command()
        self.accept()
        if cmd:
            parent_view = self.parent_view
            def on_done(code):
                if parent_view and hasattr(parent_view, '_refresh_all_cards'):
                    parent_view._refresh_all_cards()
                elif parent_view and hasattr(parent_view, '_render_view'):
                    parent_view._render_view()
            self.services.runner.run_command(cmd, on_finish=on_done)

class AppGridCard(QFrame):
    """Clean modern compact card for 3-column Grid View."""
    clicked = pyqtSignal(dict, bool)

    def __init__(self, app_data: dict, installed_sources: dict, parent: QWidget = None):
        super().__init__(parent)
        self.app_data = app_data
        self.services = ServiceRegistry.get()
        self.installed_sources = installed_sources
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        theme_key = self.services.settings.get("theme", "light")
        t = THEMES.get(theme_key, THEMES["light"])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Top row: Icon & Status
        top_row = QHBoxLayout()
        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(44, 44)
        pix = get_app_icon(app_data.get("icon_names", []), app_data.get("fallback_icon", "package"), size=44)
        self.icon_lbl.setPixmap(pix.scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        top_row.addWidget(self.icon_lbl)
        top_row.addStretch()

        self.status_lbl = QLabel()
        self.status_lbl.setStyleSheet("font-size: 11px; font-weight: 700;")
        top_row.addWidget(self.status_lbl)
        layout.addLayout(top_row)

        # Name + Category
        name_row = QHBoxLayout()
        self.name_lbl = QLabel(app_data["name"])
        name_row.addWidget(self.name_lbl)

        self.cat_badge = QLabel(f" {app_data['category']} ")
        name_row.addWidget(self.cat_badge)
        name_row.addStretch()
        layout.addLayout(name_row)

        # Short Description
        self.desc_lbl = QLabel(app_data["desc"])
        self.desc_lbl.setWordWrap(True)
        layout.addWidget(self.desc_lbl)

        layout.addStretch()

        # Action Button
        self.action_btn = SharpButton("Install", icon_name="download", variant="primary")
        self.action_btn.setFixedHeight(28)
        self.action_btn.clicked.connect(self._on_action)
        layout.addWidget(self.action_btn)

        self.apply_theme_style(theme_key)
        self.refresh_status(theme_key)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_action()
        super().mousePressEvent(event)

    def _on_action(self):
        self.clicked.emit(self.app_data, self._check_installed())

    def apply_theme_style(self, theme_key: str = None):
        if not theme_key:
            theme_key = self.services.settings.get("theme", "light")
        t = THEMES.get(theme_key, THEMES["light"])
        self.setStyleSheet(f"""
            AppGridCard {{
                background-color: {t["card_bg"]};
                border: 1px solid {t["border"]};
                border-radius: 0px;
            }}
            AppGridCard:hover {{
                border-color: {t["accent"]};
                background-color: {t["nav_hover"]};
            }}
        """)
        self.name_lbl.setStyleSheet(f"font-size: 13px; font-weight: 800; color: {t['text']};")
        self.cat_badge.setStyleSheet(f"font-size: 9px; font-weight: 700; color: {t['subtext']}; border: 1px solid {t['border']}; padding: 1px 4px;")
        self.desc_lbl.setStyleSheet(f"font-size: 11px; color: {t['subtext']}; min-height: 28px;")
        self.action_btn.apply_style(theme_key)
        self.refresh_status(theme_key)

    def refresh_status(self, theme_key: str = None):
        if not theme_key:
            theme_key = self.services.settings.get("theme", "light")
        t = THEMES.get(theme_key, THEMES["light"])
        is_inst = self._check_installed()
        if is_inst:
            self.status_lbl.setText("✓ Installed")
            self.status_lbl.setStyleSheet(f"color: {t['success']}; font-weight: 700; font-size: 11px;")
            self.action_btn.set_clean_text("Manage")
            self.action_btn.variant = "outline"
            self.action_btn.apply_style(theme_key)
        else:
            self.status_lbl.setText("Available")
            self.status_lbl.setStyleSheet(f"color: {t['muted']}; font-weight: 600; font-size: 11px;")
            self.action_btn.set_clean_text("Install")
            self.action_btn.variant = "primary"
            self.action_btn.apply_style(theme_key)

    def _check_installed(self) -> bool:
        for b in self.app_data.get("check_bin", []):
            if shutil.which(b):
                return True
        for s in self.app_data.get("sources", []):
            if s.get("type") == "flatpak" and s.get("pkg", "") in self.installed_sources["flatpak"]:
                return True
            elif s.get("type") in ("pacman", "aur") and s.get("pkg", "") in self.installed_sources["arch"]:
                return True
        return False

class AppBannerCard(QFrame):
    """Horizontal banner card for List View."""
    clicked = pyqtSignal(dict, bool)

    def __init__(self, app_data: dict, installed_sources: dict, parent: QWidget = None):
        super().__init__(parent)
        self.app_data = app_data
        self.services = ServiceRegistry.get()
        self.installed_sources = installed_sources
        self.setFixedHeight(64)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        theme_key = self.services.settings.get("theme", "light")
        t = THEMES.get(theme_key, THEMES["light"])

        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(14)

        self.icon_lbl = QLabel()
        self.icon_lbl.setFixedSize(40, 40)
        pix = get_app_icon(app_data.get("icon_names", []), app_data.get("fallback_icon", "package"), size=40)
        self.icon_lbl.setPixmap(pix.scaled(40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        layout.addWidget(self.icon_lbl)

        info_box = QVBoxLayout()
        info_box.setSpacing(2)
        
        t_row = QHBoxLayout()
        t_row.setSpacing(8)
        self.title_lbl = QLabel(app_data["name"])
        t_row.addWidget(self.title_lbl)

        self.cat_badge = QLabel(f" {app_data['category']} ")
        t_row.addWidget(self.cat_badge)
        t_row.addStretch()
        info_box.addLayout(t_row)

        self.desc_lbl = QLabel(app_data["desc"])
        info_box.addWidget(self.desc_lbl)
        layout.addLayout(info_box, 1)

        self.status_lbl = QLabel()
        self.status_lbl.setStyleSheet("font-size: 11px; font-weight: 700;")
        layout.addWidget(self.status_lbl)

        self.action_btn = SharpButton("Install", icon_name="download", variant="primary")
        self.action_btn.setMinimumWidth(85)
        self.action_btn.setFixedHeight(28)
        self.action_btn.clicked.connect(self._on_action)
        layout.addWidget(self.action_btn)

        self.apply_theme_style(theme_key)
        self.refresh_status(theme_key)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._on_action()
        super().mousePressEvent(event)

    def _on_action(self):
        self.clicked.emit(self.app_data, self._check_installed())

    def apply_theme_style(self, theme_key: str = None):
        if not theme_key:
            theme_key = self.services.settings.get("theme", "light")
        t = THEMES.get(theme_key, THEMES["light"])
        self.setStyleSheet(f"""
            AppBannerCard {{
                background-color: {t["card_bg"]};
                border: 1px solid {t["border"]};
                border-radius: 0px;
            }}
            AppBannerCard:hover {{
                border-color: {t["accent"]};
                background-color: {t["nav_hover"]};
            }}
        """)
        self.title_lbl.setStyleSheet(f"font-size: 13px; font-weight: 800; color: {t['text']};")
        self.cat_badge.setStyleSheet(f"font-size: 9px; font-weight: 700; color: {t['subtext']}; border: 1px solid {t['border']}; padding: 1px 4px;")
        self.desc_lbl.setStyleSheet(f"font-size: 11px; color: {t['subtext']};")
        self.action_btn.apply_style(theme_key)
        self.refresh_status(theme_key)

    def refresh_status(self, theme_key: str = None):
        if not theme_key:
            theme_key = self.services.settings.get("theme", "light")
        t = THEMES.get(theme_key, THEMES["light"])
        is_inst = self._check_installed()
        if is_inst:
            self.status_lbl.setText("✓ Installed")
            self.status_lbl.setStyleSheet(f"color: {t['success']}; font-weight: 700; font-size: 11px;")
            self.action_btn.set_clean_text("Manage")
            self.action_btn.variant = "outline"
            self.action_btn.apply_style(theme_key)
        else:
            self.status_lbl.setText("Available")
            self.status_lbl.setStyleSheet(f"color: {t['muted']}; font-weight: 600; font-size: 11px;")
            self.action_btn.set_clean_text("Install")
            self.action_btn.variant = "primary"
            self.action_btn.apply_style(theme_key)

    def _check_installed(self) -> bool:
        for b in self.app_data.get("check_bin", []):
            if shutil.which(b):
                return True
        for s in self.app_data.get("sources", []):
            if s.get("type") == "flatpak" and s.get("pkg", "") in self.installed_sources["flatpak"]:
                return True
            elif s.get("type") in ("pacman", "aur") and s.get("pkg", "") in self.installed_sources["arch"]:
                return True
        return False

class StoreView(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.services = ServiceRegistry.get()
        self.installed_sources = self.services.packages.get_installed_sources(refresh=True)
        self.view_mode = self.services.settings.get("store_view_mode", "grid") # "grid" or "list"
        self.cards = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        # Header
        header = QHBoxLayout()
        header.addWidget(SectionBadge("store", "CURATED APP STORE & WORKAROUND HUBS"))
        header.addStretch()

        self.refresh_btn = SharpButton("Refresh Status", icon_name="refresh", variant="outline")
        self.refresh_btn.clicked.connect(self._refresh_all_cards)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        # Search and Category Filters Bar
        filter_card = SharpCard("Discover & Filter Software", "Curated selection of essential Linux apps, workaround tools, and game runners")
        f_layout = QVBoxLayout()
        f_layout.setSpacing(10)

        # Top Filter Row: Search Input + View Mode Switchers
        s_row = QHBoxLayout()
        s_row.setSpacing(10)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter store apps by name, description, or category (e.g. vesktop, notion, wine, pipewire)...")
        self.search_input.textChanged.connect(self._filter_apps)
        s_row.addWidget(self.search_input, 1)

        # View Mode Toggle Buttons
        self.grid_mode_btn = SharpButton("Grid", icon_name="dashboard", variant="secondary" if self.view_mode == "grid" else "outline")
        self.grid_mode_btn.setToolTip("Switch to 3-column Grid View")
        self.grid_mode_btn.clicked.connect(lambda: self._set_view_mode("grid"))
        s_row.addWidget(self.grid_mode_btn)

        self.list_mode_btn = SharpButton("List", icon_name="sliders", variant="secondary" if self.view_mode == "list" else "outline")
        self.list_mode_btn.setToolTip("Switch to Banner List View")
        self.list_mode_btn.clicked.connect(lambda: self._set_view_mode("list"))
        s_row.addWidget(self.list_mode_btn)

        f_layout.addLayout(s_row)

        # Category Filter Row
        cat_row = QHBoxLayout()
        cat_row.setSpacing(8)
        self.categories = ["All", "Communication", "Gaming", "Audio & Media", "Productivity", "Utilities"]
        self.subtab_configs = [(cat, cat) for cat in self.categories]
        self.active_sub_tab = "All"
        self.cat_buttons = []
        self.selected_category = "All"

        for cat in self.categories:
            btn = SharpButton(cat, variant="secondary" if cat == "All" else "outline")
            btn.clicked.connect(lambda _, c=cat: self._on_category_clicked(c))
            cat_row.addWidget(btn)
            self.cat_buttons.append((cat, btn))

        cat_row.addStretch()
        f_layout.addLayout(cat_row)
        filter_card.add_layout(f_layout)
        layout.addWidget(filter_card)

        # Scroll Area for Content
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.container = QWidget()
        self.c_layout = QVBoxLayout(self.container)
        self.c_layout.setContentsMargins(0, 0, 0, 0)
        self.c_layout.setSpacing(10)

        self._render_view()

        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

    def apply_theme_style(self, theme_key: str = None):
        if not theme_key:
            theme_key = self.services.settings.get("theme", "light")
        for card in self.cards:
            card.apply_theme_style(theme_key)
        for c_name, btn in self.cat_buttons:
            btn.variant = "secondary" if c_name == self.selected_category else "outline"
            btn.apply_style(theme_key)
        self.grid_mode_btn.variant = "secondary" if self.view_mode == "grid" else "outline"
        self.grid_mode_btn.apply_style(theme_key)
        self.list_mode_btn.variant = "secondary" if self.view_mode == "list" else "outline"
        self.list_mode_btn.apply_style(theme_key)
        self.refresh_btn.apply_style(theme_key)

    def _set_view_mode(self, mode: str):
        self.view_mode = mode
        self.services.settings.set("store_view_mode", mode)
        theme_key = self.services.settings.get("theme", "light")
        self.grid_mode_btn.variant = "secondary" if mode == "grid" else "outline"
        self.grid_mode_btn.apply_style(theme_key)
        self.list_mode_btn.variant = "secondary" if mode == "list" else "outline"
        self.list_mode_btn.apply_style(theme_key)
        self._render_view()

    def _render_view(self):
        while self.c_layout.count():
            item = self.c_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget(): sub.widget().deleteLater()
        self.cards.clear()

        if self.view_mode == "grid":
            grid_widget = QWidget()
            self.grid_layout = QGridLayout(grid_widget)
            self.grid_layout.setContentsMargins(0, 0, 0, 0)
            self.grid_layout.setHorizontalSpacing(14)
            self.grid_layout.setVerticalSpacing(14)

            for app in CURATED_APPS:
                card = AppGridCard(app, self.installed_sources)
                card.clicked.connect(self._open_install_popup)
                self.cards.append(card)

            self.c_layout.addWidget(grid_widget)
        else: # List view
            for app in CURATED_APPS:
                card = AppBannerCard(app, self.installed_sources)
                card.clicked.connect(self._open_install_popup)
                self.cards.append(card)
                self.c_layout.addWidget(card)

        self.c_layout.addStretch()
        self._filter_apps()

    def _open_install_popup(self, app_data: dict, is_installed: bool):
        dialog = AppInstallDialog(app_data, is_installed, parent=self)
        dialog.exec()
        # Refresh card status immediately after dialog closes (no delay needed)
        self._refresh_all_cards()

    def _filter_apps(self):
        query = self.search_input.text().strip().lower()
        visible_cards = []

        for card in self.cards:
            app = card.app_data
            matches_cat = (self.selected_category == "All") or (app["category"] == self.selected_category)
            matches_query = (not query) or (query in app["name"].lower()) or (query in app["desc"].lower()) or (query in app["category"].lower())
            
            if matches_cat and matches_query:
                visible_cards.append(card)
                card.show()
            else:
                card.hide()

        if self.view_mode == "grid" and hasattr(self, "grid_layout"):
            # Arrange visible cards into 3 columns
            for idx, card in enumerate(visible_cards):
                row = idx // 3
                col = idx % 3
                self.grid_layout.addWidget(card, row, col)

    def _on_category_clicked(self, cat: str):
        self.selected_category = cat
        self.active_sub_tab = cat
        theme_key = self.services.settings.get("theme", "light")
        for c_name, btn in self.cat_buttons:
            btn.variant = "secondary" if c_name == cat else "outline"
            btn.apply_style(theme_key)
        self._filter_apps()

    def _switch_sub_tab(self, key: str):
        self._on_category_clicked(key)

    def _refresh_all_cards(self):
        self.installed_sources = self.services.packages.get_installed_sources(refresh=True)
        for card in self.cards:
            card.installed_sources = self.installed_sources
            card.refresh_status()
