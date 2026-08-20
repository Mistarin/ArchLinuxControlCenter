"""
Updates & Package Management View:
- Sub-Module Header Navigation (Search, Pending Updates, Granular/Repos, Doctor, Local Installer, Show All)
- Polished table row rendering with proper heights (no clipping)
- Instant in-memory package search with live debouncing
- Full system upgrade & granular separate updates
- Drag & Drop local package installer (.pkg.tar.zst / .pkg.tar.xz)
- Comprehensive Package Conflict & Health Doctor
"""

import shutil
import shlex
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QFrame
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer

from cachy_control.core.service_registry import ServiceRegistry
from cachy_control.core.contracts.package_contract import PackageItem, PendingUpdate
from cachy_control.ui.components.sharp_card import SharpCard
from cachy_control.ui.components.confirm_dialog import confirm_destructive_action
from cachy_control.ui.components.sharp_button import SharpButton
from cachy_control.ui.components.dependency_button import DependencyButton
from cachy_control.ui.components.section_badge import SectionBadge
from cachy_control.ui.components.drop_zone import DropZone
from cachy_control.ui.theme import THEMES, DESTRUCTIVE_RED

class SearchWorker(QThread):
    results_ready = pyqtSignal(list)

    def __init__(self, query: str, package_service):
        super().__init__()
        self.query = query
        self.package_service = package_service

    def run(self):
        res = self.package_service.search_all(self.query)
        self.results_ready.emit(res)

class CheckUpdatesWorker(QThread):
    updates_ready = pyqtSignal(list)

    def __init__(self, package_service):
        super().__init__()
        self.package_service = package_service

    def run(self):
        res = self.package_service.get_pending_updates()
        self.updates_ready.emit(res)

