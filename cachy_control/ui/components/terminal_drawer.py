"""
TerminalDrawer: Permanently docked execution terminal drawer with semantic ANSI-level styling.
Modules bend around it seamlessly.
Supports interactive text input, live scroll, clear, copy, and full semantic theme integration.
"""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPlainTextEdit,
    QLineEdit, QPushButton, QWidget, QApplication
)
from PyQt6.QtCore import Qt, pyqtSignal, QEvent
from PyQt6.QtGui import QFont, QKeyEvent
from cachy_control.ui.components.sharp_button import SharpButton
from cachy_control.ui.theme import create_deep_shadow, THEMES, DESTRUCTIVE_RED
from cachy_control.core.service_registry import ServiceRegistry

class InteractiveTerminalInput(QLineEdit):
    """Command input line that captures Enter and history up/down arrows."""
    def __init__(self, on_submit, parent: QWidget = None):
        super().__init__(parent)
        self.on_submit = on_submit
        self.history = []
        self.history_index = -1
        self.setPlaceholderText("Type command / stdin here and press Enter (e.g. y, sudo pacman -Syu)...")
        self.returnPressed.connect(self._handle_enter)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Up:
            if self.history and self.history_index < len(self.history) - 1:
                self.history_index += 1
                self.setText(self.history[-(self.history_index + 1)])
            return
        elif event.key() == Qt.Key.Key_Down:
            if self.history_index > 0:
                self.history_index -= 1
                self.setText(self.history[-(self.history_index + 1)])
            elif self.history_index == 0:
                self.history_index = -1
                self.clear()
            return
        super().keyPressEvent(event)

    def _handle_enter(self):
        text = self.text()
        if text.strip():
            if not self.history or self.history[-1] != text:
                self.history.append(text)
            self.history_index = -1
        self.on_submit(text)
        self.clear()

class TerminalDrawer(QFrame):
    cancel_requested = pyqtSignal()

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.services = ServiceRegistry.get()
        self.setGraphicsEffect(create_deep_shadow())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(8)

        # 1. Header
        header = QHBoxLayout()
        header.setSpacing(10)

        self.status_dot = QLabel("●")
        self.status_dot.setStyleSheet("color: #10B981; font-size: 14px;")
        header.addWidget(self.status_dot)

        self.title_label = QLabel("LIVE EXECUTION TERMINAL")
        header.addWidget(self.title_label)

        self.cmd_preview = QLabel("Idle (Ready for input)")
        header.addWidget(self.cmd_preview)

        header.addStretch()

        self.copy_btn = SharpButton("Copy", icon_name="external_link", variant="outline")
        self.copy_btn.clicked.connect(self._copy_log)
        header.addWidget(self.copy_btn)

        self.clear_btn = SharpButton("Clear", icon_name="trash", variant="outline")
        self.clear_btn.clicked.connect(self.clear)
        header.addWidget(self.clear_btn)

        self.stop_btn = SharpButton("Stop Process", icon_name="stop", variant="danger")
        self.stop_btn.clicked.connect(self.cancel_requested.emit)
        self.stop_btn.hide()
        header.addWidget(self.stop_btn)

        layout.addLayout(header)

        # 2. Log Output Box
        self.log_box = QPlainTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFont(QFont("JetBrains Mono", 10))
        self.log_box.setMinimumHeight(130)
        self.log_box.setMaximumBlockCount(10000)
        layout.addWidget(self.log_box)

        # 3. Interactive Input Line
        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.prompt_lbl = QLabel(">")
        input_row.addWidget(self.prompt_lbl)

        self.input_field = InteractiveTerminalInput(self._handle_submit)
        input_row.addWidget(self.input_field, 1)

        self.send_btn = SharpButton("Send / Run", icon_name="play", variant="primary")
        self.send_btn.clicked.connect(self._handle_button_send)
        input_row.addWidget(self.send_btn)

        layout.addLayout(input_row)

        saved_theme = self.services.settings.get("theme", "light")
        self.apply_theme_style(saved_theme)

    def apply_theme_style(self, theme_key: str = None):
        if not theme_key:
            theme_key = self.services.settings.get("theme", "light")
        t = THEMES.get(theme_key, THEMES["light"])

        self.setStyleSheet(f"""
            TerminalDrawer {{
                background-color: {t['surface_2']};
                border: 1px solid {t['border']};
                border-radius: 0px;
            }}
        """)
        self.title_label.setStyleSheet(f"color: {t['text']}; font-weight: 700; font-size: 11px; letter-spacing: 1px;")
        self.cmd_preview.setStyleSheet(f"color: {t['muted']}; font-size: 11px; font-family: monospace;")
        self.log_box.setStyleSheet(f"""
            QPlainTextEdit {{
                background-color: {t['background']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 0px;
                padding: 10px;
                font-family: 'JetBrains Mono', 'Fira Code', monospace;
                font-size: 11px;
            }}
        """)
        self.prompt_lbl.setStyleSheet(f"color: {t['accent']}; font-family: monospace; font-size: 14px; font-weight: 900;")
        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {t['background']};
                color: {t['text']};
                border: 1px solid {t['border']};
                border-radius: 0px;
                padding: 6px 10px;
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
            }}
            QLineEdit:focus {{
                border: 1px solid {t['accent']};
            }}
        """)

    def _handle_button_send(self):
        self.input_field._handle_enter()

    def _handle_submit(self, text: str):
        if self.services.runner.is_running():
            self.services.runner.write_input(text)
        else:
            if text.strip():
                self.services.runner.run_command(text)

    def append_text(self, text: str) -> None:
        self.log_box.insertPlainText(text)
        self.log_box.ensureCursorVisible()

    def set_running(self, running: bool, command: str = "") -> None:
        theme_key = self.services.settings.get("theme", "light")
        t = THEMES.get(theme_key, THEMES["light"])

        if running:
            self.status_dot.setStyleSheet(f"color: {t['warning']}; font-size: 14px;")
            self.title_label.setText("PROCESS RUNNING")
            self.cmd_preview.setText(f"Running: {command[:60]}..." if len(command) > 60 else f"Running: {command}")
            self.stop_btn.show()
        else:
            self.status_dot.setStyleSheet(f"color: {t['success']}; font-size: 14px;")
            self.title_label.setText("LIVE EXECUTION TERMINAL")
            self.cmd_preview.setText("Idle (Ready for input)")
            self.stop_btn.hide()

    def clear(self) -> None:
        self.log_box.clear()

    def _copy_log(self) -> None:
        text = self.log_box.toPlainText()
        if text:
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
