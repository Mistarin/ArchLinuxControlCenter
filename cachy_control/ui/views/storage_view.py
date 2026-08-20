"""
Storage, Cloud Mounts & Steam AppData View.
Equipped with top sub-module tabs for focused organization.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QFileDialog, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QTimer

from cachy_control.core.service_registry import ServiceRegistry
from cachy_control.ui.components.sharp_card import SharpCard
from cachy_control.ui.components.sharp_button import SharpButton
from cachy_control.ui.components.stat_gauge import StatGauge
from cachy_control.ui.components.section_badge import SectionBadge
from cachy_control.ui.theme import THEMES

class StorageView(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.services = ServiceRegistry.get()
        self.path_inputs = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Row
        header = QHBoxLayout()
        header.addWidget(SectionBadge("storage", "STORAGE, CLOUD DRIVES & DISK HEALTH"))
        header.addStretch()
        
        self.refresh_btn = SharpButton("Refresh", icon_name="refresh", variant="outline")
        self.refresh_btn.clicked.connect(self._refresh_all)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        # Sub-Module Filter Tabs at the Top
        subtab_row = QHBoxLayout()
        subtab_row.setSpacing(8)

        self.subtab_configs = [
            ("cloud", "Cloud Drives (Rclone)", "cloud"),
            ("disks", "Disk Partitions & Space", "sliders"),
            ("steam", "Steam AppData & Prefixes", "folder"),
            ("all", "Show All", "sliders"),
        ]
        self.subtab_buttons = {}
        for key, label, icon in self.subtab_configs:
            btn = SharpButton(label, icon_name=icon, variant="outline" if key != "cloud" else "primary")
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

        # 1. Rclone Cloud Drives Card
        self.cloud_card = SharpCard("Cloud Drives (Rclone VFS)", "Mount and manage Google Drive or remote cloud storage in Dolphin")
        
        c_head_row = QHBoxLayout()
        c_head_row.addWidget(QLabel("Configured Remotes & Mount Points:"))
        c_head_row.addStretch()

        self.rclone_wizard_btn = SharpButton("Interactive Rclone Setup (Wizard)", icon_name="terminal", variant="outline")
        self.rclone_wizard_btn.clicked.connect(self._launch_rclone_config)
        c_head_row.addWidget(self.rclone_wizard_btn)
        self.cloud_card.add_layout(c_head_row)

        self.cloud_list_layout = QVBoxLayout()
        self.cloud_list_layout.setSpacing(8)
        self.cloud_card.add_layout(self.cloud_list_layout)
        self.c_layout.addWidget(self.cloud_card)

        # 2. Local Disk Partitions & Space Card
        self.disks_card = SharpCard("Local Disk Partitions & Space", "Mounted physical filesystems and NVMe/SATA volume capacity")
        self.disks_layout = QVBoxLayout()
        self.disks_layout.setSpacing(8)
        self.disks_card.add_layout(self.disks_layout)
        self.c_layout.addWidget(self.disks_card)

        # 3. Steam Proton Prefix / AppData Quick Shortcuts
        self.steam_card = SharpCard("Steam Proton AppData Quick Shortcuts", "Quick access to Windows AppData folders inside Proton prefixes")
        s_layout = QVBoxLayout()
        s_layout.setSpacing(12)

        # NMS Row
        nms_row = QHBoxLayout()
        nms_info = QVBoxLayout()
        nms_title = QLabel("No Man's Sky (AppID 275850) Saves & AppData")
        nms_title.setStyleSheet("font-weight: 700; font-size: 12px;")
        nms_path_label = QLabel(".../compatdata/275850/pfx/drive_c/users/steamuser/AppData/Roaming/HelloGames/NMS/")
        nms_path_label.setStyleSheet("opacity: 0.85; font-size: 11px;")
        nms_info.addWidget(nms_title)
        nms_info.addWidget(nms_path_label)
        nms_row.addLayout(nms_info)
        nms_row.addStretch()

        nms_btn = SharpButton("Open in Dolphin", icon_name="folder", variant="secondary")
        nms_btn.clicked.connect(self._open_nms_appdata)
        nms_row.addWidget(nms_btn)
        s_layout.addLayout(nms_row)

        # General CompatData directory row
        gen_row = QHBoxLayout()
        gen_info = QVBoxLayout()
        gen_title = QLabel("All Steam Proton Prefixes (compatdata)")
        gen_title.setStyleSheet("font-weight: 700; font-size: 12px;")
        gen_path_label = QLabel("~/.local/share/Steam/steamapps/compatdata/")
        gen_path_label.setStyleSheet("opacity: 0.85; font-size: 11px;")
        gen_info.addWidget(gen_title)
        gen_info.addWidget(gen_path_label)
        gen_row.addLayout(gen_info)
        gen_row.addStretch()

        gen_btn = SharpButton("Open in Dolphin", icon_name="folder", variant="outline")
        gen_btn.clicked.connect(self._open_compatdata)
        gen_row.addWidget(gen_btn)
        s_layout.addLayout(gen_row)

        self.steam_card.add_layout(s_layout)
        self.c_layout.addWidget(self.steam_card)

        self.c_layout.addStretch()
        self.scroll.setWidget(container)
        layout.addWidget(self.scroll)

        self._switch_sub_tab("cloud")
        QTimer.singleShot(0, self._refresh_all)

    def _switch_sub_tab(self, active_key: str):
        self.active_sub_tab = active_key
        t_key = self.services.settings.get("theme", "light")
        for key, btn in self.subtab_buttons.items():
            btn.variant = "primary" if key == active_key else "outline"
            btn.apply_style(t_key)

        show_all = (active_key == "all")
        self.cloud_card.setVisible(show_all or active_key == "cloud")
        self.disks_card.setVisible(show_all or active_key == "disks")
        self.steam_card.setVisible(show_all or active_key == "steam")

    def _refresh_all(self):
        self._render_cloud_mounts()
        self._render_disk_partitions()

    def _render_cloud_mounts(self):
        while self.cloud_list_layout.count():
            item = self.cloud_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget(): sub.widget().deleteLater()

        mounts = self.services.storage.get_cloud_mounts()
        for mount in mounts:
            row = QHBoxLayout()
            row.setSpacing(10)

            name_lbl = QLabel(f"Remote: <b>{mount.remote_name}</b>")
            name_lbl.setFixedWidth(130)
            row.addWidget(name_lbl)

            path_input = QLineEdit(mount.mount_point)
            path_input.setPlaceholderText("Select mount directory path...")
            self.path_inputs[mount.remote_name] = path_input
            row.addWidget(path_input, 1)

            browse_btn = SharpButton("Browse...", icon_name="folder", variant="outline")
            browse_btn.clicked.connect(lambda _, r=mount.remote_name: self._browse_mount_path(r))
            row.addWidget(browse_btn)

            if mount.is_mounted:
                unmount_btn = SharpButton("Unmount", icon_name="cross", variant="danger")
                unmount_btn.clicked.connect(lambda _, p=mount.mount_point: self._unmount_cloud(p))
                row.addWidget(unmount_btn)

                open_btn = SharpButton("Open Folder", icon_name="folder", variant="secondary")
                open_btn.clicked.connect(lambda _, p=mount.mount_point: self._open_dir(p))
                row.addWidget(open_btn)
            else:
                mount_btn = SharpButton("Mount (VFS Daemon)", icon_name="cloud", variant="primary")
                mount_btn.clicked.connect(lambda _, m=mount: self._mount_cloud(m.remote_name, path_input.text().strip()))
                row.addWidget(mount_btn)

                reauth_btn = SharpButton("Refresh Token / Reconnect", icon_name="refresh", variant="outline")
                reauth_btn.clicked.connect(lambda _, r=mount.remote_name: self._reconnect_remote(r))
                row.addWidget(reauth_btn)

            self.cloud_list_layout.addLayout(row)

    def _browse_mount_path(self, remote: str):
        if remote in self.path_inputs:
            current = self.path_inputs[remote].text().strip()
            chosen = QFileDialog.getExistingDirectory(self, f"Select Mount Directory for {remote}", current)
            if chosen:
                self.path_inputs[remote].setText(chosen)

    def _render_disk_partitions(self):
        while self.disks_layout.count():
            item = self.disks_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    sub = item.layout().takeAt(0)
                    if sub.widget(): sub.widget().deleteLater()

        partitions = self.services.storage.get_disk_partitions()
        for p in partitions:
            gauge = StatGauge(f"{p.device} ({p.mountpoint}) - {p.fstype}", "%")
            gauge.set_value(p.percent, f"{p.used_gb:.1f} / {p.total_gb:.1f} GB ({p.free_gb:.1f} GB free)")
            self.disks_layout.addWidget(gauge)

    def _mount_cloud(self, remote: str, path: str):
        cmd = self.services.storage.get_mount_command(remote, path)
        self.services.runner.run_command(cmd, on_finish=lambda _: self._refresh_all())

    def _unmount_cloud(self, path: str):
        cmd = self.services.storage.get_unmount_command(path)
        self.services.runner.run_command(cmd, on_finish=lambda _: self._refresh_all())

    def _reconnect_remote(self, remote: str):
        cmd = self.services.storage.get_reconnect_command(remote)
        self.services.runner.run_command(cmd)

    def _launch_rclone_config(self):
        cmd = self.services.storage.get_rclone_config_command()
        self.services.runner.run_command(cmd)

    def _open_dir(self, path: str):
        expanded = str(Path(path).expanduser())
        self.services.runner.run_command(f"dolphin '{expanded}' &")

    def _open_nms_appdata(self):
        path = str(Path.home() / ".local" / "share" / "Steam" / "steamapps" / "compatdata" / "275850" / "pfx" / "drive_c" / "users" / "steamuser" / "AppData" / "Roaming" / "HelloGames" / "NMS")
        self.services.runner.run_command(f"mkdir -p '{path}' && dolphin '{path}' &")

    def _open_compatdata(self):
        path = str(Path.home() / ".local" / "share" / "Steam" / "steamapps" / "compatdata")
        self.services.runner.run_command(f"mkdir -p '{path}' && dolphin '{path}' &")
