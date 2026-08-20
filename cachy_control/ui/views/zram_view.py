"""
Memory, Swappiness & ZRAM Tuner View.
Equipped with top sub-module tabs for focused controls.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QComboBox, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt

from cachy_control.core.service_registry import ServiceRegistry
from cachy_control.ui.components.sharp_card import SharpCard
from cachy_control.ui.components.sharp_button import SharpButton
from cachy_control.ui.components.section_badge import SectionBadge
from cachy_control.ui.components.confirm_dialog import confirm_destructive_action
from cachy_control.ui.theme import THEMES

class ZramView(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.services = ServiceRegistry.get()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Row
        header = QHBoxLayout()
        header.addWidget(SectionBadge("zram", "MEMORY & ZRAM OPTIMIZER"))
        header.addStretch()
        self.refresh_btn = SharpButton("Refresh Status", icon_name="refresh", variant="outline")
        self.refresh_btn.clicked.connect(self._check_zram_status)
        header.addWidget(self.refresh_btn)
        layout.addLayout(header)

        # Sub-Module Filter Tabs at the Top
        subtab_row = QHBoxLayout()
        subtab_row.setSpacing(8)

        self.subtab_configs = [
            ("status", "ZRAM Swap Status", "cpu"),
            ("generator", "Systemd Generator", "sliders"),
            ("swappiness", "Kernel Swappiness", "sliders"),
            ("all", "Show All", "package"),
        ]
        self.subtab_buttons = {}
        for key, label, icon in self.subtab_configs:
            btn = SharpButton(label, icon_name=icon, variant="outline" if key != "status" else "primary")
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

        # 1. Live ZRAM & Swap Inspection Card
        self.status_card = SharpCard("ZRAM & Swap Device Status", "Inspect active compressed RAM swap devices")
        s_btn_row = QHBoxLayout()
        s_btn_row.setSpacing(10)

        self.inspect_zram_btn = SharpButton("Run zramctl & swapon --show", icon_name="terminal", variant="primary")
        self.inspect_zram_btn.clicked.connect(self._check_zram_status)
        s_btn_row.addWidget(self.inspect_zram_btn)

        self.free_btn = SharpButton("Run free -h", icon_name="cpu", variant="secondary")
        self.free_btn.clicked.connect(lambda: self.services.runner.run_command("free -h"))
        s_btn_row.addWidget(self.free_btn)

        s_btn_row.addStretch()
        self.status_card.add_layout(s_btn_row)
        self.c_layout.addWidget(self.status_card)

        # 2. Systemd ZRAM Generator Config Card
        self.gen_card = SharpCard("Systemd ZRAM Generator Configurator", "Generates /etc/systemd/zram-generator.conf and applies immediately")
        g_layout = QVBoxLayout()
        g_layout.setSpacing(12)

        g_row = QHBoxLayout()
        g_row.setSpacing(16)

        g_row.addWidget(QLabel("ZRAM Size (MB):"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(512, 131072)
        self.size_spin.setSingleStep(1024)
        self.size_spin.setValue(self.services.settings.get("zram_size_mb", 12288))
        g_row.addWidget(self.size_spin)

        g_row.addWidget(QLabel("Algorithm:"))
        self.algo_combo = QComboBox()
        self.algo_combo.addItems(["zstd", "lz4", "lzo", "lz4hc"])
        self.algo_combo.setCurrentText(self.services.settings.get("zram_algorithm", "zstd"))
        g_row.addWidget(self.algo_combo)

        g_row.addWidget(QLabel("Priority:"))
        self.prio_spin = QSpinBox()
        self.prio_spin.setRange(0, 32767)
        self.prio_spin.setValue(self.services.settings.get("zram_priority", 100))
        g_row.addWidget(self.prio_spin)

        g_row.addStretch()
        g_layout.addLayout(g_row)

        g_btn_row = QHBoxLayout()
        self.apply_gen_btn = SharpButton("Apply & Restart ZRAM Service", icon_name="check", variant="primary")
        self.apply_gen_btn.clicked.connect(self._apply_zram_generator)
        g_btn_row.addWidget(self.apply_gen_btn)
        g_btn_row.addStretch()
        g_layout.addLayout(g_btn_row)

        self.gen_card.add_layout(g_layout)
        self.c_layout.addWidget(self.gen_card)

        # 3. Kernel Swappiness & Tuning Card
        self.swap_card = SharpCard("Kernel Swappiness & Page Cluster Tuner", "Tune how aggressively Linux kernel swaps into ZRAM")
        sw_layout = QVBoxLayout()
        sw_layout.setSpacing(12)

        sw_row = QHBoxLayout()
        sw_row.setSpacing(16)

        sw_row.addWidget(QLabel("vm.swappiness:"))
        self.swappiness_spin = QSpinBox()
        self.swappiness_spin.setRange(0, 200)
        self.swappiness_spin.setValue(self.services.settings.get("vm_swappiness", 150))
        sw_row.addWidget(self.swappiness_spin)

        sw_row.addWidget(QLabel("vm.page-cluster:"))
        self.cluster_spin = QSpinBox()
        self.cluster_spin.setRange(0, 5)
        self.cluster_spin.setValue(self.services.settings.get("vm_page_cluster", 0))
        sw_row.addWidget(self.cluster_spin)

        sw_row.addStretch()
        sw_layout.addLayout(sw_row)

        sw_btn_row = QHBoxLayout()
        sw_btn_row.setSpacing(10)

        self.apply_swap_btn = SharpButton("Apply Now & Save to /etc/sysctl.d/99-zram.conf", icon_name="check", variant="primary")
        self.apply_swap_btn.clicked.connect(self._apply_swappiness)
        sw_btn_row.addWidget(self.apply_swap_btn)

        self.reset_zram_btn = SharpButton("Reset /dev/zram0", icon_name="trash", variant="outline")
        self.reset_zram_btn.clicked.connect(self._reset_zram)
        sw_btn_row.addWidget(self.reset_zram_btn)

        sw_btn_row.addStretch()
        sw_layout.addLayout(sw_btn_row)

        self.swap_card.add_layout(sw_layout)
        self.c_layout.addWidget(self.swap_card)

        self.c_layout.addStretch()
        self.scroll.setWidget(container)
        layout.addWidget(self.scroll)

        self._switch_sub_tab("status")

    def _switch_sub_tab(self, active_key: str):
        self.active_sub_tab = active_key
        t_key = self.services.settings.get("theme", "light")
        for key, btn in self.subtab_buttons.items():
            btn.variant = "primary" if key == active_key else "outline"
            btn.apply_style(t_key)

        show_all = (active_key == "all")
        self.status_card.setVisible(show_all or active_key == "status")
        self.gen_card.setVisible(show_all or active_key == "generator")
        self.swap_card.setVisible(show_all or active_key == "swappiness")

    def _check_zram_status(self):
        cmd = self.services.zram.get_status_command()
        self.services.runner.run_command(cmd)

    def _apply_zram_generator(self):
        size_mb = self.size_spin.value()
        algo = self.algo_combo.currentText()
        prio = self.prio_spin.value()

        self.services.settings.set("zram_size_mb", size_mb)
        self.services.settings.set("zram_algorithm", algo)
        self.services.settings.set("zram_priority", prio)

        cmd = self.services.zram.get_generator_config_command(size_mb, algo, prio)
        self.services.runner.run_command(cmd)

    def _apply_swappiness(self):
        swappiness = self.swappiness_spin.value()
        cluster = self.cluster_spin.value()

        self.services.settings.set("vm_swappiness", swappiness)
        self.services.settings.set("vm_page_cluster", cluster)

        cmd = self.services.zram.get_swappiness_command(swappiness, cluster)
        self.services.runner.run_command(cmd)

    def _reset_zram(self):
        if confirm_destructive_action(
            self,
            "Reset ZRAM Device (/dev/zram0)",
            "This will execute 'swapoff /dev/zram0' and reset the block device. Proceed?",
            "Yes, Reset ZRAM"
        ):
            cmd = self.services.zram.get_reset_command()
            self.services.runner.run_command(cmd)
