"""
SharpCard: Base elevated container with geometric hard corners.
Automatically adapts to active theme palette.
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QWidget, QLayout
from PyQt6.QtCore import Qt
from cachy_control.ui.theme import create_card_shadow, THEMES
from cachy_control.core.service_registry import ServiceRegistry

class SharpCard(QFrame):
    def __init__(self, title: str = "", subtitle: str = "", parent: QWidget = None):
        super().__init__(parent)
        self.services = ServiceRegistry.get()
        self.setObjectName("sharpCard")
        self.setGraphicsEffect(create_card_shadow())
        
        self.layout_main = QVBoxLayout(self)
        self.layout_main.setContentsMargins(18, 16, 18, 16)
        self.layout_main.setSpacing(12)

        self.title_lbl = None
        self.sub_lbl = None

        if title or subtitle:
            header_layout = QVBoxLayout()
            header_layout.setSpacing(2)

            if title:
                self.title_lbl = QLabel(title)
                self.title_lbl.setStyleSheet("font-size: 14px; font-weight: 800;")
                header_layout.addWidget(self.title_lbl)

            if subtitle:
                self.sub_lbl = QLabel(subtitle)
                self.sub_lbl.setStyleSheet("font-size: 11px;")
                header_layout.addWidget(self.sub_lbl)

            self.layout_main.addLayout(header_layout)

        self.apply_theme_style()

    def apply_theme_style(self, theme_key: str = None):
        if not theme_key:
            theme_key = self.services.settings.get("theme", "light")
        t = THEMES.get(theme_key, THEMES["light"])
        self.setStyleSheet(f"""
            QFrame#sharpCard, SharpCard {{
                background-color: {t["card_bg"]};
                border: 1px solid {t["border"]};
                border-radius: 0px;
            }}
        """)
        if self.title_lbl:
            self.title_lbl.setStyleSheet(f"font-size: 14px; font-weight: 800; color: {t['text']};")
        if self.sub_lbl:
            self.sub_lbl.setStyleSheet(f"font-size: 11px; color: {t['subtext']};")

    def add_widget(self, widget: QWidget) -> None:
        self.layout_main.addWidget(widget)

    def add_layout(self, layout: QLayout) -> None:
        self.layout_main.addLayout(layout)
