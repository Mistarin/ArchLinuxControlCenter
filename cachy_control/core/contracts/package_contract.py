"""Package Service Contract."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

@dataclass
class PackageItem:
    name: str
    version: str
    repo_or_source: str  # e.g. "core", "extra", "AUR", "flatpak"
    description: str
    installed: bool

@dataclass
class PendingUpdate:
    name: str
    old_version: str
    new_version: str
    repo_or_source: str
    download_size: str
    build_date: str

class IPackageService(ABC):
    @abstractmethod
    def search_all(self, query: str) -> List[PackageItem]:
        """Searches across Pacman, AUR (yay/paru), and Flatpak."""
        pass

    @abstractmethod
    def get_pending_updates(self) -> List[PendingUpdate]:
        """Checks for pending updates across Pacman, AUR, and Flatpak with sizes and dates."""
        pass

    @abstractmethod
    def get_update_command(self, manager: str) -> str:
        """Returns the update command for a specific manager ('pacman', 'yay', 'paru', 'flatpak', 'all')."""
        pass
