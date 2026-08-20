"""
Settings View: Application menu registration, autostart on login,
AppImage packaging, and Theme Switcher (Dark Mode, Dark Blue, Cyberpunk, Doom, White).
Equipped with top sub-module tabs for focused organization.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QScrollArea, QFrame, QGridLayout, QApplication, QPushButton
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QPixmap, QCursor

from cachy_control.core.service_registry import ServiceRegistry
from cachy_control.ui.components.sharp_card import SharpCard
from cachy_control.ui.components.sharp_button import SharpButton
from cachy_control.ui.components.section_badge import SectionBadge
from cachy_control.ui.theme import THEMES, get_theme_stylesheet

class ThemeCard(QFrame):
    def __init__(self, theme_key: str, theme_info: dict, is_active: bool, on_select, parent: QWidget = None):
        super().__init__(parent)
        self.theme_key = theme_key
        self.on_select = on_select
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(84)

        border_col = theme_info["accent"] if is_active else theme_info["border"]
        self.setStyleSheet(f"""
            ThemeCard {{
                background-color: {theme_info["card_bg"]};
                border: {'2px solid ' + theme_info["accent"] if is_active else '1px solid ' + theme_info["border"]};
                border-radius: 0px;
            }}
            ThemeCard:hover {{
                border: 2px solid {theme_info["accent"]};
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(12)

        # Color Swatches Preview
        swatch_box = QHBoxLayout()
        swatch_box.setSpacing(4)
        for c in [theme_info["bg"], theme_info["card_bg"], theme_info["accent"], theme_info["text"]]:
            sw = QFrame()
            sw.setFixedSize(14, 36)
            sw.setStyleSheet(f"background-color: {c}; border: 1px solid {theme_info['border']};")
            swatch_box.addWidget(sw)
        layout.addLayout(swatch_box)

        # Info
        info_box = QVBoxLayout()
        info_box.setSpacing(2)
        title = QLabel(theme_info["name"])
        title.setStyleSheet(f"font-size: 13px; font-weight: 800; color: {theme_info['text']};")
        sub = QLabel(f"Primary: {theme_info['accent']} | Canvas: {theme_info['bg']}")
        sub.setStyleSheet(f"font-size: 10px; color: {theme_info['subtext']}; font-family: monospace;")
        info_box.addWidget(title)
        info_box.addWidget(sub)
        layout.addLayout(info_box, 1)

        # Active tag or select button
        if is_active:
            tag = QLabel("Active")
            tag.setStyleSheet(f"font-size: 11px; font-weight: 800; color: {theme_info['accent']}; padding: 4px 8px; border: 1px solid {theme_info['accent']};")
            layout.addWidget(tag)
        else:
            btn = QPushButton("Select")
            btn.setFixedSize(70, 28)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {theme_info['text']};
                    border: 1px solid {theme_info['border']};
                    padding: 4px 10px;
                    font-size: 11px;
                }}
                QPushButton:hover {{
                    background-color: {theme_info['accent']};
                    color: {theme_info['accent_text']};
                }}
            """)
            btn.clicked.connect(self._select)
            layout.addWidget(btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._select()
        super().mousePressEvent(event)

    def _select(self):
        self.on_select(self.theme_key)

class SettingsView(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.services = ServiceRegistry.get()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header
        header = QHBoxLayout()
        header.addWidget(SectionBadge("settings", "SETTINGS & THEMES"))
        header.addStretch()
        self.refresh_btn = SharpButton("Refresh Status", icon_name="refresh", variant="outline")
        self.refresh_btn.clicked.connect(self._refresh_status)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        # Sub-Module Filter Tabs at the Top
        subtab_row = QHBoxLayout()
        subtab_row.setSpacing(8)

        self.subtab_configs = [
            ("themes", "Themes & Visual Style", "sliders"),
            ("desktop", "Desktop Integration", "check"),
            ("pkg", "AppImage Packaging", "package"),
            ("all", "Show All", "package"),
        ]
        self.subtab_buttons = {}
        for key, label, icon in self.subtab_configs:
            btn = SharpButton(label, icon_name=icon, variant="outline" if key != "themes" else "primary")
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

        # 1. Theme & Visual Style Selector Card
        self.theme_card = SharpCard("Theme & Visual Style", "Choose your preferred aesthetic (Dark Mode, Dark Blue, Cyberpunk, Doom, Minimalist White)")
        self.theme_grid = QVBoxLayout()
        self.theme_grid.setSpacing(10)
        self._render_theme_cards()
        self.theme_card.add_layout(self.theme_grid)
        self.c_layout.addWidget(self.theme_card)

        # 2. App Menu & Autostart Integration Card
        self.integration_card = SharpCard("Desktop & Startup Integration", "Register application into your desktop launcher and configure run on startup")
        i_layout = QVBoxLayout()
        i_layout.setSpacing(14)

        st_row = QHBoxLayout()
        st_row.setSpacing(24)

        m_box = QVBoxLayout()
        m_box.setSpacing(4)
        m_title = QLabel("Application Menu Status:")
        m_title.setStyleSheet("font-size: 12px; opacity: 0.85; font-weight: 600;")
        self.app_menu_status_lbl = QLabel("Checking...")
        self.app_menu_status_lbl.setStyleSheet("font-size: 13px; font-weight: 700; ")
        m_box.addWidget(m_title)
        m_box.addWidget(self.app_menu_status_lbl)
        st_row.addLayout(m_box)

        a_box = QVBoxLayout()
        a_box.setSpacing(4)
        a_title = QLabel("Run on Startup Status:")
        a_title.setStyleSheet("font-size: 12px; opacity: 0.85; font-weight: 600;")
        self.autostart_status_lbl = QLabel("Checking...")
        self.autostart_status_lbl.setStyleSheet("font-size: 13px; font-weight: 700; ")
        a_box.addWidget(a_title)
        a_box.addWidget(self.autostart_status_lbl)
        st_row.addLayout(a_box)
        st_row.addStretch()
        i_layout.addLayout(st_row)

        btn_grid = QHBoxLayout()
        btn_grid.setSpacing(10)

        self.both_btn = SharpButton("Add Once to Startup & App Menu (Both)", icon_name="check", variant="primary")
        self.both_btn.clicked.connect(self._add_both)
        btn_grid.addWidget(self.both_btn)

        self.add_menu_btn = SharpButton("Add to App Menu", icon_name="plus", variant="secondary")
        self.add_menu_btn.clicked.connect(self._toggle_app_menu)
        btn_grid.addWidget(self.add_menu_btn)

        self.toggle_auto_btn = SharpButton("Run on Startup", icon_name="power", variant="secondary")
        self.toggle_auto_btn.clicked.connect(self._toggle_autostart)
        btn_grid.addWidget(self.toggle_auto_btn)

        btn_grid.addStretch()
        i_layout.addLayout(btn_grid)

        self.integration_card.add_layout(i_layout)
        self.c_layout.addWidget(self.integration_card)

        # 3. AppImage & Packaging Card
        self.pkg_card = SharpCard("AppImage & Packaging", "Standalone AppImage bundle generation inside ./packaging")
        p_layout = QVBoxLayout()
        p_layout.setSpacing(12)

        info_row = QHBoxLayout()
        info_row.setSpacing(16)

        self.logo_lbl = QLabel()
        self.logo_lbl.setFixedSize(64, 64)
        logo_path = Path(__file__).parent.parent / "assets" / "logo_256.png"
        if not logo_path.exists():
            logo_path = Path(__file__).parent.parent / "assets" / "logo.png"
        if logo_path.exists():
            pix = QPixmap(str(logo_path))
            self.logo_lbl.setPixmap(pix.scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        info_row.addWidget(self.logo_lbl)

        info_text = QVBoxLayout()
        info_text.setSpacing(4)
        name_lbl = QLabel("CachyOS Control Center AppImage Bundle")
        name_lbl.setStyleSheet("font-size: 13px; font-weight: 700;")
        desc_lbl = QLabel("Builds a portable, single-file executable package with bundled desktop metadata and hicolor icons.")
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("font-size: 11px; opacity: 0.85;")
        info_text.addWidget(name_lbl)
        info_text.addWidget(desc_lbl)
        info_row.addLayout(info_text, 1)

        p_layout.addLayout(info_row)

        pkg_btn_row = QHBoxLayout()
        pkg_btn_row.setSpacing(10)

        self.build_appimage_btn = SharpButton("Build Standalone AppImage", icon_name="package", variant="primary")
        self.build_appimage_btn.clicked.connect(self._build_appimage)
        pkg_btn_row.addWidget(self.build_appimage_btn)

        self.open_pkg_dir_btn = SharpButton("Open Packaging Folder", icon_name="folder", variant="outline")
        self.open_pkg_dir_btn.clicked.connect(self._open_packaging_folder)
        pkg_btn_row.addWidget(self.open_pkg_dir_btn)

        pkg_btn_row.addStretch()
        p_layout.addLayout(pkg_btn_row)

        self.pkg_card.add_layout(p_layout)
        self.c_layout.addWidget(self.pkg_card)

        self.c_layout.addStretch()
        self.scroll.setWidget(container)
        layout.addWidget(self.scroll)

        self._switch_sub_tab("themes")
        QTimer.singleShot(0, self._refresh_status)

    def _switch_sub_tab(self, active_key: str):
        self.active_sub_tab = active_key
        t_key = self.services.settings.get("theme", "light")
        for key, btn in self.subtab_buttons.items():
            btn.variant = "primary" if key == active_key else "outline"
            btn.apply_style(t_key)

        show_all = (active_key == "all")
        self.theme_card.setVisible(show_all or active_key == "themes")
        self.integration_card.setVisible(show_all or active_key == "desktop")
        self.pkg_card.setVisible(show_all or active_key == "pkg")

    def _render_theme_cards(self):
        while self.theme_grid.count():
            item = self.theme_grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget(): sub.widget().deleteLater()

        current_theme = self.services.settings.get("theme", "light")
        for key, info in THEMES.items():
            card = ThemeCard(key, info, is_active=(key == current_theme), on_select=self._set_theme)
            self.theme_grid.addWidget(card)

    def _set_theme(self, theme_key: str):
        win = self.window()
        if hasattr(win, "set_theme"):
            win.set_theme(theme_key)
        else:
            self.services.settings.set("theme", theme_key)
            QApplication.instance().setStyleSheet(get_theme_stylesheet(theme_key))
            self._render_theme_cards()

    def _refresh_status(self):
        is_menu = self.services.system.is_app_menu_installed()
        is_auto = self.services.system.is_autostart_enabled()

        if is_menu:
            self.app_menu_status_lbl.setText("✓ Registered in App Menu")
            self.app_menu_status_lbl.setStyleSheet("color: #059669; font-weight: 700;")
            self.add_menu_btn.set_clean_text("Remove from Menu")
            self.add_menu_btn.variant = "danger"
        else:
            self.app_menu_status_lbl.setText("Not Registered")
            self.app_menu_status_lbl.setStyleSheet("opacity: 0.7; font-weight: 600;")
            self.add_menu_btn.set_clean_text("Add to App Menu")
            self.add_menu_btn.variant = "secondary"
        self.add_menu_btn.apply_style()

        if is_auto:
            self.autostart_status_lbl.setText("✓ Enabled (Starts on Login)")
            self.autostart_status_lbl.setStyleSheet("color: #059669; font-weight: 700;")
            self.toggle_auto_btn.set_clean_text("Disable Autostart")
            self.toggle_auto_btn.variant = "danger"
        else:
            self.autostart_status_lbl.setText("Disabled")
            self.autostart_status_lbl.setStyleSheet("opacity: 0.7; font-weight: 600;")
            self.toggle_auto_btn.set_clean_text("Enable Autostart")
            self.toggle_auto_btn.variant = "secondary"
        self.toggle_auto_btn.apply_style()

        if is_menu and is_auto:
            self.both_btn.setEnabled(False)
            self.both_btn.set_clean_text("✓ Fully Integrated")
        else:
            self.both_btn.setEnabled(True)
            self.both_btn.set_clean_text("Add Once to Startup & App Menu (Both)")
        self.both_btn.apply_style()

    def _add_both(self):
        self.services.system.install_app_menu()
        self.services.system.enable_autostart()
        self._refresh_status()

    def _toggle_app_menu(self):
        if self.services.system.is_app_menu_installed():
            self.services.system.uninstall_app_menu()
        else:
            self.services.system.install_app_menu()
        self._refresh_status()

    def _toggle_autostart(self):
        if self.services.system.is_autostart_enabled():
            self.services.system.disable_autostart()
        else:
            self.services.system.enable_autostart()
        self._refresh_status()

    def _build_appimage(self):
        script = str(Path(__file__).parent.parent.parent.parent / "packaging" / "build_appimage.sh")
        self.services.runner.run_command(f"bash '{script}'")

    def _open_packaging_folder(self):
        pkg_dir = str(Path(__file__).parent.parent.parent.parent / "packaging")
        self.services.runner.run_command(f"dolphin '{pkg_dir}' &")
