"""
Theme and styling definitions for CachyOS Control Center.
Strict Semantic Token Architecture:
- Accent (Install / Positive Action)
- Accent2 (Informational / Neutral Highlight)
- Destructive (#FF4D5A across ALL themes)
- Success (Positive Completion)
- Warning (Amber / Orange)
- Text / Muted / Border / Background / Surface / Surface 2
"""

from typing import Dict
from PyQt6.QtWidgets import QGraphicsDropShadowEffect
from PyQt6.QtGui import QColor

DESTRUCTIVE_RED = "#FF4D5A"

THEMES = {
    "light": {
        "name": "Minimalist White (Default)",
        "background": "#F4F5F7",
        "surface": "#FFFFFF",
        "surface_2": "#FFFFFF",
        "border": "#E4E4E7",
        "text": "#111111",
        "muted": "#52525B",
        "accent": "#111111",
        "accent_hover": "#27272A",
        "accent_text": "#FFFFFF",
        "accent2": "#0284C7",
        "accent2_hover": "#0369A1",
        "destructive": DESTRUCTIVE_RED,
        "warning": "#D97706",
        "success": "#059669",
        "secondary_accent": "#EA580C",
        # Backward compatibility aliases
        "bg": "#F4F5F7",
        "sidebar": "#FFFFFF",
        "card_bg": "#FFFFFF",
        "subtext": "#52525B",
        "input_bg": "#FFFFFF",
        "nav_hover": "#F4F4F5",
        "nav_active_bg": "#E4E4E7",
        "table_alt": "#FAFAFA",
        "header_bg": "#F4F4F5",
        "header_border": "#E4E4E7",
        "divider": "#EA580C",
        "active_nav_border": "#111111",
    },
    "dark": {
        "name": "Dark — Neutral Graphite",
        "background": "#0D0F12",
        "surface": "#15181C",
        "surface_2": "#1C2025",
        "border": "#2A2F36",
        "text": "#F1F3F5",
        "muted": "#9AA1AA",
        "accent": "#7CFF8A",
        "accent_hover": "#65E672",
        "accent_text": "#0D0F12",
        "accent2": "#6EA8FF",
        "accent2_hover": "#5090F0",
        "destructive": DESTRUCTIVE_RED,
        "warning": "#FFB454",
        "success": "#54E38E",
        "secondary_accent": "#6EA8FF",
        # Backward compatibility aliases
        "bg": "#0D0F12",
        "sidebar": "#15181C",
        "card_bg": "#1C2025",
        "subtext": "#9AA1AA",
        "input_bg": "#15181C",
        "nav_hover": "#22272E",
        "nav_active_bg": "#22272E",
        "table_alt": "#191D22",
        "header_bg": "#22272E",
        "header_border": "#2A2F36",
        "divider": "#6EA8FF",
        "active_nav_border": "#7CFF8A",
    },
    "dark_blue": {
        "name": "Dark Blue — Deep Navy",
        "background": "#080D16",
        "surface": "#0E1624",
        "surface_2": "#152033",
        "border": "#26354A",
        "text": "#E8F0FA",
        "muted": "#8998AC",
        "accent": "#61E7A5",
        "accent_hover": "#4DD190",
        "accent_text": "#080D16",
        "accent2": "#5AA9FF",
        "accent2_hover": "#4293F0",
        "destructive": DESTRUCTIVE_RED,
        "warning": "#FFC15C",
        "success": "#45D98A",
        "secondary_accent": "#5AA9FF",
        # Backward compatibility aliases
        "bg": "#080D16",
        "sidebar": "#0E1624",
        "card_bg": "#152033",
        "subtext": "#8998AC",
        "input_bg": "#0E1624",
        "nav_hover": "#1C2A42",
        "nav_active_bg": "#1C2A42",
        "table_alt": "#121C2D",
        "header_bg": "#1C2A42",
        "header_border": "#26354A",
        "divider": "#5AA9FF",
        "active_nav_border": "#61E7A5",
    },
    "cyberpunk": {
        "name": "Cyberpunk — Black / Violet / Neon",
        "background": "#09070D",
        "surface": "#120D19",
        "surface_2": "#1B1226",
        "border": "#38234A",
        "text": "#F5EEFF",
        "muted": "#A895B8",
        "accent": "#00F5A0",
        "accent_hover": "#00DC90",
        "accent_text": "#09070D",
        "accent2": "#00D9FF",
        "accent2_hover": "#00B8D9",
        "destructive": DESTRUCTIVE_RED,
        "warning": "#FFE14A",
        "success": "#00F5A0",
        "secondary_accent": "#D946EF",
        # Backward compatibility aliases
        "bg": "#09070D",
        "sidebar": "#120D19",
        "card_bg": "#1B1226",
        "subtext": "#A895B8",
        "input_bg": "#120D19",
        "nav_hover": "#251933",
        "nav_active_bg": "#251933",
        "table_alt": "#160F1F",
        "header_bg": "#251933",
        "header_border": "#D946EF",
        "divider": "#D946EF",
        "active_nav_border": "#00F5A0",
    },
    "doom": {
        "name": "DOOM — Hellish Industrial",
        "background": "#0C0908",
        "surface": "#17110F",
        "surface_2": "#211714",
        "border": "#3A2821",
        "text": "#F2E9E3",
        "muted": "#A99A92",
        "accent": "#FFB52E",
        "accent_hover": "#E69E20",
        "accent_text": "#0C0908",
        "accent2": "#5CC8FF",
        "accent2_hover": "#3EB0EC",
        "destructive": DESTRUCTIVE_RED,
        "warning": "#FF7A24",
        "success": "#8EDC52",
        "secondary_accent": "#C52A24",
        # Backward compatibility aliases
        "bg": "#0C0908",
        "sidebar": "#17110F",
        "card_bg": "#211714",
        "subtext": "#A99A92",
        "input_bg": "#17110F",
        "nav_hover": "#2D1F1B",
        "nav_active_bg": "#2D1F1B",
        "table_alt": "#1B1311",
        "header_bg": "#2D1F1B",
        "header_border": "#C52A24",
        "divider": "#C52A24",
        "active_nav_border": "#FFB52E",
    }
}

