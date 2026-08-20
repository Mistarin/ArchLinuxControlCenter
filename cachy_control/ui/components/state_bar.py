"""
StateBar: App-wide execution state & progress monitoring bar with semantic token styling.
Displays live spinning progress, current task name, elapsed timer, and cancel button.
"""

from PyQt6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QProgressBar, QWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from cachy_control.ui.components.sharp_button import SharpButton
from cachy_control.ui.theme import THEMES
from cachy_control.core.service_registry import ServiceRegistry

class StateBar(QFrame):
    cancel_requested = pyqtSignal()

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setFixedHeight(34)
        self.services = ServiceRegistry.get()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Thin animated top progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(2)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Content Row
        content_row = QHBoxLayout()
        content_row.setContentsMargins(20, 0, 20, 0)
        content_row.setSpacing(10)

        # Status Dot & Text
        self.status_dot = QLabel("●")
        content_row.addWidget(self.status_dot)

        self.status_label = QLabel("Ready")
        content_row.addWidget(self.status_label)

        self.task_label = QLabel("")
        content_row.addWidget(self.task_label)

        content_row.addStretch()

        # Elapsed Timer Label
        self.timer_label = QLabel("")
        self.timer_label.hide()
        content_row.addWidget(self.timer_label)

        # Cancel Button (Destructive red)
        self.cancel_btn = SharpButton("Cancel Task", icon_name="stop", variant="danger")
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)
        self.cancel_btn.hide()
        content_row.addWidget(self.cancel_btn)

        layout.addLayout(content_row)

        # Elapsed Timer
        self.elapsed_seconds = 0
        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._update_clock)

        # Spinner Animation Timer
        self.spin_frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        self.spin_idx = 0
        self.spin_timer = QTimer(self)
        self.spin_timer.timeout.connect(self._update_spin)

        saved_theme = self.services.settings.get("theme", "light")
        self.apply_theme_style(saved_theme)

    def apply_theme_style(self, theme_key: str = "light"):
        t = THEMES.get(theme_key, THEMES["light"])
        self.setStyleSheet(f"""
            StateBar {{
                background-color: {t['surface']};
                border-bottom: 1px solid {t['border']};
            }}
        """)
        self.progress_bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: transparent;
                border: none;
            }}
            QProgressBar::chunk {{
                background-color: {t['accent']};
            }}
        """)
        self.status_dot.setStyleSheet(f"color: {t['success']}; font-size: 12px;")
        self.status_label.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {t['text']};")
        self.task_label.setStyleSheet(f"font-size: 11px; font-family: monospace; color: {t['muted']};")
        self.timer_label.setStyleSheet(f"font-size: 11px; font-family: monospace; font-weight: 600; color: {t['muted']};")

    def set_running(self, running: bool, task_name: str = ""):
        theme_key = self.services.settings.get("theme", "light")
        t = THEMES.get(theme_key, THEMES["light"])

        if running:
            self.status_dot.setText("⠋")
            self.status_dot.setStyleSheet(f"color: {t['warning']}; font-size: 13px; font-weight: bold;")
            self.status_label.setText("Executing:")
            self.task_label.setText(task_name[:75] + ("..." if len(task_name) > 75 else ""))
            
            self.progress_bar.setRange(0, 0)
            self.progress_bar.show()

            self.elapsed_seconds = 0
            self.timer_label.setText("00:00s")
            self.timer_label.show()
            self.clock_timer.start(1000)
            self.spin_timer.start(80)

            self.cancel_btn.show()
        else:
            self.clock_timer.stop()
            self.spin_timer.stop()
            self.progress_bar.hide()
            self.cancel_btn.hide()
            self.timer_label.hide()

            self.status_dot.setText("●")
            self.status_dot.setStyleSheet(f"color: {t['success']}; font-size: 12px;")
            self.status_label.setText("Ready")
            self.task_label.setText("")

    def set_status(self, text: str, is_loading: bool = False):
        theme_key = self.services.settings.get("theme", "light")
        t = THEMES.get(theme_key, THEMES["light"])

        self.status_label.setText(text)
        if is_loading:
            self.status_dot.setText("⠋")
            self.status_dot.setStyleSheet(f"color: {t['warning']}; font-size: 13px; font-weight: bold;")
        else:
            self.status_dot.setText("●")
            self.status_dot.setStyleSheet(f"color: {t['success']}; font-size: 12px;")

    def _update_clock(self):
        self.elapsed_seconds += 1
        mins = self.elapsed_seconds // 60
        secs = self.elapsed_seconds % 60
        self.timer_label.setText(f"{mins:02d}:{secs:02d}s")

    def _update_spin(self):
        self.spin_idx = (self.spin_idx + 1) % len(self.spin_frames)
        self.status_dot.setText(self.spin_frames[self.spin_idx])
