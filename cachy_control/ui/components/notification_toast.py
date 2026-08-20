"""
NotificationToast: Floating bottom-right action feedback toast.
Shows discrete non-blocking notifications with semantic theme palettes.
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from cachy_control.ui.icons import get_pixmap
from cachy_control.ui.theme import create_deep_shadow, THEMES, DESTRUCTIVE_RED
from cachy_control.core.service_registry import ServiceRegistry

class NotificationToast(QFrame):
    view_terminal_requested = pyqtSignal()

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setFixedSize(360, 95)
        self.setGraphicsEffect(create_deep_shadow())
        self.services = ServiceRegistry.get()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(6)

        # Header Row: Icon + Title + Close button
        h_row = QHBoxLayout()
        h_row.setSpacing(8)

        self.icon_lbl = QLabel()
        h_row.addWidget(self.icon_lbl)

        self.title_lbl = QLabel("Action Completed")
        self.title_lbl.setStyleSheet("font-weight: 800; font-size: 12px;")
        h_row.addWidget(self.title_lbl)
        h_row.addStretch()

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(18, 18)
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 11px;
                opacity: 0.6;
            }
            QPushButton:hover { opacity: 1.0; }
        """)
        self.close_btn.clicked.connect(self.hide)
        h_row.addWidget(self.close_btn)
        layout.addLayout(h_row)

        # Body Message Row
        self.msg_lbl = QLabel("Operation executed successfully.")
        self.msg_lbl.setWordWrap(True)
        self.msg_lbl.setStyleSheet("font-size: 11px; opacity: 0.85;")
        layout.addWidget(self.msg_lbl)

        # Bottom Actions Row
        b_row = QHBoxLayout()
        b_row.addStretch()

        self.view_term_btn = QPushButton("View Terminal Output →")
        self.view_term_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.view_term_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 11px;
                font-weight: 700;
            }
        """)
        self.view_term_btn.clicked.connect(self._on_view_term_clicked)
        b_row.addWidget(self.view_term_btn)
        layout.addLayout(b_row)

        # Auto-dismiss timer
        self.dismiss_timer = QTimer(self)
        self.dismiss_timer.setSingleShot(True)
        self.dismiss_timer.timeout.connect(self.hide)

        self.hide()

    def show_toast(self, title: str, message: str, level: str = "success", duration_ms: int = 6000):
        t_key = self.services.settings.get("theme", "light")
        t = THEMES.get(t_key, THEMES["light"])

        self.title_lbl.setText(title)
        self.title_lbl.setStyleSheet(f"font-weight: 800; font-size: 12px; color: {t['text']};")
        self.msg_lbl.setText(message)
        self.msg_lbl.setStyleSheet(f"font-size: 11px; color: {t['muted']};")
        self.view_term_btn.setStyleSheet(f"background-color: transparent; border: none; font-size: 11px; font-weight: 700; color: {t['accent2']};")

        if level == "error":
            self.icon_lbl.setPixmap(get_pixmap("alert", size=18, color=DESTRUCTIVE_RED))
            self.setStyleSheet(f"""
                NotificationToast {{
                    background-color: {t['surface_2']};
                    border: 1px solid {t['border']};
                    border-left: 4px solid {DESTRUCTIVE_RED};
                }}
            """)
        elif level == "warning":
            self.icon_lbl.setPixmap(get_pixmap("alert", size=18, color=t["warning"]))
            self.setStyleSheet(f"""
                NotificationToast {{
                    background-color: {t['surface_2']};
                    border: 1px solid {t['border']};
                    border-left: 4px solid {t['warning']};
                }}
            """)
        else: # Success
            self.icon_lbl.setPixmap(get_pixmap("check", size=18, color=t["success"]))
            self.setStyleSheet(f"""
                NotificationToast {{
                    background-color: {t['surface_2']};
                    border: 1px solid {t['border']};
                    border-left: 4px solid {t['success']};
                }}
            """)

        self.reposition()
        self.show()
        self.raise_()
        self.dismiss_timer.start(duration_ms)

    def _on_view_term_clicked(self):
        self.hide()
        self.view_terminal_requested.emit()

    def reposition(self):
        parent = self.parentWidget()
        if parent:
            margin = 24
            x = parent.width() - self.width() - margin
            y = parent.height() - self.height() - margin
            self.move(x, y)
