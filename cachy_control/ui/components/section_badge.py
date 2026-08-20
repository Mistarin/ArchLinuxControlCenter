"""
SectionBadge: Minimalist, high-contrast label for section identification. Zero emojis.
Adapts dynamically to the active theme palette.
"""

from PyQt6.QtWidgets import QLabel, QWidget
from cachy_control.ui.theme import SECTION_COLORS, THEMES
from cachy_control.core.service_registry import ServiceRegistry

class SectionBadge(QLabel):
    def __init__(self, section_key: str, custom_text: str = "", parent: QWidget = None):
        self.section_key = section_key
        self.custom_text = custom_text
        self.services = ServiceRegistry.get()
        cfg = SECTION_COLORS.get(section_key, {"name": section_key})
        text = custom_text or cfg["name"].upper()
        super().__init__(f"  {text}  ", parent)
        self.apply_theme_style()

    def apply_theme_style(self, theme_key: str = None):
        if not theme_key:
            theme_key = self.services.settings.get("theme", "light")
        theme_key = self.services.settings.get("theme", "light")
        t = THEMES.get(theme_key, THEMES["light"])
        cfg = SECTION_COLORS.get(self.section_key, {"primary": t["accent"], "bg": t["nav_hover"], "border": t["border"], "name": self.section_key})

        if theme_key == "light":
            bg = cfg.get("bg", "#F4F4F5")
            fg = cfg.get("primary", "#111111")
            border = cfg.get("border", "#E4E4E7")
        else:
            bg = t["card_bg"]
            fg = t["accent"]
            border = t["border"]

        self.setStyleSheet(f"""
            QLabel {{
                color: {fg};
                background-color: {bg};
                border: 1px solid {border};
                border-radius: 0px;
                font-size: 10px;
                font-weight: 800;
                letter-spacing: 0.8px;
                padding: 3px 8px;
            }}
        """)
