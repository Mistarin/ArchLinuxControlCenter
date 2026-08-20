"""
StatGauge: Clean metric progress bar and value card.
Adapts dynamically to the active theme palette.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar
from PyQt6.QtCore import Qt
from cachy_control.ui.theme import THEMES
from cachy_control.core.service_registry import ServiceRegistry

class StatGauge(QWidget):
    def __init__(self, label: str, unit: str = "%", parent: QWidget = None):
        super().__init__(parent)
        self.unit = unit
        self.services = ServiceRegistry.get()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        header = QHBoxLayout()
        self.title_label = QLabel(label)
        self.value_label = QLabel(f"0 {unit}")
        
        header.addWidget(self.title_label)
        header.addStretch()
        header.addWidget(self.value_label)
        layout.addLayout(header)

        self.bar = QProgressBar()
        self.bar.setRange(0, 100)
        self.bar.setValue(0)
        self.bar.setTextVisible(False)
        self.bar.setFixedHeight(8)
        layout.addWidget(self.bar)

        self.apply_theme_style()

    def apply_theme_style(self, theme_key: str = None):
        if not theme_key:
            theme_key = self.services.settings.get("theme", "light")
        theme_key = self.services.settings.get("theme", "light")
        t = THEMES.get(theme_key, THEMES["light"])

        self.title_label.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {t['subtext']};")
        self.value_label.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {t['text']};")
        self.bar.setStyleSheet(f"""
            QProgressBar {{
                background-color: {t['sidebar']};
                border: 1px solid {t['border']};
                border-radius: 0px;
            }}
            QProgressBar::chunk {{
                background-color: {t['accent']};
                border-radius: 0px;
            }}
        """)

    def set_value(self, percent: float, detail_text: str = "") -> None:
        self.bar.setValue(int(percent))
        if detail_text:
            self.value_label.setText(detail_text)
        else:
            self.value_label.setText(f"{percent:.1f} {self.unit}")
