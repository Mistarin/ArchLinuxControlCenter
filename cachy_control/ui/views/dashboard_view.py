"""
Dashboard View: Live system cockpit, quick launchers, local dev servers (npm/pnpm/yarn/bun/vite/python) & shutdown timer.
Equipped with top sub-module tabs for focused organization.
"""

import os
import shutil
import shlex
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QComboBox,
    QLineEdit, QFileDialog, QGridLayout, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer, QUrl
from PyQt6.QtGui import QDesktopServices

from cachy_control.core.service_registry import ServiceRegistry
from cachy_control.ui.components.sharp_card import SharpCard
from cachy_control.ui.components.sharp_button import SharpButton
from cachy_control.ui.components.dependency_button import DependencyButton
from cachy_control.ui.components.stat_gauge import StatGauge
from cachy_control.ui.components.section_badge import SectionBadge
from cachy_control.ui.theme import THEMES

class DashboardView(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.services = ServiceRegistry.get()
        self._is_server_running = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Row
        header = QHBoxLayout()
        header.addWidget(SectionBadge("dashboard", "SYSTEM OVERVIEW & COCKPIT"))
        header.addStretch()
        self.refresh_btn = SharpButton("Refresh", icon_name="refresh", variant="outline")
        self.refresh_btn.clicked.connect(self._refresh_all)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        # Sub-Module Filter Tabs at the Top
        subtab_row = QHBoxLayout()
        subtab_row.setSpacing(8)

        self.subtab_configs = [
            ("metrics", "Live Hardware", "cpu"),
            ("launchers", "Monitoring Launchers", "terminal"),
            ("servers", "Local Dev Servers", "network"),
            ("tools", "Java & Timers", "sliders"),
            ("all", "Show All", "package"),
        ]
        self.subtab_buttons = {}
        for key, label, icon in self.subtab_configs:
            btn = SharpButton(label, icon_name=icon, variant="outline" if key != "metrics" else "primary")
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

        # 1. Hardware & Memory Metrics Card
        self.metrics_card = SharpCard("Live Hardware & Memory", "Real-time CPU, RAM, Swap and ZRAM allocation")
        m_grid = QGridLayout()
        m_grid.setHorizontalSpacing(24)
        m_grid.setVerticalSpacing(12)

        self.cpu_gauge = StatGauge("CPU Load", "%")
        self.ram_gauge = StatGauge("RAM Allocation", "%")
        self.swap_gauge = StatGauge("Swap / ZRAM", "%")

        m_grid.addWidget(self.cpu_gauge, 0, 0)
        m_grid.addWidget(self.ram_gauge, 0, 1)
        m_grid.addWidget(self.swap_gauge, 0, 2)

        self.metrics_card.add_layout(m_grid)
        self.c_layout.addWidget(self.metrics_card)

        # 2. Monitoring & Diagnostic Launchers Card
        self.launchers_card = SharpCard("System Monitoring & Diagnostic Launchers", "Terminal-based diagnostic tools with instant dependency checks")
        btn_grid = QGridLayout()
        btn_grid.setHorizontalSpacing(10)
        btn_grid.setVerticalSpacing(10)

        self.btop_btn = DependencyButton("btop", "btop Monitor", lambda: self.services.runner.run_in_terminal("btop"), icon_name="cpu", variant="primary")
        self.nvtop_btn = DependencyButton("nvtop", "nvtop GPU", lambda: self.services.runner.run_in_terminal("nvtop"), icon_name="sliders", variant="primary")
        self.fastfetch_btn = DependencyButton("fastfetch", "fastfetch Info", lambda: self.services.runner.run_in_terminal("fastfetch; read -n1"), icon_name="terminal", variant="secondary")
        self.journal_btn = SharpButton("journalctl (Live)", icon_name="terminal", variant="outline")
        self.journal_btn.clicked.connect(lambda: self.services.runner.run_in_terminal("journalctl -f"))

        btn_grid.addWidget(self.btop_btn, 0, 0)
        btn_grid.addWidget(self.nvtop_btn, 0, 1)
        btn_grid.addWidget(self.fastfetch_btn, 0, 2)
        btn_grid.addWidget(self.journal_btn, 0, 3)

        self.launchers_card.add_layout(btn_grid)
        self.c_layout.addWidget(self.launchers_card)

        # 3. Local Web & Dev Servers Card
        self.servers_card = SharpCard("Local Web & Project Dev Servers", "Start or control background development servers (pnpm / npm / yarn / bun / Vite / Python / custom)")
        s_layout = QVBoxLayout()
        s_layout.setSpacing(12)

        # Row 1: Directory Selection
        d_row = QHBoxLayout()
        d_row.setSpacing(10)
        d_title = QLabel("Project Folder:")
        d_title.setStyleSheet("font-size: 12px; font-weight: 700;")
        d_row.addWidget(d_title)

        default_dir = self.services.settings.get("dev_server_dir", str(Path.home() / "Projects" if (Path.home() / "Projects").exists() else Path.home()))
        if not os.path.exists(default_dir):
            default_dir = str(Path.home())

        self.srv_dir_input = QLineEdit(default_dir)
        self.srv_dir_input.setPlaceholderText("Path to web project or static directory...")
        self.srv_dir_input.textChanged.connect(self._on_dir_changed)
        d_row.addWidget(self.srv_dir_input, 1)

        self.browse_srv_btn = SharpButton("Browse...", icon_name="folder", variant="outline")
        self.browse_srv_btn.clicked.connect(self._browse_srv_dir)
        d_row.addWidget(self.browse_srv_btn)
        s_layout.addLayout(d_row)

        # Row 2: Runner Type + Port + Custom Cmd
        cfg_row = QHBoxLayout()
        cfg_row.setSpacing(10)

        r_title = QLabel("Dev Runner:")
        r_title.setStyleSheet("font-size: 12px; font-weight: 700;")
        cfg_row.addWidget(r_title)

        self.runner_combo = QComboBox()
        self.runner_combo.addItem("pnpm run dev", "pnpm")
        self.runner_combo.addItem("npm run dev", "npm")
        self.runner_combo.addItem("yarn dev", "yarn")
        self.runner_combo.addItem("bun dev", "bun")
        self.runner_combo.addItem("Vite Dev Server (npx vite)", "vite")
        self.runner_combo.addItem("Python HTTP Server", "python_http")
        self.runner_combo.addItem("Cargo Run (Rust)", "cargo")
        self.runner_combo.addItem("Go Run (Golang)", "go")
        self.runner_combo.addItem("Custom Command", "custom")
        self.runner_combo.currentIndexChanged.connect(self._on_runner_changed)
        cfg_row.addWidget(self.runner_combo)

        p_title = QLabel("Port:")
        p_title.setStyleSheet("font-size: 12px; font-weight: 700;")
        cfg_row.addWidget(p_title)

        self.port_combo = QComboBox()
        self.port_combo.setEditable(True)  # allow typing a custom port
        self.port_combo.setFixedWidth(100)
        for port_val, port_label in [
            (5173, "5173 — Vite"),
            (3000, "3000 — Node/pnpm"),
            (8080, "8080 — Python"),
            (8000, "8000 — Django/FastAPI"),
            (4200, "4200 — Angular"),
            (4321, "4321 — Astro"),
            (1420, "1420 — Tauri"),
            (3001, "3001 — Alt Node"),
        ]:
            self.port_combo.addItem(port_label, port_val)
        cfg_row.addWidget(self.port_combo)

        self.custom_cmd_input = QLineEdit()
        self.custom_cmd_input.setPlaceholderText("Custom command (e.g. uvicorn main:app --reload)...")
        self.custom_cmd_input.hide()
        cfg_row.addWidget(self.custom_cmd_input, 1)

        cfg_row.addStretch()
        s_layout.addLayout(cfg_row)

        # Row 3: Action Buttons
        act_row = QHBoxLayout()
        act_row.setSpacing(10)

        self.toggle_srv_btn = SharpButton("Start Dev Server", icon_name="play", variant="primary")
        self.toggle_srv_btn.clicked.connect(self._toggle_dev_server)
        act_row.addWidget(self.toggle_srv_btn)

        self.open_browser_btn = SharpButton("Open in Browser", icon_name="external_link", variant="secondary")
        self.open_browser_btn.clicked.connect(self._open_in_browser)
        self.open_browser_btn.setEnabled(False)
        act_row.addWidget(self.open_browser_btn)

        self.open_folder_btn = SharpButton("Open Folder", icon_name="folder", variant="outline")
        self.open_folder_btn.clicked.connect(self._open_project_folder)
        act_row.addWidget(self.open_folder_btn)

        act_row.addStretch()
        s_layout.addLayout(act_row)

        self.servers_card.add_layout(s_layout)
        self.c_layout.addWidget(self.servers_card)

        # 4. Java Version & Power Control Card
        self.tools_card = SharpCard("Java Version Switcher & System Timers", "Configure default Arch Linux JVM environment or scheduled power timers")
        t_grid = QGridLayout()
        t_grid.setHorizontalSpacing(16)
        t_grid.setVerticalSpacing(12)

        # Java switcher
        j_row = QHBoxLayout()
        j_row.addWidget(QLabel("Default Java Environment:"))
        self.java_combo = QComboBox()
        self._populate_java_versions()
        j_row.addWidget(self.java_combo, 1)

        self.set_java_btn = SharpButton("Apply Java Default", icon_name="check", variant="primary")
        self.set_java_btn.clicked.connect(self._apply_java)
        j_row.addWidget(self.set_java_btn)
        t_grid.addLayout(j_row, 0, 0)

        # Timed Shutdown row
        p_row = QHBoxLayout()
        p_row.addWidget(QLabel("Scheduled Shutdown in:"))
        self.shutdown_spin = QSpinBox()
        self.shutdown_spin.setRange(1, 1440)
        self.shutdown_spin.setValue(60)
        self.shutdown_spin.setSuffix(" mins")
        p_row.addWidget(self.shutdown_spin)

        self.shutdown_btn = SharpButton("Schedule Shutdown", icon_name="power", variant="danger")
        self.shutdown_btn.clicked.connect(self._schedule_shutdown)
        p_row.addWidget(self.shutdown_btn)

        self.cancel_shutdown_btn = SharpButton("Cancel Timer", icon_name="cross", variant="outline")
        self.cancel_shutdown_btn.clicked.connect(self._cancel_shutdown)
        p_row.addWidget(self.cancel_shutdown_btn)
        t_grid.addLayout(p_row, 0, 1)

        self.tools_card.add_layout(t_grid)
        self.c_layout.addWidget(self.tools_card)

        self.c_layout.addStretch()
        self.scroll.setWidget(container)
        layout.addWidget(self.scroll)

        # Timer for polling system metrics
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._poll_metrics)
        metrics_interval_ms = self.services.settings.get("metrics_poll_interval_ms", 5000)
        self.timer.start(max(1000, int(metrics_interval_ms)))

        self._on_dir_changed()
        self._switch_sub_tab("metrics")
        QTimer.singleShot(0, self._refresh_all)

    def _switch_sub_tab(self, active_key: str):
        self.active_sub_tab = active_key
        t_key = self.services.settings.get("theme", "light")
        for key, btn in self.subtab_buttons.items():
            btn.variant = "primary" if key == active_key else "outline"
            btn.apply_style(t_key)

        show_all = (active_key == "all")
        self.metrics_card.setVisible(show_all or active_key == "metrics")
        self.launchers_card.setVisible(show_all or active_key == "launchers")
        self.servers_card.setVisible(show_all or active_key == "servers")
        self.tools_card.setVisible(show_all or active_key == "tools")

    def _refresh_all(self):
        self._poll_metrics()
        self.btop_btn.refresh_state()
        self.nvtop_btn.refresh_state()
        self.fastfetch_btn.refresh_state()

    def _poll_metrics(self):
        metrics = self.services.system.get_metrics()
        self.cpu_gauge.set_value(metrics.cpu_percent, f"{metrics.cpu_percent:.1f}% ({metrics.cpu_cores} Cores)")
        self.ram_gauge.set_value(metrics.ram_percent, f"{metrics.ram_used_gb:.1f} / {metrics.ram_total_gb:.1f} GB")
        self.swap_gauge.set_value(metrics.swap_percent, f"{metrics.swap_used_gb:.1f} / {metrics.swap_total_gb:.1f} GB")

    def _browse_srv_dir(self):
        current = self.srv_dir_input.text().strip()
        dir_path = QFileDialog.getExistingDirectory(self, "Select Project Directory", current)
        if dir_path:
            self.srv_dir_input.setText(dir_path)
            self.services.settings.set("dev_server_dir", dir_path)
            self._on_dir_changed()

    def _on_dir_changed(self):
        dir_path = self.srv_dir_input.text().strip()
        if not os.path.isdir(dir_path):
            return
        detected = self.services.dev_server.detect_project_runner(dir_path)
        for idx in range(self.runner_combo.count()):
            if self.runner_combo.itemData(idx) == detected:
                self.runner_combo.setCurrentIndex(idx)
                break

    def _get_port(self) -> int:
        """Reads port from the editable combo — handles both dropdown and typed values."""
        text = self.port_combo.currentText().split("—")[0].strip()
        try:
            return max(1, min(65535, int(text)))
        except ValueError:
            return 5173

    def _on_runner_changed(self):
        runner_key = self.runner_combo.currentData()
        if runner_key == "custom":
            self.custom_cmd_input.show()
        else:
            self.custom_cmd_input.hide()

        # Update recommended default port by selecting matching combo entry
        port_map = {
            "pnpm": 3000, "npm": 3000, "yarn": 3000, "bun": 3000,
            "vite": 5173, "python_http": 8080,
        }
        if runner_key in port_map:
            target = port_map[runner_key]
            for i in range(self.port_combo.count()):
                if self.port_combo.itemData(i) == target:
                    self.port_combo.setCurrentIndex(i)
                    break

    def _toggle_dev_server(self):
        if self._is_server_running and self.services.runner.is_running():
            self.services.runner.cancel_current()
            self._is_server_running = False
            self.toggle_srv_btn.set_clean_text("Start Dev Server")
            self.toggle_srv_btn.variant = "primary"
            self.toggle_srv_btn.apply_style()
            self.open_browser_btn.setEnabled(False)
        else:
            directory = self.srv_dir_input.text().strip()
            if not os.path.isdir(directory):
                directory = str(Path.home())
            self.services.settings.set("dev_server_dir", directory)

            runner_key = self.runner_combo.currentData()
            port = self._get_port()
            custom_cmd = self.custom_cmd_input.text().strip()

            cmd = self.services.dev_server.get_command(runner_key, directory, port, custom_cmd)
            self.services.runner.run_command(
                cmd,
                on_finish=self._on_server_finished,
                cwd=directory,
            )
            # Set this only after run_command has cancelled any prior process.
            self._is_server_running = self.services.runner.is_running()
            if self._is_server_running:
                self.toggle_srv_btn.set_clean_text("Stop Dev Server")
                self.toggle_srv_btn.variant = "danger"
                self.toggle_srv_btn.apply_style()
                self.open_browser_btn.setEnabled(True)

    def _on_server_finished(self, exit_code: int):
        if self._is_server_running:
            self._is_server_running = False
            self.toggle_srv_btn.set_clean_text("Start Dev Server")
            self.toggle_srv_btn.variant = "primary"
            self.toggle_srv_btn.apply_style()
            self.open_browser_btn.setEnabled(False)

    def _open_in_browser(self):
        port = self._get_port()
        QDesktopServices.openUrl(QUrl(f"http://localhost:{port}"))

    def _open_project_folder(self):
        directory = self.srv_dir_input.text().strip()
        if os.path.isdir(directory):
            safe_dir = shlex.quote(directory)
            self.services.runner.run_command(f"dolphin {safe_dir} 2>/dev/null || xdg-open {safe_dir} &")

    def _populate_java_versions(self):
        raw_lines = self.services.system.get_java_versions()
        self.java_combo.clear()
        for line in raw_lines:
            if "Available" in line or "detected" in line or "Error" in line:
                continue
            clean = line.replace("(default)", "").strip()
            if clean:
                self.java_combo.addItem(line, clean)
        if self.java_combo.count() == 0:
            self.java_combo.addItem("Default System JVM", "default")

    def _apply_java(self):
        env_name = self.java_combo.currentData()
        if env_name and env_name != "default":
            cmd = f"sudo archlinux-java set {env_name}"
            self.services.runner.run_command(cmd)

    def _schedule_shutdown(self):
        mins = self.shutdown_spin.value()
        cmd = self.services.system.schedule_shutdown(mins)
        self.services.runner.run_command(cmd)

    def _cancel_shutdown(self):
        cmd = self.services.system.cancel_shutdown()
        self.services.runner.run_command(cmd)
