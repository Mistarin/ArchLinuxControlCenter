"""
DependencyButton: Smart action button that automatically verifies system dependencies.
If missing, dynamically presents an Install prompt button.
"""

from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QSize
from cachy_control.core.service_registry import ServiceRegistry
from cachy_control.ui.components.sharp_button import SharpButton
from cachy_control.ui.icons import get_icon

class DependencyButton(SharpButton):
    def __init__(
        self,
        binary_name: str,
        action_text: str,
        action_callback,
        icon_name: str = "play",
        variant: str = "secondary",
        parent: QWidget = None
    ):
        super().__init__(action_text, icon_name, variant, parent)
        self.binary_name = binary_name
        self.action_text = action_text
        self.action_callback = action_callback
        self.orig_icon = icon_name
        self.orig_variant = variant
        self.services = ServiceRegistry.get()
        
        self.clicked.connect(self._handle_click)
        self.refresh_state()

    def refresh_state(self) -> bool:
        """Checks dependency and updates text/icon/style accordingly."""
        installed = self.services.deps.is_installed(self.binary_name)
        if installed:
            self.set_clean_text(self.action_text)
            icon_color = "#FFFFFF" if self.orig_variant in ("primary", "danger", "accent") else "#111111"
            self.setIcon(get_icon(self.orig_icon, size=16, color=icon_color))
            self.variant = self.orig_variant
        else:
            self.set_clean_text(f"Install {self.binary_name}")
            self.setIcon(get_icon("download", size=16, color="#FFFFFF"))
            self.variant = "accent"
        
        self.apply_style()
        return installed

    def _handle_click(self):
        if self.services.deps.is_installed(self.binary_name):
            self.action_callback()
        else:
            cmd = self.services.deps.get_install_command(self.binary_name)
            self.services.runner.run_command(cmd, on_finish=lambda _: self.refresh_state())
