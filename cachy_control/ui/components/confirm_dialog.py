"""
ConfirmDialog: Minimalist modal confirmation dialog for destructive actions with shared #FF4D5A warning styling.
"""

from PyQt6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QWidget
from PyQt6.QtCore import Qt
from cachy_control.ui.components.sharp_button import SharpButton
from cachy_control.ui.theme import create_deep_shadow, THEMES, DESTRUCTIVE_RED
from cachy_control.ui.icons import get_pixmap
from cachy_control.core.service_registry import ServiceRegistry

class SharpConfirmDialog(QDialog):
    def __init__(
        self,
        title: str,
        message: str,
        confirm_text: str = "Yes, Proceed",
        parent: QWidget = None
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(440, 210)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        services = ServiceRegistry.get()
        t_key = services.settings.get("theme", "light")
        t = THEMES.get(t_key, THEMES["light"])
        self.setStyleSheet(f"""
            SharpConfirmDialog {{
                background-color: {t['surface_2']};
                border: 2px solid {DESTRUCTIVE_RED};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 20)
        layout.setSpacing(14)

        # Header with Red Warning Icon
        h_row = QHBoxLayout()
        h_row.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_pixmap("alert", size=24, color=DESTRUCTIVE_RED))
        h_row.addWidget(icon_lbl)

        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(f"font-size: 15px; font-weight: 800; color: {t['text']};")
        h_row.addWidget(title_lbl)
        h_row.addStretch()
        layout.addLayout(h_row)

        # Warning Message
        msg_lbl = QLabel(message)
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet(f"font-size: 12px; line-height: 1.4; color: {t['text']};")
        layout.addWidget(msg_lbl)

        layout.addStretch()

        # Action Buttons Row
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        btn_row.addStretch()

        self.cancel_btn = SharpButton("Cancel", icon_name="cross", variant="outline")
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.cancel_btn)

        self.confirm_btn = SharpButton(confirm_text, icon_name="trash", variant="danger")
        self.confirm_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.confirm_btn)

        layout.addLayout(btn_row)

def confirm_destructive_action(
    parent: QWidget,
    title: str,
    message: str,
    confirm_text: str = "Yes, Proceed"
) -> bool:
    """Helper that presents the confirmation dialog and returns True if accepted."""
    dialog = SharpConfirmDialog(title, message, confirm_text, parent)
    return dialog.exec() == QDialog.DialogCode.Accepted
