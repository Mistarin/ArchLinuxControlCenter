"""
Cleanup View: One-click system cleanup, cache wipes, Dolphin reset, shader cache fixes & logs vacuum.
Equipped with top sub-module tabs for focused navigation.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QGridLayout, QScrollArea
)
from PyQt6.QtCore import Qt

from cachy_control.core.service_registry import ServiceRegistry
from cachy_control.ui.components.sharp_card import SharpCard
from cachy_control.ui.components.sharp_button import SharpButton
from cachy_control.ui.components.section_badge import SectionBadge
from cachy_control.ui.components.confirm_dialog import confirm_destructive_action
from cachy_control.ui.theme import THEMES

class CleanupView(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.services = ServiceRegistry.get()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Row
        header = QHBoxLayout()
        header.addWidget(SectionBadge("cleanup", "ONE-CLICK SYSTEM CLEANUP"))
        header.addStretch()
        layout.addLayout(header)

        # Sub-Module Filter Tabs at the Top
        subtab_row = QHBoxLayout()
        subtab_row.setSpacing(8)

        self.subtab_configs = [
            ("general", "General Maintenance", "trash"),
            ("shader", "Steam Shader Cache", "sliders"),
            ("locale", "EasyEffects Locale", "sliders"),
            ("all", "Show All", "package"),
        ]
        self.subtab_buttons = {}
        for key, label, icon in self.subtab_configs:
            btn = SharpButton(label, icon_name=icon, variant="outline" if key != "general" else "primary")
            btn.setFixedHeight(30)
            btn.clicked.connect(lambda _, k=key: self._switch_sub_tab(k))
            subtab_row.addWidget(btn)
            self.subtab_buttons[key] = btn

        subtab_row.addStretch()
        layout.addLayout(subtab_row)

        # Scroll Area
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        container = QWidget()
        self.c_layout = QVBoxLayout(container)
        self.c_layout.setContentsMargins(0, 0, 0, 0)
        self.c_layout.setSpacing(16)

        # 1. Quick One-Click Cleaners Grid Card
        self.grid_card = SharpCard("General System Maintenance", "Reclaim storage space and clear stale application caches")
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(16)

        # Dolphin Reset (Destructive - Red button)
        d_box = QVBoxLayout()
        d_title = QLabel("Dolphin File Manager Reset")
        d_title.setStyleSheet("font-weight: 700; font-size: 13px;")
        d_desc = QLabel("Clears broken config (dolphinrc), session window states, and local share cache.")
        d_desc.setWordWrap(True)
        d_desc.setStyleSheet("opacity: 0.85; font-size: 11px;")
        d_btn = SharpButton("Reset Dolphin Config", icon_name="trash", variant="danger")
        d_btn.clicked.connect(self._reset_dolphin)
        d_box.addWidget(d_title)
        d_box.addWidget(d_desc)
        d_box.addWidget(d_btn)
        grid.addLayout(d_box, 0, 0)

        # Pacman/Yay Cache Clean (Destructive)
        p_box = QVBoxLayout()
        p_title = QLabel("Package Cache Clean")
        p_title.setStyleSheet("font-weight: 700; font-size: 13px;")
        p_desc = QLabel("Removes downloaded package tarballs from /var/cache/pacman/pkg.")
        p_desc.setWordWrap(True)
        p_desc.setStyleSheet("opacity: 0.85; font-size: 11px;")
        p_btn = SharpButton("Clear Pacman & Yay Cache", icon_name="trash", variant="danger")
        p_btn.clicked.connect(self._clean_pacman_cache)
        p_box.addWidget(p_title)
        p_box.addWidget(p_desc)
        p_box.addWidget(p_btn)
        grid.addLayout(p_box, 0, 1)

        # Flatpak Unused Runtimes
        f_box = QVBoxLayout()
        f_title = QLabel("Flatpak Unused Runtimes")
        f_title.setStyleSheet("font-weight: 700; font-size: 13px;")
        f_desc = QLabel("Uninstalls orphan runtimes and libraries that are no longer referenced.")
        f_desc.setWordWrap(True)
        f_desc.setStyleSheet("opacity: 0.85; font-size: 11px;")
        f_btn = SharpButton("Remove Unused Flatpaks", icon_name="trash", variant="outline")
        f_btn.clicked.connect(self._clean_flatpak_unused)
        f_box.addWidget(f_title)
        f_box.addWidget(f_desc)
        f_box.addWidget(f_btn)
        grid.addLayout(f_box, 1, 0)

        # Journalctl vacuum
        j_box = QVBoxLayout()
        j_title = QLabel("Systemd Logs Vacuum")
        j_title.setStyleSheet("font-weight: 700; font-size: 13px;")
        j_desc = QLabel("Caps persistent journal log sizes to 100MB to avoid excessive disk bloat.")
        j_desc.setWordWrap(True)
        j_desc.setStyleSheet("opacity: 0.85; font-size: 11px;")
        j_btn = SharpButton("Vacuum Journal to 100M", icon_name="trash", variant="outline")
        j_btn.clicked.connect(self._vacuum_journal)
        j_box.addWidget(j_title)
        j_box.addWidget(j_desc)
        j_box.addWidget(j_btn)
        grid.addLayout(j_box, 1, 1)

        self.grid_card.add_layout(grid)
        self.c_layout.addWidget(self.grid_card)

        # 2. Steam Shader Cache & Texture Glitch Fix
        self.shader_card = SharpCard("Steam Shader Cache & Texture Fix", "Resolves corrupted shaders or texture glitches in games (e.g. No Man's Sky AppID 275850)")
        s_layout = QVBoxLayout()
        s_layout.setSpacing(12)

        s_input_row = QHBoxLayout()
        s_input_row.setSpacing(10)

        app_id_lbl = QLabel("Steam App ID:")
        app_id_lbl.setStyleSheet("font-size: 12px; opacity: 0.85;")
        s_input_row.addWidget(app_id_lbl)

        self.app_id_input = QLineEdit("275850")
        self.app_id_input.setPlaceholderText("e.g. 275850 (No Man's Sky)")
        self.app_id_input.setFixedWidth(120)
        s_input_row.addWidget(self.app_id_input)

        self.clean_shader_btn = SharpButton("Wipe Steam Shader Cache", icon_name="trash", variant="danger")
        self.clean_shader_btn.clicked.connect(self._wipe_shader_cache)
        s_input_row.addWidget(self.clean_shader_btn)

        self.open_shader_btn = SharpButton("Open Shader Dir in Dolphin", icon_name="folder", variant="outline")
        self.open_shader_btn.clicked.connect(self._open_shader_dir)
        s_input_row.addWidget(self.open_shader_btn)

        s_input_row.addStretch()
        s_layout.addLayout(s_input_row)

        tip_lbl = QLabel("Tip: Deleting the App ID folder inside steamapps/shadercache forces Proton/Vulkan to rebuild clean texture pipelines upon next launch.")
        tip_lbl.setStyleSheet("font-size: 11px; opacity: 0.85;")
        s_layout.addWidget(tip_lbl)

        self.shader_card.add_layout(s_layout)
        self.c_layout.addWidget(self.shader_card)

        # 3. EasyEffects Flatpak Language / Locale Fix
        self.ee_card = SharpCard("EasyEffects Language / Locale Fix", "Force English locale or reset default localization for EasyEffects Flatpak")
        ee_layout = QVBoxLayout()
        ee_layout.setSpacing(12)

        ee_row = QHBoxLayout()
        ee_row.setSpacing(10)

        self.ee_en_btn = SharpButton("Set EasyEffects Language = en_US", icon_name="check", variant="outline")
        self.ee_en_btn.clicked.connect(self._set_easyeffects_en)
        ee_row.addWidget(self.ee_en_btn)

        self.ee_reset_btn = SharpButton("Reset Language Override", icon_name="refresh", variant="outline")
        self.ee_reset_btn.clicked.connect(self._reset_easyeffects_locale)
        ee_row.addWidget(self.ee_reset_btn)

        ee_row.addStretch()
        ee_layout.addLayout(ee_row)

        self.ee_card.add_layout(ee_layout)
        self.c_layout.addWidget(self.ee_card)

        self.c_layout.addStretch()
        self.scroll.setWidget(container)
        layout.addWidget(self.scroll)

        self._switch_sub_tab("general")

    def _switch_sub_tab(self, active_key: str):
        self.active_sub_tab = active_key
        t_key = self.services.settings.get("theme", "light")
        for key, btn in self.subtab_buttons.items():
            btn.variant = "primary" if key == active_key else "outline"
            btn.apply_style(t_key)

        show_all = (active_key == "all")
        self.grid_card.setVisible(show_all or active_key == "general")
        self.shader_card.setVisible(show_all or active_key == "shader")
        self.ee_card.setVisible(show_all or active_key == "locale")

    def _reset_dolphin(self):
        if confirm_destructive_action(
            self,
            "Reset Dolphin File Manager Configuration",
            "This will close Dolphin, delete ~/.config/dolphinrc and clear view settings. Are you sure?",
            "Yes, Reset Dolphin"
        ):
            cmd = self.services.cleanup.get_clean_dolphin_command()
            self.services.runner.run_command(cmd)

    def _clean_pacman_cache(self):
        if confirm_destructive_action(
            self,
            "Clear Pacman and Yay Cache",
            "This will execute 'paccache -r -k 2' and 'yay -Sc --noconfirm' to remove downloaded tarballs. Proceed?",
            "Yes, Clear Cache"
        ):
            cmd = self.services.cleanup.get_clean_pacman_cache_command()
            self.services.runner.run_command(cmd)

    def _clean_flatpak_unused(self):
        cmd = self.services.cleanup.get_clean_flatpak_command()
        self.services.runner.run_command(cmd)

    def _vacuum_journal(self):
        cmd = self.services.cleanup.get_vacuum_journal_command()
        self.services.runner.run_command(cmd)

    def _wipe_shader_cache(self):
        raw_id = self.app_id_input.text().strip()
        app_id = "".join(c for c in raw_id if c.isdigit())
        if not app_id:
            self.services.runner.log("Invalid Steam App ID. Please enter numeric App ID (e.g. 275850).\n")
            return
        if confirm_destructive_action(
            self,
            f"Wipe Shader Cache for AppID {app_id}",
            f"This will remove the compiled Vulkan shader cache directory for Steam App ID {app_id}. Proceed?",
            "Yes, Wipe Cache"
        ):
            cmd = self.services.cleanup.get_clean_shader_cache_command(app_id)
            self.services.runner.run_command(cmd)

    def _open_shader_dir(self):
        raw_id = self.app_id_input.text().strip()
        app_id = "".join(c for c in raw_id if c.isdigit())
        if not app_id:
            app_id = "275850"
        cmd = self.services.cleanup.get_open_shader_dir_command(app_id)
        self.services.runner.run_command(cmd)

    def _set_easyeffects_en(self):
        cmd = self.services.cleanup.get_easyeffects_language_command("en_US")
        self.services.runner.run_command(cmd)

    def _reset_easyeffects_locale(self):
        cmd = self.services.cleanup.get_easyeffects_reset_command()
        self.services.runner.run_command(cmd)
