"""
Service Registry for Dependency Injection (DIP).
Provides centralized access to singleton service instances across views and components.
"""

from typing import Optional
from cachy_control.config.settings import SettingsManager
from cachy_control.core.services.runner_service import RunnerService
from cachy_control.core.services.system_service import SystemService
from cachy_control.core.services.package_service import PackageService
from cachy_control.core.services.storage_service import StorageService
from cachy_control.core.services.audio_bt_service import AudioBtService
from cachy_control.core.services.vm_service import VmService
from cachy_control.core.services.dev_server_service import DevServerService
from cachy_control.core.services.gaming_service import GamingService
from cachy_control.core.services.dependency_service import DependencyService
from cachy_control.core.services.cleanup_service import CleanupService
from cachy_control.core.services.security_service import SecurityService
from cachy_control.core.services.zram_service import ZramService

class ServiceRegistry:
    _instance: Optional['ServiceRegistry'] = None

    def __init__(self):
        self.settings = SettingsManager()
        self.runner = RunnerService()
        self.system = SystemService()
        self.packages = PackageService()
        self.storage = StorageService()
        self.audio_bt = AudioBtService()
        self.vm = VmService()
        self.dev_server = DevServerService()
        self.server = self.dev_server
        self.gaming = GamingService()
        self.deps = DependencyService()
        self.cleanup = CleanupService()
        self.security = SecurityService()
        self.zram = ZramService()

    @classmethod
    def get(cls) -> 'ServiceRegistry':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
