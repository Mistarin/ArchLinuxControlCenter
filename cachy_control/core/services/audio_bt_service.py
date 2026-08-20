"""
Audio & Bluetooth Service.
"""

import subprocess
import shutil
import re
from typing import List
from cachy_control.core.contracts.audio_bt_contract import IAudioBtService, BluetoothDevice, AudioNode

class AudioBtService(IAudioBtService):
    def get_bluetooth_devices(self) -> List[BluetoothDevice]:
        devices: List[BluetoothDevice] = []
        if not shutil.which("bluetoothctl"):
            return devices

        try:
            res = subprocess.run(["bluetoothctl", "devices"], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                for line in res.stdout.strip().split("\n"):
                    # Format: Device XX:XX:XX:XX:XX:XX DeviceName
                    match = re.match(r"^Device\s+([0-9A-Fa-f:]+)\s+(.*)$", line.strip())
                    if match:
                        mac, name = match.groups()
                        # Get detailed info for this device
                        info_res = subprocess.run(["bluetoothctl", "info", mac], capture_output=True, text=True, timeout=1)
                        info_text = info_res.stdout
                        connected = "Connected: yes" in info_text
                        paired = "Paired: yes" in info_text
                        trusted = "Trusted: yes" in info_text
                        devices.append(BluetoothDevice(
                            mac=mac,
                            name=name,
                            connected=connected,
                            paired=paired,
                            trusted=trusted
                        ))
        except Exception:
            pass
        return devices

    def get_audio_nodes(self) -> List[AudioNode]:
        nodes: List[AudioNode] = []
        if not shutil.which("pactl"):
            return nodes

        try:
            # Sinks (Outputs)
            res = subprocess.run(["pactl", "list", "short", "sinks"], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                for line in res.stdout.strip().split("\n"):
                    if not line.strip():
                        continue
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        idx = int(parts[0]) if parts[0].isdigit() else 0
                        name = parts[1]
                        nodes.append(AudioNode(
                            id=idx,
                            name=name,
                            description=name.split(".")[-1],
                            is_default=False,
                            volume_percent=100,
                            node_type="sink"
                        ))
        except Exception:
            pass
        return nodes

    def get_bt_connect_command(self, mac: str) -> str:
        return f"bluetoothctl connect {mac}"

    def get_bt_disconnect_command(self, mac: str) -> str:
        return f"bluetoothctl disconnect {mac}"

    def get_bt_pair_trust_command(self, mac: str) -> str:
        return f"bluetoothctl pair {mac} && bluetoothctl trust {mac} && bluetoothctl connect {mac}"

    def get_bt_restart_command(self) -> str:
        return "sudo systemctl restart bluetooth"

    def get_bt_autoconnect_setup_script(self) -> str:
        return """mkdir -p ~/.config/systemd/user
cat << 'SERVICE_EOF' > ~/.config/systemd/user/bluetooth-autoconnect.service
[Unit]
Description=Bluetooth Auto-connect Service
After=bluetooth.target

[Service]
Type=simple
ExecStart=/usr/bin/bluetoothctl power on
Restart=on-failure

[Install]
WantedBy=default.target
SERVICE_EOF

systemctl --user daemon-reload
systemctl --user enable --now bluetooth-autoconnect.service
echo "Bluetooth auto-connect service enabled!"
"""
