"""
Network Diagnostics, Open Ports & Virsh/Libvirt VM Networks.
Equipped with top sub-module tabs and unclipped ports table.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget,
    QTableWidgetItem, QHeaderView, QScrollArea, QLineEdit
)
from PyQt6.QtCore import Qt, QTimer

from cachy_control.core.service_registry import ServiceRegistry
from cachy_control.ui.components.sharp_card import SharpCard
from cachy_control.ui.components.sharp_button import SharpButton
from cachy_control.ui.components.dependency_button import DependencyButton
from cachy_control.ui.components.section_badge import SectionBadge
from cachy_control.ui.theme import THEMES

class NetworkVmView(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.services = ServiceRegistry.get()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Row
        header = QHBoxLayout()
        header.addWidget(SectionBadge("network", "NETWORK DIAGNOSTICS & VIRTUAL MACHINES"))
        header.addStretch()
        self.refresh_btn = SharpButton("Refresh All", icon_name="refresh", variant="outline")
        self.refresh_btn.clicked.connect(self._refresh_all)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        # Sub-Module Filter Tabs at the Top
        subtab_row = QHBoxLayout()
        subtab_row.setSpacing(8)

        self.subtab_configs = [
            ("virsh", "Virtual VM Networks", "network"),
            ("ports", "Active Listening Ports", "sliders"),
            ("diag", "DNS & Latency Tools", "search"),
            ("all", "Show All", "package"),
        ]
        self.subtab_buttons = {}
        for key, label, icon in self.subtab_configs:
            btn = SharpButton(label, icon_name=icon, variant="outline" if key != "virsh" else "primary")
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

        # 1. Virsh / Libvirt Virtual Network Controller Card
        self.virsh_card = SharpCard("Libvirt / QEMU Virtual Networks", "Manage virsh default NAT network bridge")
        v_btn_row = QHBoxLayout()
        v_btn_row.setSpacing(10)

        self.start_net_btn = DependencyButton("virsh", "Start Default Network", self._start_default_net, icon_name="play", variant="primary")
        v_btn_row.addWidget(self.start_net_btn)

        self.define_net_btn = SharpButton("Define & Autostart Default Network (XML)", icon_name="wrench", variant="secondary")
        self.define_net_btn.clicked.connect(self._define_default_net)
        v_btn_row.addWidget(self.define_net_btn)

        v_btn_row.addStretch()
        self.virsh_card.add_layout(v_btn_row)
        self.c_layout.addWidget(self.virsh_card)

        # 2. Open / Listening Ports Card
        self.ports_card = SharpCard("Active Listening Ports & Sockets", "Live TCP/UDP open sockets discovered via ss -tulnp")
        self.ports_table = QTableWidget(0, 4)
        self.ports_table.setHorizontalHeaderLabels(["PROTOCOL", "LOCAL ADDRESS & PORT", "PID / PROCESS", "ACTION"])
        self.ports_table.verticalHeader().setVisible(False)
        self.ports_table.verticalHeader().setDefaultSectionSize(44)
        self.ports_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.ports_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.ports_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.ports_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self.ports_table.setColumnWidth(3, 140)
        self.ports_table.setMinimumHeight(240)
        self.ports_table.setAlternatingRowColors(True)
        self.ports_card.add_widget(self.ports_table)
        self.c_layout.addWidget(self.ports_card)

        # 3. DNS Benchmark & Speedtest Diagnostic Card
        self.diag_card = SharpCard("Network Diagnostics & DNS Benchmarking", "Ping gateways, test DNS query latencies, and check external IPs")
        d_layout = QVBoxLayout()
        d_layout.setSpacing(10)

        ip_row = QHBoxLayout()
        ip_row.setSpacing(10)

        self.ext_ip_btn = SharpButton("Check Public IP (curl ifconfig.me)", icon_name="globe", variant="primary")
        self.ext_ip_btn.clicked.connect(self._check_public_ip)
        ip_row.addWidget(self.ext_ip_btn)

        self.ping_btn = SharpButton("Ping Gateway & Cloudflare (1.1.1.1)", icon_name="sliders", variant="secondary")
        self.ping_btn.clicked.connect(self._ping_check)
        ip_row.addWidget(self.ping_btn)

        self.dns_btn = SharpButton("Test DNS Resolvers", icon_name="terminal", variant="outline")
        self.dns_btn.clicked.connect(self._test_dns)
        ip_row.addWidget(self.dns_btn)

        ip_row.addStretch()
        d_layout.addLayout(ip_row)

        self.diag_card.add_layout(d_layout)
        self.c_layout.addWidget(self.diag_card)

        self.c_layout.addStretch()
        self.scroll.setWidget(container)
        layout.addWidget(self.scroll)

        self._switch_sub_tab("virsh")
        QTimer.singleShot(0, self._refresh_all)

    def _switch_sub_tab(self, active_key: str):
        self.active_sub_tab = active_key
        t_key = self.services.settings.get("theme", "light")
        for key, btn in self.subtab_buttons.items():
            btn.variant = "primary" if key == active_key else "outline"
            btn.apply_style(t_key)

        show_all = (active_key == "all")
        self.virsh_card.setVisible(show_all or active_key == "virsh")
        self.ports_card.setVisible(show_all or active_key == "ports")
        self.diag_card.setVisible(show_all or active_key == "diag")

    def _refresh_all(self):
        self.start_net_btn.refresh_state()
        self._render_ports()

    def _render_ports(self):
        ports = self.services.vm.get_listening_ports()
        self.ports_table.setRowCount(len(ports))

        for row, p in enumerate(ports):
            proto_item = QTableWidgetItem(p.protocol)
            addr_item = QTableWidgetItem(f"{p.address}:{p.port}")
            proc_item = QTableWidgetItem(f"{p.process} (pid={p.pid})")

            self.ports_table.setItem(row, 0, proto_item)
            self.ports_table.setItem(row, 1, addr_item)
            self.ports_table.setItem(row, 2, proc_item)

            act_container = QWidget()
            act_layout = QHBoxLayout(act_container)
            act_layout.setContentsMargins(4, 4, 4, 4)
            act_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            if p.process != "-":
                btn = SharpButton("Kill Sockets", icon_name="trash", variant="danger")
                btn.setFixedHeight(28)
                btn.clicked.connect(lambda _, proc=p.process: self._kill_port_process(proc))
                act_layout.addWidget(btn)

            self.ports_table.setCellWidget(row, 3, act_container)

    def _start_default_net(self):
        cmd = self.services.vm.get_virsh_start_default_command()
        self.services.runner.run_command(cmd)

    def _define_default_net(self):
        cmd = self.services.vm.get_virsh_define_default_command()
        self.services.runner.run_command(cmd)

    def _kill_port_process(self, process_name: str):
        self.services.runner.run_command(f"sudo killall -9 '{process_name}'", on_finish=lambda _: self._render_ports())

    def _check_public_ip(self):
        self.services.runner.run_command("echo -n 'Public IP: ' && curl -s ifconfig.me && echo ''")

    def _ping_check(self):
        self.services.runner.run_command("ping -c 4 1.1.1.1")

    def _test_dns(self):
        self.services.runner.run_command("dig @1.1.1.1 google.com +short && dig @8.8.8.8 google.com +short")
