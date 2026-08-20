"""VM & Network Service Contract."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

@dataclass
class VirshNetwork:
    name: str
    state: str
    autostart: str
    persistent: str

@dataclass
class ListeningPort:
    protocol: str
    port: int
    address: str
    process: str
    pid: str

class IVmService(ABC):
    @abstractmethod
    def get_virsh_networks(self) -> List[VirshNetwork]:
        pass

    @abstractmethod
    def get_listening_ports(self) -> List[ListeningPort]:
        pass
