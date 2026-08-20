"""
Main Application Window for CachyOS Control Center.
Composes Sidebar Navigation with distinct active item highlight,
App-Wide Live State & Progress Bar, Permanently Docked Terminal Drawer,
Bottom-Right Action Notification Toasts, Live Multi-Theme Support,
and Complete Keyboard Shortcuts (Shift+T, Q/E Sub-Page Navigation, Tab/Shift+Tab Module Cycling, Ctrl+1..9, Ctrl+F, F1).
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame, QApplication, QDialog,
    QLineEdit, QTextEdit, QPlainTextEdit
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QCursor, QFont, QIcon, QResizeEvent, QKeySequence, QShortcut, QKeyEvent
from cachy_control.core.services.sudo_service import SudoService
from cachy_control.ui.components.sudo_dialog import SudoAuthDialog

from cachy_control.core.service_registry import ServiceRegistry
from cachy_control.ui.theme import THEMES, SECTION_COLORS, get_theme_stylesheet
from cachy_control.ui.icons import get_icon, get_pixmap
from cachy_control.ui.components.state_bar import StateBar
from cachy_control.ui.components.terminal_drawer import TerminalDrawer
from cachy_control.ui.components.sharp_button import SharpButton
from cachy_control.ui.components.notification_toast import NotificationToast
from cachy_control.ui.components.shortcuts_dialog import ShortcutsDialog

# Views
from cachy_control.ui.views.dashboard_view import DashboardView
from cachy_control.ui.views.store_view import StoreView
from cachy_control.ui.views.updates_view import UpdatesView
from cachy_control.ui.views.cleanup_view import CleanupView
from cachy_control.ui.views.storage_view import StorageView
from cachy_control.ui.views.audio_bt_view import AudioBtView
from cachy_control.ui.views.network_vm_view import NetworkVmView
from cachy_control.ui.views.gaming_tools_view import GamingToolsView
from cachy_control.ui.views.zram_view import ZramView
from cachy_control.ui.views.security_view import SecurityView
from cachy_control.ui.views.settings_view import SettingsView

class NavButton(QPushButton):
    def __init__(self, key: str, label: str, icon_name: str, parent: QWidget = None):
        safe_label = label.replace("&", "&&")
        super().__init__(f"  {safe_label}", parent)
        self.key = key
        self.display_label = label
        self.icon_name = icon_name
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(38)
        self.setCheckable(True)
        self.update_theme_style("light")

    def update_theme_style(self, theme_key: str):
        t = THEMES.get(theme_key, THEMES["light"])
        self.setIcon(get_icon(self.icon_name, size=18, color=t["text"]))
        self.setIconSize(QSize(18, 18))
        active_bg = t.get("nav_active_bg", t["card_bg"])
        
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-left: 4px solid transparent;
                text-align: left;
                padding-left: 14px;
                font-weight: 600;
                font-size: 13px;
                color: {t["subtext"]};
            }}
            QPushButton:hover {{
                background-color: {t["nav_hover"]};
                color: {t["text"]};
            }}
            QPushButton:checked {{
                background-color: {active_bg};
                border-left: 4px solid {t["active_nav_border"]};
                color: {t["text"]};
                font-weight: 800;
            }}
        """)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CachyOS Control Center")
        self.resize(1240, 840)
        self.setMinimumSize(1000, 680)

        # Set Window Icon
        logo_path = Path(__file__).parent / "ui" / "assets" / "logo_256.png"
        if logo_path.exists():
            self.setWindowIcon(QIcon(str(logo_path)))

        self.services = ServiceRegistry.get()

        # Root Widget
        root = QWidget()
        root.setObjectName("rootWindow")
        self.setCentralWidget(root)
        
        main_h_layout = QHBoxLayout(root)
        main_h_layout.setContentsMargins(0, 0, 0, 0)
        main_h_layout.setSpacing(0)

        # 1. Left Sidebar Navigation
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(220)
        
        s_layout = QVBoxLayout(self.sidebar)
        s_layout.setContentsMargins(0, 0, 0, 0)
        s_layout.setSpacing(0)

        # Header Title
        title_box = QWidget()
        title_box.setFixedHeight(64)
        t_layout = QVBoxLayout(title_box)
        t_layout.setContentsMargins(20, 16, 20, 12)
        t_layout.setSpacing(2)

        self.app_title = QLabel("CACHYOS")
        self.app_title.setStyleSheet("font-weight: 900; font-size: 15px; letter-spacing: 1.5px;")
        t_layout.addWidget(self.app_title)

        self.app_sub = QLabel("CONTROL CENTER")
        self.app_sub.setStyleSheet("font-weight: 700; font-size: 11px; letter-spacing: 1px;")
        t_layout.addWidget(self.app_sub)
        s_layout.addWidget(title_box)

        # Nav Items Config
        essential_nav = [
            ("dashboard", "Dashboard", "dashboard", DashboardView),
            ("store", "App Store", "store", StoreView),
            ("updates", "Updates & Packages", "refresh", UpdatesView),
            ("cleanup", "System Cleanup", "trash", CleanupView),
            ("storage", "Storage & Cloud", "database", StorageView),
            ("audio_bt", "Audio & Bluetooth", "volume", AudioBtView),
            ("network", "Network & VMs", "globe", NetworkVmView),
        ]

        advanced_nav = [
            ("gaming", "Gaming & Runners", "gamepad", GamingToolsView),
            ("zram", "Memory & ZRAM", "zap", ZramView),
            ("security", "Security & Auditing", "shield", SecurityView),
            ("settings", "Settings & Themes", "sliders", SettingsView),
        ]

        all_nav_items = essential_nav + advanced_nav

        self.nav_buttons = []
        self.stack = QStackedWidget()
        self.views_map = {}

        # Render Essential Nav Items
        nav_container = QWidget()
        n_layout = QVBoxLayout(nav_container)
        n_layout.setContentsMargins(0, 8, 0, 0)
        n_layout.setSpacing(2)

        for i, (key, label, icon, view_cls) in enumerate(essential_nav):
            btn = NavButton(key, label, icon)
            btn.clicked.connect(lambda _, k=key, idx=i: self._switch_tab(k, idx))
            n_layout.addWidget(btn)
            self.nav_buttons.append(btn)

            view_inst = view_cls()
            self.stack.addWidget(view_inst)
            self.views_map[key] = view_inst

        # Subtle visual separator line for Advanced Features category
        divider_box = QWidget()
        d_layout = QVBoxLayout(divider_box)
        d_layout.setContentsMargins(16, 12, 16, 4)
        d_layout.setSpacing(6)
        
        self.orange_line = QFrame()
        self.orange_line.setFixedHeight(2)
        self.orange_line.setStyleSheet("background-color: #EA580C; border: none;")
        d_layout.addWidget(self.orange_line)

        self.adv_label = QLabel("ADVANCED FEATURES")
        self.adv_label.setStyleSheet("font-size: 10px; font-weight: 800; color: #EA580C; letter-spacing: 0.8px;")
        d_layout.addWidget(self.adv_label)
        n_layout.addWidget(divider_box)

        # Render Advanced Nav Items
        for j, (key, label, icon, view_cls) in enumerate(advanced_nav):
            idx = len(essential_nav) + j
            btn = NavButton(key, label, icon)
            btn.clicked.connect(lambda _, k=key, index=idx: self._switch_tab(k, index))
            n_layout.addWidget(btn)
            self.nav_buttons.append(btn)

            view_inst = view_cls()
            self.stack.addWidget(view_inst)
            self.views_map[key] = view_inst

        s_layout.addWidget(nav_container)
        s_layout.addStretch()

        # Bottom Branding Footer
        footer_box = QWidget()
        f_layout = QVBoxLayout(footer_box)
        f_layout.setContentsMargins(20, 10, 20, 16)
        self.cachy_badge = QLabel("Arch / CachyOS Linux")
        self.cachy_badge.setStyleSheet("font-size: 11px; font-weight: 600; opacity: 0.6;")
        f_layout.addWidget(self.cachy_badge)
        s_layout.addWidget(footer_box)

        main_h_layout.addWidget(self.sidebar)

        # 2. Main Content Area (Modules bend to the absolute docked terminal)
        content_container = QWidget()
        content_v_layout = QVBoxLayout(content_container)
        content_v_layout.setContentsMargins(0, 0, 0, 0)
        content_v_layout.setSpacing(0)

        # Top Bar
        self.topbar = QWidget()
        self.topbar.setFixedHeight(52)
        self.topbar.setStyleSheet("background-color: #FFFFFF; border-bottom: 1px solid #EEEEEE;")
        tb_layout = QHBoxLayout(self.topbar)
        tb_layout.setContentsMargins(24, 0, 24, 0)
        tb_layout.setSpacing(10)

        self.current_section_title = QLabel("Dashboard")
        self.current_section_title.setTextFormat(Qt.TextFormat.PlainText)
        self.current_section_title.setMinimumWidth(320)
        self.current_section_title.setStyleSheet("font-size: 15px; font-weight: 700;")
        tb_layout.addWidget(self.current_section_title)
        tb_layout.addStretch()

        # Keyboard shortcuts quick guide button
        self.shortcuts_btn = SharpButton("Hotkeys (?)", icon_name="sliders", variant="outline")
        self.shortcuts_btn.setToolTip("Show Keyboard Shortcuts Reference (F1 / ?)")
        self.shortcuts_btn.clicked.connect(self._show_shortcuts_dialog)
        tb_layout.addWidget(self.shortcuts_btn)

        self.terminal_toggle_btn = SharpButton("Terminal Log (Shift+T)", icon_name="terminal", variant="outline")
        self.terminal_toggle_btn.setToolTip("Toggle Live Terminal drawer (Shift+T / Ctrl+` / F12)")
        self.terminal_toggle_btn.clicked.connect(self._toggle_terminal)
        tb_layout.addWidget(self.terminal_toggle_btn)
        content_v_layout.addWidget(self.topbar)

        # App-Wide State & Progress Bar
        self.state_bar = StateBar()
        self.state_bar.cancel_requested.connect(self.services.runner.cancel_current)
        content_v_layout.addWidget(self.state_bar)

        # Stack container
        content_v_layout.addWidget(self.stack, 1)

        # Absolute Docked Terminal Container at the bottom of the window
        self.terminal_container = QWidget()
        t_box = QVBoxLayout(self.terminal_container)
        t_box.setContentsMargins(24, 0, 24, 16)
        t_box.setSpacing(0)

        self.terminal_drawer = TerminalDrawer()
        self.terminal_drawer.cancel_requested.connect(self.services.runner.cancel_current)
        t_box.addWidget(self.terminal_drawer)
        self.terminal_container.hide()
        content_v_layout.addWidget(self.terminal_container)

        main_h_layout.addWidget(content_container)

        # Floating Bottom-Right Notification Toast
        self.toast = NotificationToast(self)
        self.toast.view_terminal_requested.connect(self._show_and_scroll_terminal)

        # Connect Runner Signals
        self.services.runner.output_received.connect(self.terminal_drawer.append_text)
        self.services.runner.process_started.connect(self._on_process_started)
        self.services.runner.process_finished.connect(self._on_process_finished)

        # Configure Global Keyboard Shortcuts
        self._setup_shortcuts()

        # Apply saved Theme
        saved_theme = self.services.settings.get("theme", "light")
        self.set_theme(saved_theme)

        # Select Initial Tab
        last_tab = self.services.settings.get("last_tab", "dashboard")
        initial_idx = 0
        for i, (k, _, _, _) in enumerate(all_nav_items):
            if k == last_tab:
                initial_idx = i
                break
        self._switch_tab(all_nav_items[initial_idx][0], initial_idx)

        # Check and prompt for Sudo authentication on launch
        QTimer.singleShot(250, self._prompt_startup_sudo)

    def _setup_shortcuts(self):
        # 1. Terminal toggles: Shift+T, Ctrl+`, F12
        sc_shift_t = QShortcut(QKeySequence("Shift+T"), self)
        sc_shift_t.activated.connect(self._toggle_terminal)

        sc_tilde = QShortcut(QKeySequence("Ctrl+`"), self)
        sc_tilde.activated.connect(self._toggle_terminal)

        sc_f12 = QShortcut(QKeySequence("F12"), self)
        sc_f12.activated.connect(self._toggle_terminal)

        # 2. Search box focus: Ctrl+F
        sc_find = QShortcut(QKeySequence("Ctrl+F"), self)
        sc_find.activated.connect(self._focus_active_search)

        # 3. Help modal: F1
        sc_help = QShortcut(QKeySequence("F1"), self)
        sc_help.activated.connect(self._show_shortcuts_dialog)

        # 4. Module Jump shortcuts: Ctrl+1 through Ctrl+9, Ctrl+0
        for num in range(1, 10):
            sc_num = QShortcut(QKeySequence(f"Ctrl+{num}"), self)
            idx = num - 1
            sc_num.activated.connect(lambda i=idx: self._jump_to_module(i))

        sc_num0 = QShortcut(QKeySequence("Ctrl+0"), self)
        sc_num0.activated.connect(lambda: self._jump_to_module(9))

        # 5. Shift+Tab module cycling
        sc_shift_tab = QShortcut(QKeySequence("Shift+Tab"), self)
        sc_shift_tab.activated.connect(lambda: self._cycle_module(-1))

    def _jump_to_module(self, index: int):
        if 0 <= index < len(self.nav_buttons):
            self.nav_buttons[index].click()

    def _cycle_module(self, delta: int):
        curr = self.stack.currentIndex()
        next_idx = (curr + delta) % len(self.nav_buttons)
        self.nav_buttons[next_idx].click()

    def keyPressEvent(self, event: QKeyEvent):
        focus_w = QApplication.focusWidget()
        is_typing = isinstance(focus_w, (QLineEdit, QTextEdit, QPlainTextEdit))

        # Escape key
        if event.key() == Qt.Key.Key_Escape:
            if self.terminal_container.isVisible() and self.terminal_drawer.input_field.hasFocus():
                self.terminal_container.hide()
                return
            elif is_typing and focus_w:
                focus_w.clearFocus()
                return

        # Navigation shortcuts (only when not actively typing in an input)
        if not is_typing:
            if event.key() == Qt.Key.Key_Q:
                self._navigate_subtab(-1)
                return
            elif event.key() == Qt.Key.Key_E:
                self._navigate_subtab(1)
                return
            elif event.key() == Qt.Key.Key_Backtab or (event.key() == Qt.Key.Key_Tab and event.modifiers() == Qt.KeyboardModifier.ShiftModifier):
                self._cycle_module(-1)
                return
            elif event.key() == Qt.Key.Key_Tab:
                self._cycle_module(1)
                return
            elif event.key() == Qt.Key.Key_Slash:
                self._focus_active_search()
                return
            elif event.key() == Qt.Key.Key_Question:
                self._show_shortcuts_dialog()
                return

        super().keyPressEvent(event)

    def _navigate_subtab(self, delta: int):
        curr_view = self.stack.currentWidget()
        if hasattr(curr_view, "subtab_configs") and hasattr(curr_view, "_switch_sub_tab"):
            configs = curr_view.subtab_configs
            if not configs:
                return
            keys = [c[0] for c in configs]
            active = getattr(curr_view, "active_sub_tab", keys[0])
            try:
                curr_idx = keys.index(active)
            except ValueError:
                curr_idx = 0
            new_idx = (curr_idx + delta) % len(keys)
            curr_view._switch_sub_tab(keys[new_idx])

    def _focus_active_search(self):
        curr_view = self.stack.currentWidget()
        for attr in ["search_input", "filter_input", "app_id_input", "watch_path_input"]:
            if hasattr(curr_view, attr):
                w = getattr(curr_view, attr)
                if isinstance(w, QLineEdit):
                    w.setFocus()
                    w.selectAll()
                    return

    def _show_shortcuts_dialog(self):
        dlg = ShortcutsDialog(self)
        dlg.exec()

    def _prompt_startup_sudo(self):
        if not SudoService.is_sudo_cached():
            dlg = SudoAuthDialog("Grant Administrator Privileges on Launch", is_startup=True, parent=self)
            if dlg.exec() == QDialog.DialogCode.Accepted:
                self.state_bar.set_status("Root Session Authenticated", is_loading=False)

    def set_theme(self, theme_key: str):
        t = THEMES.get(theme_key, THEMES["light"])
        self.setStyleSheet(get_theme_stylesheet(theme_key))
        self.services.settings.set("theme", theme_key)
        
        self.topbar.setStyleSheet(f"background-color: {t['card_bg']}; border-bottom: 1px solid {t['border']};")
        self.orange_line.setStyleSheet(f"background-color: {t['divider']}; border: none;")
        self.adv_label.setStyleSheet(f"font-size: 10px; font-weight: 800; color: {t['divider']}; letter-spacing: 0.8px;")
        self.app_title.setStyleSheet(f"font-weight: 900; font-size: 15px; letter-spacing: 1.5px; color: {t['text']};")
        self.app_sub.setStyleSheet(f"font-weight: 700; font-size: 11px; letter-spacing: 1px; color: {t['subtext']};")
        self.cachy_badge.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {t['subtext']};")
        self.current_section_title.setStyleSheet(f"font-size: 15px; font-weight: 700; color: {t['text']};")
        self.state_bar.apply_theme_style(theme_key)
        self.terminal_drawer.apply_theme_style(theme_key)

        for btn in self.nav_buttons:
            btn.update_theme_style(theme_key)

        from cachy_control.ui.components.sharp_card import SharpCard
        from cachy_control.ui.components.stat_gauge import StatGauge
        from cachy_control.ui.components.section_badge import SectionBadge
        from cachy_control.ui.components.drop_zone import DropZone
        from cachy_control.ui.components.sharp_button import SharpButton

        for card in self.findChildren(SharpCard):
            card.apply_theme_style(theme_key)
        for gauge in self.findChildren(StatGauge):
            gauge.apply_theme_style(theme_key)
        for badge in self.findChildren(SectionBadge):
            badge.apply_theme_style(theme_key)
        for drop in self.findChildren(DropZone):
            drop.apply_theme_style(theme_key)
        for btn in self.findChildren(SharpButton):
            btn.apply_style(theme_key)

        from cachy_control.ui.views.store_view import StoreView, AppGridCard, AppBannerCard
        for sv in self.findChildren(StoreView):
            sv.apply_theme_style(theme_key)
        for card in self.findChildren(AppGridCard):
            card.apply_theme_style(theme_key)
        for card in self.findChildren(AppBannerCard):
            card.apply_theme_style(theme_key)

        if "settings" in self.views_map and hasattr(self.views_map["settings"], "_render_theme_cards"):
            self.views_map["settings"]._render_theme_cards()

    def _switch_tab(self, key: str, index: int):
        for btn in self.nav_buttons:
            btn.setChecked(btn.key == key)
        self.stack.setCurrentIndex(index)
        cfg = SECTION_COLORS.get(key, {"name": key.title()})
        self.current_section_title.setText(cfg["name"])
        self.services.settings.set("last_tab", key)

    def _on_process_started(self, cmd: str):
        self.state_bar.set_running(True, cmd)
        self.terminal_drawer.set_running(True, cmd)
        self.terminal_container.show()

    def _on_process_finished(self, exit_code: int):
        self.state_bar.set_running(False)
        self.terminal_drawer.set_running(False)
        if exit_code == 0:
            self.toast.show_toast(
                "Action Completed Successfully",
                "Operation finished with exit code 0.",
                "success"
            )
        else:
            self.toast.show_toast(
                "Action Notice / Error",
                f"Process returned exit code {exit_code}. Check terminal for details.",
                "error"
            )

    def _show_and_scroll_terminal(self):
        self.terminal_container.show()

    def _toggle_terminal(self):
        if self.terminal_container.isVisible():
            self.terminal_container.hide()
        else:
            self.terminal_container.show()
            self.terminal_drawer.input_field.setFocus()

    def resizeEvent(self, event: QResizeEvent):
        super().resizeEvent(event)
        self.toast.reposition()
