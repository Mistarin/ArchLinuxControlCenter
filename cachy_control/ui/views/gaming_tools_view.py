"""
Gaming, UMU Launcher, Minecraft Server & Custom Script Runners.
Equipped with top sub-module tabs and unclipped process doctor tables.
"""

import shlex
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QSpinBox, QFileDialog, QTableWidget, QTableWidgetItem,
    QHeaderView, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QTimer

from cachy_control.core.service_registry import ServiceRegistry
from cachy_control.ui.components.sharp_card import SharpCard
from cachy_control.ui.components.sharp_button import SharpButton
from cachy_control.ui.components.dependency_button import DependencyButton
from cachy_control.ui.components.section_badge import SectionBadge
from cachy_control.ui.components.confirm_dialog import confirm_destructive_action
from cachy_control.ui.theme import THEMES, DESTRUCTIVE_RED

class GamingToolsView(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.services = ServiceRegistry.get()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Row
        header = QHBoxLayout()
        header.addWidget(SectionBadge("gaming", "GAMING, UMU & RUNNERS"))
        header.addStretch()
        layout.addLayout(header)

        # Sub-Module Filter Tabs at the Top
        subtab_row = QHBoxLayout()
        subtab_row.setSpacing(8)

        self.subtab_configs = [
            ("umu", "UMU Proton Runner", "play"),
            ("minecraft", "Minecraft Server", "terminal"),
            ("kill", "Process Killer Doctor", "stop"),
            ("all", "Show All", "sliders"),
        ]
        self.subtab_buttons = {}
        for key, label, icon in self.subtab_configs:
            btn = SharpButton(label, icon_name=icon, variant="outline" if key != "umu" else "primary")
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

        # 1. UMU Runner Card
        self.umu_card = SharpCard("Unified Linux Wine / Proton Game Runner (UMU)", "Universal Proton game launcher wrapper")
        self.umu_container_layout = QVBoxLayout()
        self.umu_card.add_layout(self.umu_container_layout)
        self.c_layout.addWidget(self.umu_card)

        # 2. Minecraft Dedicated Server Manager
        self.mc_card = SharpCard("Minecraft Dedicated Server Manager", "Launch and control local Java server instances")
        mc_layout = QVBoxLayout()
        mc_layout.setSpacing(10)

        # Path row
        p_row = QHBoxLayout()
        p_row.addWidget(QLabel("Server Directory:"))
        default_mc = self.services.settings.get("minecraft_server_path", str(Path.home() / "MinecraftServer"))
        self.mc_path_input = QLineEdit(default_mc)
        p_row.addWidget(self.mc_path_input, 1)

        browse_btn = SharpButton("Browse...", icon_name="folder", variant="outline")
        browse_btn.clicked.connect(self._browse_mc_dir)
        p_row.addWidget(browse_btn)
        mc_layout.addLayout(p_row)

        # Config Row
        c_row = QHBoxLayout()
        c_row.setSpacing(16)

        c_row.addWidget(QLabel("Min RAM (GB):"))
        self.min_ram_spin = QSpinBox()
        self.min_ram_spin.setRange(1, 64)
        self.min_ram_spin.setValue(self.services.settings.get("minecraft_min_ram", 4))
        c_row.addWidget(self.min_ram_spin)

        c_row.addWidget(QLabel("Max RAM (GB):"))
        self.max_ram_spin = QSpinBox()
        self.max_ram_spin.setRange(1, 64)
        self.max_ram_spin.setValue(self.services.settings.get("minecraft_max_ram", 8))
        c_row.addWidget(self.max_ram_spin)

        c_row.addStretch()

        self.start_mc_btn = SharpButton("Start Server (Interactive Terminal)", icon_name="play", variant="primary")
        self.start_mc_btn.clicked.connect(self._start_minecraft)
        c_row.addWidget(self.start_mc_btn)

        self.open_mc_btn = SharpButton("Open Dir in Dolphin", icon_name="folder", variant="outline")
        self.open_mc_btn.clicked.connect(self._open_mc_dir)
        c_row.addWidget(self.open_mc_btn)

        mc_layout.addLayout(c_row)
        self.mc_card.add_layout(mc_layout)
        self.c_layout.addWidget(self.mc_card)

        # 3. Process Killer Doctor Card
        self.kill_card = SharpCard("Process Killer Doctor", "Search and kill unresponsive game instances or rogue background processes")
        k_layout = QVBoxLayout()
        k_layout.setSpacing(10)

        f_row = QHBoxLayout()
        f_row.setSpacing(8)
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter processes by name (e.g. wine, steam, java, discord)...")
        self.filter_input.textChanged.connect(self._refresh_processes)
        f_row.addWidget(self.filter_input, 1)

        self.refresh_proc_btn = SharpButton("Refresh Processes", icon_name="refresh", variant="outline")
        self.refresh_proc_btn.clicked.connect(self._refresh_processes)
        f_row.addWidget(self.refresh_proc_btn)
        k_layout.addLayout(f_row)

        self.kill_table = QTableWidget(0, 5)
        self.kill_table.setHorizontalHeaderLabels(["PID", "USER", "CPU %", "COMMAND / PROCESS", "ACTION"])
        self.kill_table.verticalHeader().setVisible(False)
        self.kill_table.verticalHeader().setDefaultSectionSize(44)
        self.kill_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.kill_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.kill_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.kill_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.kill_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.kill_table.setColumnWidth(4, 140)
        self.kill_table.setMinimumHeight(280)
        self.kill_table.setAlternatingRowColors(True)
        k_layout.addWidget(self.kill_table)

        self.kill_card.add_layout(k_layout)
        self.c_layout.addWidget(self.kill_card)

        self.c_layout.addStretch()
        self.scroll.setWidget(container)
        layout.addWidget(self.scroll)

        self._switch_sub_tab("umu")
        QTimer.singleShot(0, self._refresh_umu_state)
        QTimer.singleShot(0, self._refresh_processes)

    def _switch_sub_tab(self, active_key: str):
        self.active_sub_tab = active_key
        t_key = self.services.settings.get("theme", "light")
        for key, btn in self.subtab_buttons.items():
            btn.variant = "primary" if key == active_key else "outline"
            btn.apply_style(t_key)

        show_all = (active_key == "all")
        self.umu_card.setVisible(show_all or active_key == "umu")
        self.mc_card.setVisible(show_all or active_key == "minecraft")
        self.kill_card.setVisible(show_all or active_key == "kill")

    def _refresh_umu_state(self):
        while self.umu_container_layout.count():
            item = self.umu_container_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget(): sub.widget().deleteLater()

        is_installed = self.services.gaming.is_umu_installed()
        if not is_installed:
            w_box = QVBoxLayout()
            w_box.setSpacing(8)
            w_title = QLabel("UMU Launcher is not installed")
            w_title.setStyleSheet(f"font-weight: 700; color: {DESTRUCTIVE_RED}; font-size: 12px;")
            w_desc = QLabel("UMU is required to launch Windows executables with proton/wine compatibility wrappers outside Steam.")
            w_desc.setStyleSheet("font-size: 11px; opacity: 0.85;")
            
            inst_btn = SharpButton("Install UMU (AUR: umu-launcher)", icon_name="download", variant="primary")
            inst_btn.clicked.connect(self._install_umu)

            w_box.addWidget(w_title)
            w_box.addWidget(w_desc)
            w_box.addWidget(inst_btn)
            self.umu_container_layout.addLayout(w_box)
        else:
            u_box = QVBoxLayout()
            u_box.setSpacing(10)

            exe_row = QHBoxLayout()
            exe_row.addWidget(QLabel("Executable (.exe):"))
            self.exe_path_input = QLineEdit()
            self.exe_path_input.setPlaceholderText("Select Windows game or launcher .exe...")
            exe_row.addWidget(self.exe_path_input, 1)

            browse_exe_btn = SharpButton("Browse...", icon_name="folder", variant="outline")
            browse_exe_btn.clicked.connect(self._browse_exe)
            exe_row.addWidget(browse_exe_btn)
            u_box.addLayout(exe_row)

            opt_row = QHBoxLayout()
            opt_row.setSpacing(16)

            opt_row.addWidget(QLabel("Game AppID / Verb:"))
            self.appid_input = QLineEdit("0")
            self.appid_input.setFixedWidth(100)
            opt_row.addWidget(self.appid_input)

            opt_row.addStretch()

            launch_btn = SharpButton("Launch Game with UMU", icon_name="play", variant="primary")
            launch_btn.clicked.connect(self._launch_umu_game)
            opt_row.addWidget(launch_btn)
            u_box.addLayout(opt_row)

            self.umu_container_layout.addLayout(u_box)

    def _browse_exe(self):
        chosen, _ = QFileDialog.getOpenFileName(self, "Select Executable", str(Path.home()), "Executables (*.exe);;All Files (*)")
        if chosen:
            self.exe_path_input.setText(chosen)

    def _browse_mc_dir(self):
        current = self.mc_path_input.text().strip()
        chosen = QFileDialog.getExistingDirectory(self, "Select Minecraft Server Directory", current)
        if chosen:
            self.mc_path_input.setText(chosen)
            self.services.settings.set("minecraft_server_path", chosen)

    def _start_minecraft(self):
        server_dir = self.mc_path_input.text().strip()
        min_ram = self.min_ram_spin.value()
        max_ram = self.max_ram_spin.value()
        self.services.settings.set("minecraft_server_path", server_dir)
        self.services.settings.set("minecraft_min_ram", min_ram)
        self.services.settings.set("minecraft_max_ram", max_ram)

        cmd = self.services.gaming.get_minecraft_start_command(server_dir, min_ram, max_ram)
        self.services.runner.run_command(cmd, cwd=server_dir)

    def _open_mc_dir(self):
        server_dir = self.mc_path_input.text().strip()
        self.services.runner.run_command(f"dolphin '{server_dir}' &")

    def _install_umu(self):
        cmd = self.services.gaming.get_umu_install_command()
        self.services.runner.run_command(cmd, on_finish=lambda _: self._refresh_umu_state())

    def _launch_umu_game(self):
        exe = self.exe_path_input.text().strip()
        appid = self.appid_input.text().strip()
        if not exe:
            return
        cmd = self.services.gaming.get_umu_launch_command(exe, appid)
        self.services.runner.run_command(cmd)

    def _refresh_processes(self):
        query = self.filter_input.text().strip()
        procs = self.services.gaming.get_running_processes(query)
        if not procs:
            self.kill_table.setRowCount(1)
            empty_item = QTableWidgetItem("No processes found matching filter.")
            empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.kill_table.setItem(0, 3, empty_item)
            for c_idx in (0, 1, 2, 4):
                self.kill_table.setItem(0, c_idx, QTableWidgetItem("-"))
            return
        self.kill_table.setRowCount(len(procs))

        for row, p in enumerate(procs):
            pid_item = QTableWidgetItem(str(p["pid"]))
            user_item = QTableWidgetItem(p["user"])
            cpu_item = QTableWidgetItem(p["cpu"])
            cmd_item = QTableWidgetItem(p["command"])

            self.kill_table.setItem(row, 0, pid_item)
            self.kill_table.setItem(row, 1, user_item)
            self.kill_table.setItem(row, 2, cpu_item)
            self.kill_table.setItem(row, 3, cmd_item)

            act_container = QWidget()
            act_layout = QHBoxLayout(act_container)
            act_layout.setContentsMargins(4, 4, 4, 4)
            act_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            kill_btn = SharpButton("Kill Process", icon_name="trash", variant="danger")
            kill_btn.setFixedHeight(28)
            kill_btn.clicked.connect(lambda _, pid=p["pid"], name=p["command"]: self._kill_process(pid, name))
            act_layout.addWidget(kill_btn)

            self.kill_table.setCellWidget(row, 4, act_container)

    def _kill_process(self, pid: int, name: str):
        if confirm_destructive_action(
            self,
            f"Kill Process PID {pid}",
            f"Are you sure you want to terminate process {pid} ({name[:50]})?",
            "Yes, Kill Process"
        ):
            cmd = self.services.gaming.get_kill_process_command(pid)
            self.services.runner.run_command(cmd, on_finish=lambda _: self._refresh_processes())
