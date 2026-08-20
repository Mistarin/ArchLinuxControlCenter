"""
Security, Howdy Face Auth, Auditd & File Permission Inspector View.
Equipped with top sub-module tabs for focused controls.
"""

from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QFileDialog, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt

from cachy_control.core.service_registry import ServiceRegistry
from cachy_control.ui.components.sharp_card import SharpCard
from cachy_control.ui.components.sharp_button import SharpButton
from cachy_control.ui.components.dependency_button import DependencyButton
from cachy_control.ui.components.section_badge import SectionBadge
from cachy_control.ui.components.confirm_dialog import confirm_destructive_action
from cachy_control.ui.theme import THEMES

class SecurityView(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.services = ServiceRegistry.get()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Row
        header = QHBoxLayout()
        header.addWidget(SectionBadge("security", "SECURITY, HOWDY & AUDITING"))
        header.addStretch()
        layout.addLayout(header)

        # Sub-Module Filter Tabs at the Top
        subtab_row = QHBoxLayout()
        subtab_row.setSpacing(8)

        self.subtab_configs = [
            ("howdy", "Face Auth & SDDM", "shield"),
            ("audit", "Auditd File Watcher", "terminal"),
            ("perms", "Permission Inspector", "folder"),
            ("all", "Show All", "package"),
        ]
        self.subtab_buttons = {}
        for key, label, icon in self.subtab_configs:
            btn = SharpButton(label, icon_name=icon, variant="outline" if key != "howdy" else "primary")
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

        # 1. Howdy Face Auth & Display Manager Card
        self.howdy_card = SharpCard("Howdy Face Authentication & SDDM", "Test infrared / webcam authentication and manage PAM login rules")
        h_row = QHBoxLayout()
        h_row.setSpacing(10)

        self.howdy_test_btn = DependencyButton("howdy", "Run Howdy Test", lambda: self.services.runner.run_command("sudo howdy test"), icon_name="camera", variant="primary")
        h_row.addWidget(self.howdy_test_btn)

        self.restart_sddm_btn = SharpButton("Restart SDDM Service", icon_name="power", variant="danger")
        self.restart_sddm_btn.clicked.connect(self._restart_sddm)
        h_row.addWidget(self.restart_sddm_btn)
        h_row.addStretch()

        self.howdy_card.add_layout(h_row)
        self.c_layout.addWidget(self.howdy_card)

        # 2. Auditd & Inotify File Watcher Card
        self.audit_card = SharpCard("Auditd & Inotify Real-Time File Watcher", "Monitor unauthorized read/write modifications to sensitive directories")
        a_layout = QVBoxLayout()
        a_layout.setSpacing(10)

        a_row = QHBoxLayout()
        a_row.addWidget(QLabel("Target Path to Watch:"))
        self.watch_path_input = QLineEdit("/etc/pam.d")
        a_row.addWidget(self.watch_path_input, 1)

        browse_btn = SharpButton("Browse...", icon_name="folder", variant="outline")
        browse_btn.clicked.connect(self._browse_watch_path)
        a_row.addWidget(browse_btn)
        a_layout.addLayout(a_row)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self.watch_btn = SharpButton("Add Watch Rule (auditctl -w)", icon_name="eye", variant="primary")
        self.watch_btn.clicked.connect(self._add_audit_rule)
        btn_row.addWidget(self.watch_btn)

        self.log_btn = SharpButton("View Recent Audit Events (ausearch)", icon_name="terminal", variant="outline")
        self.log_btn.clicked.connect(self._view_audit_events)
        btn_row.addWidget(self.log_btn)

        btn_row.addStretch()
        a_layout.addLayout(btn_row)

        self.audit_card.add_layout(a_layout)
        self.c_layout.addWidget(self.audit_card)

        # 3. File Permissions Inspector Card
        self.perm_card = SharpCard("File & Directory Permissions Inspector", "Inspect ownership, octal modes, ACLs and POSIX permissions")
        p_layout = QVBoxLayout()
        p_layout.setSpacing(10)

        p_row = QHBoxLayout()
        p_row.addWidget(QLabel("Inspect Path:"))
        self.inspect_path_input = QLineEdit(str(Path.home()))
        p_row.addWidget(self.inspect_path_input, 1)

        browse_p_btn = SharpButton("Browse...", icon_name="folder", variant="outline")
        browse_p_btn.clicked.connect(self._browse_inspect_path)
        p_row.addWidget(browse_p_btn)
        p_layout.addLayout(p_row)

        p_btn_row = QHBoxLayout()
        self.stat_btn = SharpButton("Inspect Mode & Stat (stat -c)", icon_name="sliders", variant="primary")
        self.stat_btn.clicked.connect(self._inspect_stat)
        p_btn_row.addWidget(self.stat_btn)

        self.acl_btn = SharpButton("Inspect Extended ACLs (getfacl)", icon_name="shield", variant="outline")
        self.acl_btn.clicked.connect(self._inspect_acl)
        p_btn_row.addWidget(self.acl_btn)

        p_btn_row.addStretch()
        p_layout.addLayout(p_btn_row)

        self.perm_card.add_layout(p_layout)
        self.c_layout.addWidget(self.perm_card)

        self.c_layout.addStretch()
        self.scroll.setWidget(container)
        layout.addWidget(self.scroll)

        self._switch_sub_tab("howdy")

    def _switch_sub_tab(self, active_key: str):
        self.active_sub_tab = active_key
        t_key = self.services.settings.get("theme", "light")
        for key, btn in self.subtab_buttons.items():
            btn.variant = "primary" if key == active_key else "outline"
            btn.apply_style(t_key)

        show_all = (active_key == "all")
        self.howdy_card.setVisible(show_all or active_key == "howdy")
        self.audit_card.setVisible(show_all or active_key == "audit")
        self.perm_card.setVisible(show_all or active_key == "perms")

    def _restart_sddm(self):
        if confirm_destructive_action(
            self,
            "Restart SDDM Display Manager",
            "WARNING: Restarting SDDM will immediately terminate your current desktop session and return you to the login screen. Save all work first!",
            "Yes, Restart SDDM"
        ):
            self.services.runner.run_command("sudo systemctl restart sddm.service")

    def _browse_watch_path(self):
        chosen = QFileDialog.getExistingDirectory(self, "Select Directory to Watch", self.watch_path_input.text().strip())
        if chosen:
            self.watch_path_input.setText(chosen)

    def _browse_inspect_path(self):
        chosen = QFileDialog.getExistingDirectory(self, "Select Path to Inspect", self.inspect_path_input.text().strip())
        if chosen:
            self.inspect_path_input.setText(chosen)

    def _add_audit_rule(self):
        target = self.watch_path_input.text().strip()
        if target:
            cmd = self.services.security.get_audit_watch_command(target)
            self.services.runner.run_command(cmd)

    def _view_audit_events(self):
        target = self.watch_path_input.text().strip()
        if target:
            cmd = self.services.security.get_audit_search_command(target)
            self.services.runner.run_command(cmd)

    def _inspect_stat(self):
        target = self.inspect_path_input.text().strip()
        if target:
            cmd = self.services.security.get_file_stat_command(target)
            self.services.runner.run_command(cmd)

    def _inspect_acl(self):
        target = self.inspect_path_input.text().strip()
        if target:
            cmd = self.services.security.get_file_acl_command(target)
            self.services.runner.run_command(cmd)
