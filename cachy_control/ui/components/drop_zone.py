"""
DropZone: Drag and drop target for Arch package files (.pkg.tar.zst / .pkg.tar.xz).
Adapts dynamically to the active theme palette.
"""

from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel, QFileDialog, QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent
from cachy_control.ui.components.sharp_button import SharpButton
from cachy_control.ui.icons import get_pixmap
from cachy_control.ui.theme import THEMES
from cachy_control.core.service_registry import ServiceRegistry

class DropZone(QFrame):
    file_selected = pyqtSignal(str)

    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.services = ServiceRegistry.get()
        self.setAcceptDrops(True)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(10)

        self.icon_label = QLabel()
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.icon_label)

        self.text_label = QLabel("Drag and drop .pkg.tar.zst / .pkg.tar.xz file here")
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.text_label)

        self.browse_btn = SharpButton("Browse Package File...", icon_name="folder", variant="outline")
        self.browse_btn.clicked.connect(self._browse_file)
        layout.addWidget(self.browse_btn, alignment=Qt.AlignmentFlag.AlignCenter)

        self.apply_theme_style()

    def apply_theme_style(self, theme_key: str = None):
        if not theme_key:
            theme_key = self.services.settings.get("theme", "light")
        theme_key = self.services.settings.get("theme", "light")
        t = THEMES.get(theme_key, THEMES["light"])

        self.setStyleSheet(f"""
            DropZone {{
                background-color: {t['sidebar']};
                border: 2px dashed {t['border']};
                border-radius: 0px;
                padding: 20px;
            }}
            DropZone:hover {{
                border-color: {t['accent']};
                background-color: {t['nav_hover']};
            }}
        """)
        self.icon_label.setPixmap(get_pixmap("upload", size=32, color=t["subtext"]))
        self.text_label.setStyleSheet(f"font-weight: 600; color: {t['text']}; font-size: 12px;")

    def _browse_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Arch Linux Package",
            "",
            "Arch Packages (*.pkg.tar.zst *.pkg.tar.xz *.pkg.tar);;All Files (*)"
        )
        if file_path:
            self.file_selected.emit(file_path)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if any(path.endswith(ext) for ext in [".pkg.tar.zst", ".pkg.tar.xz", ".pkg.tar"]):
                self.file_selected.emit(path)
