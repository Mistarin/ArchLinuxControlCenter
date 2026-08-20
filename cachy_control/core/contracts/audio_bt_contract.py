"""Audio & Bluetooth Service Contract."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

@dataclass
class BluetoothDevice:
    mac: str
    name: str
    connected: bool
    paired: bool
    trusted: bool

@dataclass
class AudioNode:
    id: int
    name: str
    description: str
    is_default: bool
    volume_percent: int
    node_type: str  # 'sink' (output) or 'source' (input)

class IAudioBtService(ABC):
    @abstractmethod
    def get_bluetooth_devices(self) -> List[BluetoothDevice]:
        pass

    @abstractmethod
    def get_audio_nodes(self) -> List[AudioNode]:
        pass
