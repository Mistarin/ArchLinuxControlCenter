"""
Audio & Bluetooth Management View.
Equipped with top sub-module tabs and unclipped device table rows.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QScrollArea
)
from PyQt6.QtCore import Qt

from cachy_control.core.service_registry import ServiceRegistry
from cachy_control.ui.components.sharp_card import SharpCard
from cachy_control.ui.components.sharp_button import SharpButton
from cachy_control.ui.components.section_badge import SectionBadge
from cachy_control.ui.theme import THEMES

class AudioBtView(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.services = ServiceRegistry.get()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Row
        header = QHBoxLayout()
        header.addWidget(SectionBadge("audio_bt", "AUDIO & BLUETOOTH COCKPIT"))
        header.addStretch()
        self.refresh_btn = SharpButton("Refresh Devices", icon_name="refresh", variant="outline")
        self.refresh_btn.clicked.connect(self._refresh_all)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        # Sub-Module Filter Tabs at the Top
        subtab_row = QHBoxLayout()
        subtab_row.setSpacing(8)

        self.subtab_configs = [
            ("bt", "Bluetooth Devices & Control", "sliders"),
            ("audio", "PipeWire Audio Nodes", "sliders"),
            ("all", "Show All", "package"),
        ]
        self.subtab_buttons = {}
        for key, label, icon in self.subtab_configs:
            btn = SharpButton(label, icon_name=icon, variant="outline" if key != "bt" else "primary")
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

        # 1. Bluetooth Actions Bar
        self.bt_ctrl_card = SharpCard("Bluetooth Operations & Service", "Quick power toggles, daemon restarts and auto-connect service")
        b_row = QHBoxLayout()
        b_row.setSpacing(10)

        self.restart_bt_btn = SharpButton("Restart Bluetooth Service", icon_name="refresh", variant="secondary")
        self.restart_bt_btn.clicked.connect(self._restart_bt)
        b_row.addWidget(self.restart_bt_btn)

        self.scan_on_btn = SharpButton("Start Device Scan (10s)", icon_name="search", variant="primary")
        self.scan_on_btn.clicked.connect(self._scan_bt)
        b_row.addWidget(self.scan_on_btn)

        self.autoconnect_btn = SharpButton("Enable User Auto-Connect Service", icon_name="check", variant="outline")
        self.autoconnect_btn.clicked.connect(self._setup_autoconnect)
        b_row.addWidget(self.autoconnect_btn)

        b_row.addStretch()
        self.bt_ctrl_card.add_layout(b_row)
        self.c_layout.addWidget(self.bt_ctrl_card)

        # 2. Paired Bluetooth Devices Table
        self.bt_table_card = SharpCard("Paired & Discovered Bluetooth Devices", "Manage individual Bluetooth device connections")
        self.bt_table = QTableWidget(0, 4)
        self.bt_table.setHorizontalHeaderLabels(["DEVICE NAME", "MAC ADDRESS", "STATUS", "ACTION"])
        self.bt_table.verticalHeader().setVisible(False)
        self.bt_table.verticalHeader().setDefaultSectionSize(44)
        self.bt_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.bt_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.bt_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.bt_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.bt_table.setColumnWidth(3, 140)
        self.bt_table.setMinimumHeight(220)
        self.bt_table.setAlternatingRowColors(True)
        self.bt_table_card.add_widget(self.bt_table)
        self.c_layout.addWidget(self.bt_table_card)

        # 3. PipeWire Audio Nodes Table
        self.audio_card = SharpCard("PipeWire Audio Endpoints (Sinks & Sources)", "Real-time audio devices detected by pactl")
        self.audio_table = QTableWidget(0, 4)
        self.audio_table.setHorizontalHeaderLabels(["ID", "DEVICE / STREAM NAME", "TYPE", "ACTION"])
        self.audio_table.verticalHeader().setVisible(False)
        self.audio_table.verticalHeader().setDefaultSectionSize(44)
        self.audio_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.audio_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.audio_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.audio_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.audio_table.setColumnWidth(3, 140)
        self.audio_table.setMinimumHeight(240)
        self.audio_table.setAlternatingRowColors(True)
        self.audio_card.add_widget(self.audio_table)
        self.c_layout.addWidget(self.audio_card)

        self.c_layout.addStretch()
        self.scroll.setWidget(container)
        layout.addWidget(self.scroll)

        self._switch_sub_tab("bt")
        self._refresh_all()

    def _switch_sub_tab(self, active_key: str):
        self.active_sub_tab = active_key
        t_key = self.services.settings.get("theme", "light")
        for key, btn in self.subtab_buttons.items():
            btn.variant = "primary" if key == active_key else "outline"
            btn.apply_style(t_key)

        show_all = (active_key == "all")
        self.bt_ctrl_card.setVisible(show_all or active_key == "bt")
        self.bt_table_card.setVisible(show_all or active_key == "bt")
        self.audio_card.setVisible(show_all or active_key == "audio")

    def _refresh_all(self):
        self._render_bt_devices()
        self._render_audio_nodes()

    def _render_bt_devices(self):
        devices = self.services.audio_bt.get_bluetooth_devices()
        self.bt_table.setRowCount(len(devices))

        for row, dev in enumerate(devices):
            name_item = QTableWidgetItem(dev.name)
            mac_item = QTableWidgetItem(dev.mac)
            status_str = "Connected" if dev.connected else "Disconnected"
            status_item = QTableWidgetItem(status_str)

            self.bt_table.setItem(row, 0, name_item)
            self.bt_table.setItem(row, 1, mac_item)
            self.bt_table.setItem(row, 2, status_item)

            act_container = QWidget()
            act_layout = QHBoxLayout(act_container)
            act_layout.setContentsMargins(4, 4, 4, 4)
            act_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            if dev.connected:
                btn = SharpButton("Disconnect", icon_name="cross", variant="danger")
                btn.setFixedHeight(28)
                btn.clicked.connect(lambda _, m=dev.mac: self._disconnect_bt(m))
            else:
                btn = SharpButton("Connect", icon_name="check", variant="primary")
                btn.setFixedHeight(28)
                btn.clicked.connect(lambda _, m=dev.mac: self._connect_bt(m))

            act_layout.addWidget(btn)
            self.bt_table.setCellWidget(row, 3, act_container)

    def _render_audio_nodes(self):
        nodes = self.services.audio_bt.get_audio_nodes()
        self.audio_table.setRowCount(len(nodes))

        for row, n in enumerate(nodes):
            id_item = QTableWidgetItem(str(n.id))
            name_item = QTableWidgetItem(n.name)
            type_item = QTableWidgetItem(n.node_type)

            self.audio_table.setItem(row, 0, id_item)
            self.audio_table.setItem(row, 1, name_item)
            self.audio_table.setItem(row, 2, type_item)

            act_container = QWidget()
            act_layout = QHBoxLayout(act_container)
            act_layout.setContentsMargins(4, 4, 4, 4)
            act_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            def_btn = SharpButton("Set Default", icon_name="check", variant="outline")
            def_btn.setFixedHeight(28)
            def_btn.clicked.connect(lambda _, nid=n.id: self._set_default_audio(nid))
            act_layout.addWidget(def_btn)

            self.audio_table.setCellWidget(row, 3, act_container)

    def _restart_bt(self):
        cmd = self.services.audio_bt.get_restart_bluetooth_command()
        self.services.runner.run_command(cmd, on_finish=lambda _: self._refresh_all())

    def _scan_bt(self):
        cmd = self.services.audio_bt.get_scan_command()
        self.services.runner.run_command(cmd, on_finish=lambda _: self._refresh_all())

    def _setup_autoconnect(self):
        cmd = self.services.audio_bt.get_autoconnect_command()
        self.services.runner.run_command(cmd)

    def _connect_bt(self, mac: str):
        cmd = self.services.audio_bt.get_connect_command(mac)
        self.services.runner.run_command(cmd, on_finish=lambda _: self._refresh_all())

    def _disconnect_bt(self, mac: str):
        cmd = self.services.audio_bt.get_disconnect_command(mac)
        self.services.runner.run_command(cmd, on_finish=lambda _: self._refresh_all())

    def _set_default_audio(self, node_id: int):
        cmd = self.services.audio_bt.get_set_default_sink_command(node_id)
        self.services.runner.run_command(cmd, on_finish=lambda _: self._refresh_all())
