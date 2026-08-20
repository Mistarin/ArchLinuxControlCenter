"""
SharpButton: Minimalist button with hard geometric edges and semantic token styling.
Adapts dynamically to the active theme palette with support for tooltips and hover tokens.

Theme key is resolved at construction time; no ServiceRegistry dependency.
"""

from PyQt6.QtWidgets import QPushButton, QWidget
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QCursor
from cachy_control.ui.icons import get_icon
from cachy_control.ui.theme import THEMES, DESTRUCTIVE_RED

class SharpButton(QPushButton):
    def __init__(
        self,
        text: str = "",
        icon_name: str = None,
        variant: str = "primary",
        tooltip: str = None,
        theme_key: str = "light",
        parent: QWidget = None
    ):
        safe_text = text.replace("&", "&&")
        super().__init__(safe_text, parent)
        self.variant = variant
        self.icon_name = icon_name
        self.raw_text = text
        self._theme_key = theme_key

        if tooltip:
            self.setToolTip(tooltip)

        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setFixedHeight(34)
        self.apply_style(theme_key)

    def set_clean_text(self, text: str):
        self.raw_text = text
        self.setText(text.replace("&", "&&"))

    def apply_style(self, theme_key: str = None):
        if not theme_key:
            theme_key = self._theme_key
        else:
            self._theme_key = theme_key
        t = THEMES.get(theme_key, THEMES["light"])

        # Determine colors by semantic variant
        if self.variant in ("primary", "accent", "install"):
            bg = t["accent"]
            hover_bg = t["accent_hover"]
            fg = t["accent_text"]
            border = "none"
            icon_color = fg
        elif self.variant in ("accent2", "info"):
            bg = t["accent2"]
            hover_bg = t.get("accent2_hover", t["accent2"])
            fg = "#FFFFFF"
            border = "none"
            icon_color = "#FFFFFF"
        elif self.variant in ("danger", "destructive"):
            bg = DESTRUCTIVE_RED  # #FF4D5A across ALL themes
            hover_bg = "#E03B47"
            fg = "#FFFFFF"
            border = "none"
            icon_color = "#FFFFFF"
        elif self.variant == "secondary":
            bg = t["surface_2"]
            hover_bg = t["nav_hover"]
            fg = t["text"]
            border = f"1px solid {t['border']}"
            icon_color = t["text"]
        else:  # outline / default
            bg = "transparent"
            hover_bg = t["nav_hover"]
            fg = t["text"]
            border = f"1px solid {t['border']}"
            icon_color = t["text"]

        if self.icon_name:
            self.setIcon(get_icon(self.icon_name, size=16, color=icon_color))
            self.setIconSize(QSize(16, 16))

        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg};
                color: {fg};
                border: {border};
                border-radius: 0px;
                padding: 6px 14px;
                font-weight: 700;
                font-size: 12px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: {hover_bg};
                border-color: {t["accent"]};
            }}
            QPushButton:pressed {{
                background-color: {hover_bg};
            }}
            QPushButton:disabled {{
                background-color: {t["surface"]};
                color: {t["muted"]};
                border: 1px solid {t["border"]};
            }}
        """)
