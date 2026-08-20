"""
SudoAuthDialog: Minimalist modal password prompt for upfront administrator privileges.
Includes warning confirmation modal if the user declines or cancels privileges on launch.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QWidget
)
from PyQt6.QtCore import Qt
from cachy_control.core.services.sudo_service import SudoService
from cachy_control.ui.components.sharp_button import SharpButton
from cachy_control.ui.icons import get_pixmap
from cachy_control.ui.theme import THEMES, DESTRUCTIVE_RED
from cachy_control.core.service_registry import ServiceRegistry

class SudoDeclineWarningDialog(QDialog):
    """Warning modal shown when user declines administrator permissions."""
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("Warning: Limited Mode")
        self.setModal(True)
        self.setFixedSize(500, 270)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        services = ServiceRegistry.get()
        t_key = services.settings.get("theme", "light")
        t = THEMES.get(t_key, THEMES["light"])
        self.setStyleSheet(f"""
            SudoDeclineWarningDialog {{
                background-color: {t['surface_2']};
                border: 2px solid {t['warning']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        # Header with Alert Icon
        h_row = QHBoxLayout()
        h_row.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_pixmap("alert", size=26, color=t["warning"]))
        h_row.addWidget(icon_lbl)

        title_lbl = QLabel("Are you sure you want to decline Admin Privileges?")
        title_lbl.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {t['warning']};")
        h_row.addWidget(title_lbl)
        h_row.addStretch()
        layout.addLayout(h_row)

        # Detailed consequences text
        warn_text = (
            "<b>Warning:</b> CachyOS Control Center was not intended to work without administrator privileges.<br><br>"
            "Running without root access will cause the following limitations:<br>"
            "• <b>Package Management:</b> System upgrades, AUR helpers (yay/paru), and installs will fail.<br>"
            "• <b>Kernel & Memory:</b> ZRAM configuration and swappiness tuners will be disabled.<br>"
            "• <b>Services & Hardware:</b> Display managers (SDDM), audio routing, and auditd cannot be configured."
        )
        desc_lbl = QLabel(warn_text)
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet(f"font-size: 11px; line-height: 1.4; color: {t['text']};")
        layout.addWidget(desc_lbl)

        layout.addStretch()

        # Action buttons
        b_row = QHBoxLayout()
        b_row.setSpacing(10)
        b_row.addStretch()

        self.limited_btn = SharpButton("Proceed in Limited Mode", icon_name="cross", variant="outline")
        self.limited_btn.clicked.connect(self.accept) # Accept proceeding in limited mode
        b_row.addWidget(self.limited_btn)

        self.back_btn = SharpButton("Go Back & Authenticate", icon_name="shield", variant="primary")
        self.back_btn.clicked.connect(self.reject) # Go back to password prompt
        b_row.addWidget(self.back_btn)

        layout.addLayout(b_row)

class SudoAuthDialog(QDialog):
    def __init__(self, command_preview: str = "", is_startup: bool = False, parent: QWidget = None):
        super().__init__(parent)
        self.is_startup = is_startup
        self.setWindowTitle("Administrator Authentication")
        self.setModal(True)
        self.setFixedSize(450, 250)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        services = ServiceRegistry.get()
        t_key = services.settings.get("theme", "light")
        t = THEMES.get(t_key, THEMES["light"])
        self.setStyleSheet(f"""
            SudoAuthDialog {{
                background-color: {t['surface_2']};
                border: 2px solid {t['border']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(12)

        # Header with Shield Icon
        h_row = QHBoxLayout()
        h_row.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_pixmap("shield", size=24, color=t["accent"]))
        h_row.addWidget(icon_lbl)

        title_lbl = QLabel("Administrator Privileges Required")
        title_lbl.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {t['text']};")
        h_row.addWidget(title_lbl)
        h_row.addStretch()
        layout.addLayout(h_row)

        # Command Preview / Description
        if command_preview and not command_preview.startswith("Grant"):
            cmd_short = command_preview[:60] + ("..." if len(command_preview) > 60 else "")
            info_lbl = QLabel(f"The following action requires root permissions:\n<span style='font-family: monospace;'>{cmd_short}</span>")
        else:
            info_lbl = QLabel("Authenticate once to allow seamless system updates, package installations, and kernel optimizations without repeated password prompts.")
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet(f"font-size: 11px; opacity: 0.85; color: {t['muted']};")
        layout.addWidget(info_lbl)

        # Password Input Field
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Enter sudo password...")
        self.password_input.returnPressed.connect(self._do_auth)
        layout.addWidget(self.password_input)

        # Error / Feedback Label
        self.error_lbl = QLabel()
        self.error_lbl.setStyleSheet(f"font-size: 11px; font-weight: 600; color: {DESTRUCTIVE_RED};")
        self.error_lbl.hide()
        layout.addWidget(self.error_lbl)

        layout.addStretch()

        # Action Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        self.cancel_btn = SharpButton("Skip / Cancel", icon_name="cross", variant="outline")
        self.cancel_btn.clicked.connect(self._handle_cancel)
        btn_row.addWidget(self.cancel_btn)

        self.auth_btn = SharpButton("Authenticate Session", icon_name="check", variant="primary")
        self.auth_btn.clicked.connect(self._do_auth)
        btn_row.addWidget(self.auth_btn)

        layout.addLayout(btn_row)

    def _handle_cancel(self):
        # Show warning confirmation popup
        warn_dlg = SudoDeclineWarningDialog(self)
        if warn_dlg.exec() == QDialog.DialogCode.Accepted:
            # User confirmed they want to proceed in limited mode
            self.reject()
        else:
            # User wants to go back and authenticate
            self.password_input.setFocus()

    def _do_auth(self):
        pwd = self.password_input.text()
        if not pwd:
            self.error_lbl.setText("Password cannot be empty.")
            self.error_lbl.show()
            return

        self.auth_btn.setEnabled(False)
        self.auth_btn.setText("Validating...")

        ok, msg = SudoService.validate_and_cache_password(pwd)
        if ok:
            self.accept()
        else:
            self.auth_btn.setEnabled(True)
            self.auth_btn.setText("Authenticate Session")
            self.error_lbl.setText("Incorrect password. Please try again.")
            self.error_lbl.show()
            self.password_input.clear()
            self.password_input.setFocus()

def request_upfront_sudo(command: str = "", parent: QWidget = None) -> bool:
    """Helper that verifies sudo upfront and prompts the user if credentials are not cached."""
    if command and not SudoService.is_sudo_needed(command):
        return True
    if SudoService.is_sudo_cached():
        return True
    dialog = SudoAuthDialog(command, is_startup=False, parent=parent)
    return dialog.exec() == QDialog.DialogCode.Accepted