SECTION_COLORS = {
    "store":     {"primary": "#059669", "bg": "#ECFDF5", "border": "#A7F3D0", "name": "App Store"},
    "dashboard": {"primary": "#0284C7", "bg": "#F0F9FF", "border": "#BAE6FD", "name": "Dashboard"},
    "updates":   {"primary": "#D97706", "bg": "#FFFBEB", "border": "#FDE68A", "name": "Updates"},
    "cleanup":   {"primary": "#059669", "bg": "#ECFDF5", "border": "#A7F3D0", "name": "System Cleanup"},
    "storage":   {"primary": "#4F46E5", "bg": "#EEF2FF", "border": "#C7D2FE", "name": "Storage & Cloud"},
    "audio_bt":  {"primary": "#7C3AED", "bg": "#F5F3FF", "border": "#DDD6FE", "name": "Audio & Bluetooth"},
    "network":   {"primary": "#0D9488", "bg": "#F0FDFA", "border": "#99F6E4", "name": "Network & VMs"},
    "gaming":    {"primary": "#E11D48", "bg": "#FFF1F2", "border": "#FECDD3", "name": "Gaming & Runners"},
    "zram":      {"primary": "#EA580C", "bg": "#FFF7ED", "border": "#FFEDD5", "name": "Memory & ZRAM"},
    "security":  {"primary": "#334155", "bg": "#F8FAFC", "border": "#CBD5E1", "name": "Security & Logs"},
    "settings":  {"primary": "#2563EB", "bg": "#EFF6FF", "border": "#BFDBFE", "name": "Settings & Themes"},
}