class UpdatesView(QWidget):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.services = ServiceRegistry.get()
        self.search_worker = None
        self.check_worker = None
        self.active_sub_tab = "search"

        # Search debounce timer (150ms for instant search)
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self._do_search)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # Header Row
        header = QHBoxLayout()
        header.addWidget(SectionBadge("updates", "PACKAGE UPDATES & REPOSITORIES"))
        header.addStretch()

        self.refresh_check_btn = SharpButton("Check for Updates", icon_name="refresh", variant="outline")
        self.refresh_check_btn.clicked.connect(self._start_check_updates)
        header.addWidget(self.refresh_check_btn)
        layout.addLayout(header)

        # Sub-Module Filter Tabs at the Top
        subtab_row = QHBoxLayout()
        subtab_row.setSpacing(8)

        self.subtab_configs = [
            ("search", "Universal Search", "search"),
            ("updates", "Pending Updates", "refresh"),
            ("repos", "Granular & Repos", "package"),
            ("doctor", "Package Doctor", "shield"),
            ("installer", "Local Installer", "download"),
            ("all", "Show All", "sliders"),
        ]
        self.subtab_buttons = {}
        for key, label, icon in self.subtab_configs:
            btn = SharpButton(label, icon_name=icon, variant="outline" if key != "search" else "primary")
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

        # 1. Universal Multi-Source Search Card
        self.search_card = SharpCard("Universal Package Search", "Instant in-memory search across Official Repos, AUR, and Flatpak")
        s_layout = QVBoxLayout()
        s_layout.setSpacing(12)

        s_input_row = QHBoxLayout()
        s_input_row.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search packages instantly as you type (e.g. discord, easyeffects, vlc, steam)...")
        self.search_input.textChanged.connect(lambda: self.search_timer.start(150))
        self.search_input.returnPressed.connect(self._do_search)
        s_input_row.addWidget(self.search_input, 1)

        self.search_btn = SharpButton("Search", icon_name="search", variant="primary")
        self.search_btn.clicked.connect(self._do_search)
        s_input_row.addWidget(self.search_btn)
        s_layout.addLayout(s_input_row)

        # Results Table with proper row heights and column distribution
        self.results_table = QTableWidget(0, 6)
        self.results_table.setHorizontalHeaderLabels(["SOURCE", "PACKAGE NAME", "VERSION", "DESCRIPTION", "STATUS", "ACTION"])
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.verticalHeader().setDefaultSectionSize(44)
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.results_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.results_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        self.results_table.setColumnWidth(4, 110)
        self.results_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.results_table.setColumnWidth(5, 110)
        self.results_table.setMinimumHeight(380)
        self.results_table.setAlternatingRowColors(True)
        s_layout.addWidget(self.results_table)

        self.search_card.add_layout(s_layout)
        self.c_layout.addWidget(self.search_card)

        # 2. Pending Updates Inspector Card
        self.pending_card = SharpCard("Pending System & Application Updates", "Detects available updates, download sizes, and build release dates")
        p_layout = QVBoxLayout()
        p_layout.setSpacing(12)

        s_row = QHBoxLayout()
        s_row.setSpacing(16)

        self.status_summary_lbl = QLabel("Checking for available updates...")
        self.status_summary_lbl.setStyleSheet("font-size: 13px; font-weight: 700;")
        s_row.addWidget(self.status_summary_lbl)
        s_row.addStretch()

        self.full_update_top_btn = SharpButton("Upgrade All Packages", icon_name="refresh", variant="primary")
        self.full_update_top_btn.clicked.connect(lambda: self._run_update("all"))
        s_row.addWidget(self.full_update_top_btn)
        p_layout.addLayout(s_row)

        self.updates_table = QTableWidget(0, 7)
        self.updates_table.setHorizontalHeaderLabels([
            "SOURCE", "PACKAGE NAME", "CURRENT", "NEW VERSION", "DOWNLOAD SIZE", "UPDATE / BUILD DATE", "ACTION"
        ])
        self.updates_table.verticalHeader().setVisible(False)
        self.updates_table.verticalHeader().setDefaultSectionSize(44)
        self.updates_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.updates_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.updates_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.updates_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.updates_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.updates_table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        self.updates_table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeMode.Fixed)
        self.updates_table.setColumnWidth(6, 120)
        self.updates_table.setMinimumHeight(280)
        self.updates_table.setAlternatingRowColors(True)
        p_layout.addWidget(self.updates_table)

        self.pending_card.add_layout(p_layout)
        self.c_layout.addWidget(self.pending_card)

        # 3. Granular Updates & Mirrors Action Bar
        self.update_card = SharpCard("Granular Update Operations", "Upgrade individual package systems or rate download mirrors")
        u_row = QHBoxLayout()
        u_row.setSpacing(10)

        self.pacman_up_btn = SharpButton("Pacman (System)", icon_name="package", variant="secondary")
        self.pacman_up_btn.clicked.connect(lambda: self._run_update("pacman"))
        u_row.addWidget(self.pacman_up_btn)

        self.yay_up_btn = DependencyButton("yay", "Yay (AUR)", lambda: self._run_update("yay"), icon_name="package", variant="outline")
        u_row.addWidget(self.yay_up_btn)

        self.paru_up_btn = DependencyButton("paru", "Paru (AUR)", lambda: self._run_update("paru"), icon_name="package", variant="outline")
        u_row.addWidget(self.paru_up_btn)

        self.flatpak_up_btn = DependencyButton("flatpak", "Flatpak", lambda: self._run_update("flatpak"), icon_name="package", variant="outline")
        u_row.addWidget(self.flatpak_up_btn)

        self.mirrors_btn = DependencyButton("cachyos-rate-mirrors", "Rate CachyOS Mirrors", lambda: self._run_update("rate_mirrors"), icon_name="sliders", variant="secondary")
        u_row.addWidget(self.mirrors_btn)

        u_row.addStretch()
        self.update_card.add_layout(u_row)
        self.c_layout.addWidget(self.update_card)

        # 4. Package Doctor Card
        self.fix_card = SharpCard("Package Conflict & Health Doctor", "Diagnose & resolve pacman collisions, broken dependencies, locked DBs & PGP keyring errors")
        f_layout = QVBoxLayout()
        f_layout.setSpacing(10)

        diag_row = QHBoxLayout()
        diag_row.setSpacing(8)

        self.check_deps_btn = SharpButton("Check Dependencies", icon_name="check", variant="outline")
        self.check_deps_btn.clicked.connect(lambda: self.services.runner.run_command("sudo pacman -D --check"))
        diag_row.addWidget(self.check_deps_btn)

        self.fix_keys_btn = SharpButton("Repair PGP Keys", icon_name="shield", variant="outline")
        self.fix_keys_btn.clicked.connect(lambda: self.services.runner.run_command("sudo pacman-key --init && sudo pacman-key --populate archlinux cachyos && sudo pacman -S --needed --noconfirm archlinux-keyring cachyos-keyring"))
        diag_row.addWidget(self.fix_keys_btn)

        self.unlock_db_btn = SharpButton("Unlock DB (db.lck)", icon_name="cross", variant="outline")
        self.unlock_db_btn.clicked.connect(lambda: self.services.runner.run_command("sudo rm -f /var/lib/pacman/db.lck && echo 'Pacman database lock removed!'"))
        diag_row.addWidget(self.unlock_db_btn)
        diag_row.addStretch()
        f_layout.addLayout(diag_row)

        ov_row = QHBoxLayout()
        ov_row.setSpacing(8)
        self.conflict_pkg_input = QLineEdit()
        self.conflict_pkg_input.setPlaceholderText("Package with file collisions (e.g. package-name)...")
        ov_row.addWidget(self.conflict_pkg_input, 1)

        self.overwrite_btn = SharpButton("Resolve (--overwrite)", icon_name="wrench", variant="secondary")
        self.overwrite_btn.clicked.connect(self._resolve_file_conflict)
        ov_row.addWidget(self.overwrite_btn)
        f_layout.addLayout(ov_row)

        rm_row = QHBoxLayout()
        rm_row.setSpacing(8)
        self.rdd_pkg_input = QLineEdit()
        self.rdd_pkg_input.setPlaceholderText("Conflicting package to force-remove without breaking deps (-Rdd)...")
        rm_row.addWidget(self.rdd_pkg_input, 1)

        self.rdd_btn = SharpButton("Force Remove (-Rdd)", icon_name="trash", variant="danger")
        self.rdd_btn.clicked.connect(self._force_remove_conflict)
        rm_row.addWidget(self.rdd_btn)
        f_layout.addLayout(rm_row)

        self.fix_card.add_layout(f_layout)
        self.c_layout.addWidget(self.fix_card)

        # 5. Local Package Installer Card
        self.pkg_drop_card = SharpCard("Local Package Installer", "Install offline .pkg.tar.zst / .pkg.tar.xz files (pacman -U)")
        self.drop_zone = DropZone()
        self.drop_zone.file_selected.connect(self._install_local_file)
        self.pkg_drop_card.add_widget(self.drop_zone)
        self.c_layout.addWidget(self.pkg_drop_card)

        self.c_layout.addStretch()
        self.scroll.setWidget(container)
        layout.addWidget(self.scroll)

        # Apply initial tab filtering
        self._switch_sub_tab("search")

        # Initial Search (fast in-memory)
        QTimer.singleShot(0, self._do_search)

    def _switch_sub_tab(self, active_key: str):
        self.active_sub_tab = active_key
        t_key = self.services.settings.get("theme", "light")

        for key, btn in self.subtab_buttons.items():
            btn.variant = "primary" if key == active_key else "outline"
            btn.apply_style(t_key)

        # Full-size table adjustment based on active tab
        if active_key == "search":
            self.results_table.setMinimumHeight(620)
        elif active_key == "updates":
            self.updates_table.setMinimumHeight(620)
        else:
            self.results_table.setMinimumHeight(340)
            self.updates_table.setMinimumHeight(280)

        # Show / Hide sections based on tab
        show_all = (active_key == "all")
        self.search_card.setVisible(show_all or active_key == "search")
        self.pending_card.setVisible(show_all or active_key == "updates")
        self.update_card.setVisible(show_all or active_key == "repos")
        self.fix_card.setVisible(show_all or active_key == "doctor")
        self.pkg_drop_card.setVisible(show_all or active_key == "installer")

    def _start_check_updates(self):
        self.status_summary_lbl.setText("Scanning for pending updates...")
        self.refresh_check_btn.setEnabled(False)
        self.refresh_check_btn.setText("Scanning...")

        if self.check_worker and self.check_worker.isRunning():
            self.check_worker.terminate()
            self.check_worker.wait()

        self.check_worker = CheckUpdatesWorker(self.services.packages)
        self.check_worker.updates_ready.connect(self._display_pending_updates)
        self.check_worker.start()

    def _display_pending_updates(self, updates: list):
        self.refresh_check_btn.setEnabled(True)
        self.refresh_check_btn.setText("Check for Updates")
        self.updates_table.setRowCount(len(updates))

        if not updates:
            self.updates_table.setRowCount(1)
            empty_item = QTableWidgetItem("✓ Your system is fully up to date — 0 pending updates.")
            empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.updates_table.setItem(0, 1, empty_item)
            self.status_summary_lbl.setText("✓ Your system and applications are fully up to date!")
            self.full_update_top_btn.setEnabled(False)
            return

        self.full_update_top_btn.setEnabled(True)
        self.status_summary_lbl.setText(f"Found {len(updates)} pending update(s)")

        for row, u in enumerate(updates):
            src_name = getattr(u, 'repo_or_source', getattr(u, 'source', 'repo'))
            src_item = QTableWidgetItem(f"[{src_name.upper()}]")
            src_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            name_item = QTableWidgetItem(u.name)
            old_ver = getattr(u, 'old_version', getattr(u, 'current_version', '-'))
            curr_item = QTableWidgetItem(old_ver)
            new_item = QTableWidgetItem(u.new_version)
            size_item = QTableWidgetItem(u.download_size)
            date_item = QTableWidgetItem(u.build_date)

            self.updates_table.setItem(row, 0, src_item)
            self.updates_table.setItem(row, 1, name_item)
            self.updates_table.setItem(row, 2, curr_item)
            self.updates_table.setItem(row, 3, new_item)
            self.updates_table.setItem(row, 4, size_item)
            self.updates_table.setItem(row, 5, date_item)

            act_container = QWidget()
            act_layout = QHBoxLayout(act_container)
            act_layout.setContentsMargins(4, 4, 4, 4)
            act_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            up_btn = SharpButton("Update", icon_name="refresh", variant="primary")
            up_btn.setFixedHeight(28)
            up_btn.setFixedWidth(84)
            up_btn.clicked.connect(lambda _, pkg_name=u.name, src=src_name: self._update_single(pkg_name, src))
            act_layout.addWidget(up_btn)

            self.updates_table.setCellWidget(row, 6, act_container)

    def _update_single(self, pkg_name: str, source: str):
        if source == "aur":
            cmd = f"yay -S --noconfirm {pkg_name}"
        elif source == "flatpak":
            cmd = f"flatpak update -y {pkg_name}"
        else:
            cmd = f"sudo pacman -S --noconfirm {pkg_name}"
        self.services.runner.run_command(cmd, on_finish=lambda _: self._start_check_updates())

    def _run_update(self, manager: str):
        cmd = self.services.packages.get_update_command(manager)
        self.services.runner.run_command(cmd, on_finish=lambda _: self._start_check_updates())

    def _do_search(self):
        query = self.search_input.text().strip()

        if self.search_worker and self.search_worker.isRunning():
            self.search_worker.terminate()
            self.search_worker.wait()

        self.search_worker = SearchWorker(query, self.services.packages)
        self.search_worker.results_ready.connect(self._display_search_results)
        self.search_worker.start()

    def _display_search_results(self, items: list):
        t_key = self.services.settings.get("theme", "light")
        t = THEMES.get(t_key, THEMES["light"])

        self.results_table.setRowCount(0)
        self.results_table.clearContents()

        if not items:
            self.results_table.setRowCount(1)
            empty_item = QTableWidgetItem("No matching packages found.")
            empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.results_table.setItem(0, 3, empty_item)
            for c_idx in (0, 1, 2, 4, 5):
                self.results_table.setItem(0, c_idx, QTableWidgetItem("-"))
            return

        self.results_table.setRowCount(len(items))
        for row, item in enumerate(items):
            src_item = QTableWidgetItem(f"[{item.repo_or_source.upper()}]")
            src_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

            name_item = QTableWidgetItem(item.name)
            ver_item = QTableWidgetItem(item.version)
            desc_item = QTableWidgetItem(item.description)

            self.results_table.setItem(row, 0, src_item)
            self.results_table.setItem(row, 1, name_item)
            self.results_table.setItem(row, 2, ver_item)
            self.results_table.setItem(row, 3, desc_item)

            # Column 4: Status
            status_container = QWidget()
            status_layout = QHBoxLayout(status_container)
            status_layout.setContentsMargins(4, 4, 4, 4)
            status_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            if item.installed:
                inst_lbl = QLabel("✓ Installed")
                inst_lbl.setStyleSheet(f"color: {t['success']}; font-weight: 700; font-size: 11px;")
                status_layout.addWidget(inst_lbl)
            else:
                avail_lbl = QLabel("Available")
                avail_lbl.setStyleSheet(f"color: {t['muted']}; font-weight: 600; font-size: 11px;")
                status_layout.addWidget(avail_lbl)

            self.results_table.setCellWidget(row, 4, status_container)

            # Column 5: Action
            act_container = QWidget()
            act_layout = QHBoxLayout(act_container)
            act_layout.setContentsMargins(4, 4, 4, 4)
            act_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            if item.installed:
                rm_btn = SharpButton("Remove", icon_name="trash", variant="danger", theme_key=t_key)
                rm_btn.setFixedHeight(28)
                rm_btn.setFixedWidth(84)
                rm_btn.clicked.connect(lambda _, pkg=item: self._uninstall_pkg(pkg))
                act_layout.addWidget(rm_btn)
            else:
                install_btn = SharpButton("Install", icon_name="download", variant="primary", theme_key=t_key)
                install_btn.setFixedHeight(28)
                install_btn.setFixedWidth(84)
                install_btn.clicked.connect(lambda _, pkg=item: self._install_pkg(pkg))
                act_layout.addWidget(install_btn)

            self.results_table.setCellWidget(row, 5, act_container)

    def _uninstall_pkg(self, pkg: PackageItem):
        cmd = self.services.packages.get_remove_command(pkg)
        if not confirm_destructive_action(
            self,
            f"Uninstall {pkg.name}",
            f"Are you sure you want to completely remove {pkg.name} ({pkg.repo_or_source}) and unneeded dependencies?\n\nCommand: {cmd}",
            "Yes, Remove Package"
        ):
            return
        self.services.runner.run_command(cmd, on_finish=lambda _: self._do_search())

    def _install_pkg(self, pkg: PackageItem):
        cmd = self.services.packages.get_install_command(pkg)
        self.services.runner.run_command(cmd, on_finish=lambda _: self._do_search())

    def _install_local_file(self, file_path: str):
        cmd = self.services.packages.get_local_install_command(file_path)
        self.services.runner.run_command(cmd)

    def _resolve_file_conflict(self):
        pkg = self.conflict_pkg_input.text().strip()
        if not pkg:
            return
        cmd = f"sudo pacman -S --overwrite '*' --noconfirm {pkg}"
        self.services.runner.run_command(cmd)

    def _force_remove_conflict(self):
        pkg = self.rdd_pkg_input.text().strip()
        if not pkg:
            return
        if not confirm_destructive_action(
            self,
            f"Force Remove {pkg} (-Rdd)",
            f"CAUTION: Force-removing {pkg} bypasses pacman dependency checks (-Rdd) and may break packages that depend on it.\n\nCommand: sudo pacman -Rdd --noconfirm {pkg}",
            "Force Remove (-Rdd)"
        ):
            return
        cmd = f"sudo pacman -Rdd --noconfirm {pkg}"
        self.services.runner.run_command(cmd)
