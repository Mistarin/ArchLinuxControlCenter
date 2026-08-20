"""Storage & Cloud Service Contract."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

@dataclass
class DiskPartition:
    device: str
    mountpoint: str
    fstype: str
    total_gb: float
    used_gb: float
    free_gb: float
    percent: float

@dataclass
class CloudMount:
    remote_name: str
    mount_point: str
    is_mounted: bool

class IStorageService(ABC):
    @abstractmethod
    def get_disk_partitions(self) -> List[DiskPartition]:
        pass

    @abstractmethod
    def get_cloud_mounts(self) -> List[CloudMount]:
        pass