def get_theme_stylesheet(theme_key: str = "light") -> str:
    t = THEMES.get(theme_key, THEMES["light"])
    
    return f"""
    * {{
        font-family: 'Inter', 'Segoe UI', 'Ubuntu', 'Roboto', sans-serif;
        font-size: 13px;
        color: {t["text"]};
    }}

    QMainWindow, QWidget#rootWindow, QStackedWidget {{
        background-color: {t["background"]};
    }}

    QWidget#sidebar {{
        background-color: {t["surface"]};
        border-right: 1px solid {t["border"]};
    }}

    QLabel {{
        color: {t["text"]};
    }}

    QScrollArea, QScrollArea > QWidget, QScrollArea > QWidget > QWidget {{
        background-color: {t["background"]};
        border: none;
    }}

    QScrollBar:vertical {{
        border: none;
        background: {t["surface"]};
        width: 6px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background: {t["border"]};
        min-height: 20px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {t["accent"]};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    /* Inputs & Form Controls */
    QLineEdit, QPlainTextEdit, QTextEdit, QSpinBox, QComboBox {{
        background-color: {t["input_bg"]};
        border: 1px solid {t["border"]};
        border-radius: 0px;
        padding: 7px 10px;
        color: {t["text"]};
        selection-background-color: {t["accent"]};
        selection-color: {t["accent_text"]};
    }}

    QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QSpinBox:focus, QComboBox:focus {{
        border: 1px solid {t["accent"]};
        background-color: {t["input_bg"]};
    }}

    QComboBox QAbstractItemView {{
        background-color: {t["surface_2"]};
        color: {t["text"]};
        selection-background-color: {t["nav_hover"]};
        selection-color: {t["text"]};
        border: 1px solid {t["border"]};
    }}

    QComboBox::drop-down {{
        border: none;
        padding-right: 8px;
    }}

    /* Tables and Lists */
    QTableWidget, QTableView, QTreeWidget, QListWidget {{
        background-color: {t["surface_2"]};
        alternate-background-color: {t["table_alt"]};
        border: 1px solid {t["border"]};
        border-radius: 0px;
        gridline-color: {t["border"]};
        color: {t["text"]};
        selection-background-color: {t["nav_hover"]};
        selection-color: {t["text"]};
    }}

    QTableWidget::item {{
        color: {t["text"]};
        padding: 6px 8px;
        border-bottom: 1px solid {t["border"]};
    }}

    QHeaderView {{
        background-color: {t["header_bg"]};
        border: none;
    }}

    QHeaderView::section {{
        background-color: {t["header_bg"]};
        color: {t["text"]};
        padding: 7px 8px;
        border: none;
        border-bottom: 2px solid {t["header_border"]};
        font-weight: 700;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }}

    /* Progress bar */
    QProgressBar {{
        background-color: {t["surface"]};
        border: 1px solid {t["border"]};
        border-radius: 0px;
        text-align: center;
        font-weight: 600;
        font-size: 11px;
        height: 16px;
        color: {t["text"]};
    }}

    QProgressBar::chunk {{
        background-color: {t["accent"]};
    }}

    /* Checkbox */
    QCheckBox {{
        spacing: 8px;
        color: {t["text"]};
    }}

    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border: 1px solid {t["border"]};
        border-radius: 0px;
        background-color: {t["surface_2"]};
    }}

    QCheckBox::indicator:checked {{
        background-color: {t["accent"]};
        border-color: {t["accent"]};
    }}
    """

GLOBAL_STYLESHEET = get_theme_stylesheet("light")

def create_card_shadow() -> QGraphicsDropShadowEffect:
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(14)
    shadow.setXOffset(0)
    shadow.setYOffset(2)
    shadow.setColor(QColor(0, 0, 0, 14))
    return shadow

def create_deep_shadow() -> QGraphicsDropShadowEffect:
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(24)
    shadow.setXOffset(0)
    shadow.setYOffset(6)
    shadow.setColor(QColor(0, 0, 0, 26))
    return shadow
