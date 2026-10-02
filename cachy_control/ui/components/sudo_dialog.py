"""Password prompt shown only when an administrator action needs it."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QWidget
)
from PyQt6.QtCore import Qt
from cachy_control.core.services.sudo_service import SudoService
from cachy_control.ui.components.sharp_button import SharpButton
from cachy_control.ui.icons import get_pixmap
from cachy_control.ui.theme import THEMES, DESTRUCTIVE_RED
from cachy_control.core.service_registry import ServiceRegistry

class SudoAuthDialog(QDialog):
    def __init__(self, command_preview: str = "", parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("Administrator Authentication")
        self.setModal(True)
        self.setFixedSize(450, 280)
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
        if command_preview:
            cmd_short = command_preview[:100] + ("..." if len(command_preview) > 100 else "")
            info_lbl = QLabel(f"This action needs administrator access:\n{cmd_short}")
            info_lbl.setTextFormat(Qt.TextFormat.PlainText)
        else:
            info_lbl = QLabel("Authenticate when an administrator action needs it. Sudo may ask again after its normal timeout.")
        info_lbl.setWordWrap(True)
        info_lbl.setStyleSheet(f"font-size: 11px; color: {t['muted']};")
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

        self.cancel_btn = SharpButton("Cancel", icon_name="cross", variant="outline")
        self.cancel_btn.clicked.connect(self._handle_cancel)
        btn_row.addWidget(self.cancel_btn)

        self.auth_btn = SharpButton("Authenticate", icon_name="check", variant="primary")
        self.auth_btn.clicked.connect(self._do_auth)
        btn_row.addWidget(self.auth_btn)

        layout.addLayout(btn_row)

    def _handle_cancel(self):
        self.password_input.clear()
        self.reject()

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
            self.password_input.clear()
            self.accept()
        else:
            self.auth_btn.setEnabled(True)
            self.auth_btn.setText("Authenticate")
            self.error_lbl.setText(msg or "Authentication failed. Please try again.")
            self.error_lbl.show()
            self.password_input.clear()
            self.password_input.setFocus()

def request_upfront_sudo(command: str = "", parent: QWidget = None) -> bool:
    """Helper that verifies sudo upfront and prompts the user if credentials are not cached."""
    if command and not SudoService.is_sudo_needed(command):
        return True
    if SudoService.is_sudo_cached():
        return True
    dialog = SudoAuthDialog(command, parent=parent)
    return dialog.exec() == QDialog.DialogCode.Accepted
