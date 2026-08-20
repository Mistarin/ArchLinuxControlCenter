"""System Service Contract."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Any

@dataclass
class SystemMetrics:
    cpu_percent: float
    cpu_cores: int
    ram_total_gb: float
    ram_used_gb: float
    ram_percent: float
    swap_total_gb: float
    swap_used_gb: float
    swap_percent: float
    zram_info: str
    swappiness: int

class ISystemService(ABC):
    @abstractmethod
    def get_metrics(self) -> SystemMetrics:
        pass

    @abstractmethod
    def get_java_versions(self) -> List[str]:
        pass

    @abstractmethod
    def schedule_shutdown(self, minutes: int) -> str:
        pass

    @abstractmethod
    def cancel_shutdown(self) -> str:
        pass

    @abstractmethod
    def is_app_menu_installed(self) -> bool:
        pass

    @abstractmethod
    def install_app_menu(self) -> bool:
        pass

    @abstractmethod
    def uninstall_app_menu(self) -> bool:
        pass

    @abstractmethod
    def is_autostart_enabled(self) -> bool:
        pass

    @abstractmethod
    def enable_autostart(self) -> bool:
        pass

    @abstractmethod
    def disable_autostart(self) -> bool:
        pass
