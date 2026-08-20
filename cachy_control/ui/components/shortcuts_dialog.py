"""
ShortcutsDialog: Crisp modal presenting complete keyboard shortcut reference.
"""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QFrame
)
from PyQt6.QtCore import Qt
from cachy_control.ui.components.sharp_button import SharpButton
from cachy_control.ui.icons import get_pixmap
from cachy_control.ui.theme import THEMES
from cachy_control.core.service_registry import ServiceRegistry

class ShortcutsDialog(QDialog):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setWindowTitle("Keyboard Shortcuts & Hotkeys")
        self.setModal(True)
        self.setFixedSize(620, 440)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.FramelessWindowHint)

        services = ServiceRegistry.get()
        t_key = services.settings.get("theme", "light")
        t = THEMES.get(t_key, THEMES["light"])

        self.setStyleSheet(f"""
            ShortcutsDialog {{
                background-color: {t['surface_2']};
                border: 2px solid {t['border']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 22, 24, 22)
        layout.setSpacing(14)

        # Header
        h_row = QHBoxLayout()
        h_row.setSpacing(10)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(get_pixmap("sliders", size=24, color=t["accent"]))
        h_row.addWidget(icon_lbl)

        title_lbl = QLabel("KEYBOARD SHORTCUTS & NAVIGATION")
        title_lbl.setStyleSheet(f"font-size: 14px; font-weight: 800; letter-spacing: 1px; color: {t['text']};")
        h_row.addWidget(title_lbl)
        h_row.addStretch()

        close_btn = SharpButton("", icon_name="cross", variant="outline")
        close_btn.setFixedSize(26, 26)
        close_btn.clicked.connect(self.accept)
        h_row.addWidget(close_btn)
        layout.addLayout(h_row)

        desc_lbl = QLabel("Fast power-user shortcuts for terminal control, sub-page navigation, and modules:")
        desc_lbl.setStyleSheet(f"font-size: 11px; color: {t['muted']};")
        layout.addWidget(desc_lbl)

        # Container list
        list_frame = QFrame()
        list_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {t['background']};
                border: 1px solid {t['border']};
            }}
        """)
        list_layout = QVBoxLayout(list_frame)
        list_layout.setContentsMargins(14, 12, 14, 12)
        list_layout.setSpacing(8)

        shortcuts = [
            ("Shift + T  /  Ctrl + `  /  F12", "Toggle Live Terminal drawer & focus input"),
            ("Q  /  E", "Switch to Previous / Next Sub-Tab in active module"),
            ("Tab  /  Shift + Tab", "Cycle through Next / Previous Main Modules"),
            ("Ctrl + 1 ... Ctrl + 9", "Jump directly to Main Sidebar Module (1 to 9)"),
            ("Ctrl + F  /  /", "Focus Search / Filter box in active module"),
            ("Esc", "Close terminal drawer / unfocus search input"),
            ("Up / Down Arrows", "Cycle command history in terminal input line"),
            ("F1  /  ?", "Show this Keyboard Shortcuts reference guide"),
        ]

        for keys, desc in shortcuts:
            row = QHBoxLayout()
            row.setSpacing(12)

            k_lbl = QLabel(keys)
            k_lbl.setFixedWidth(240)
            k_lbl.setStyleSheet(f"background: transparent; border: none; font-family: 'JetBrains Mono', monospace; font-weight: 800; font-size: 11px; color: {t['accent2']};")
            
            d_lbl = QLabel(desc)
            d_lbl.setStyleSheet(f"background: transparent; border: none; font-size: 11px; color: {t['text']};")

            row.addWidget(k_lbl)
            row.addWidget(d_lbl, 1)
            list_layout.addLayout(row)

        layout.addWidget(list_frame)
        layout.addStretch()

        # Bottom Action
        b_row = QHBoxLayout()
        b_row.addStretch()
        done_btn = SharpButton("Got It (Esc)", icon_name="check", variant="primary")
        done_btn.clicked.connect(self.accept)
        b_row.addWidget(done_btn)
        layout.addLayout(b_row)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Escape, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.accept()
        else:
            super().keyPressEvent(event)
