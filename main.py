#!/usr/bin/env python3
"""
CachyOS Control Center - Entry Point
"""

import sys
import os
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

# Ensure cachy_control package is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cachy_control.app import MainWindow

def main():
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("CachyOS Control Center")
    app.setApplicationDisplayName("CachyOS Control Center")

    # Set default modern font
    font = QFont("Inter", 10)
    font.setStyleHint(QFont.StyleHint.SansSerif)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
