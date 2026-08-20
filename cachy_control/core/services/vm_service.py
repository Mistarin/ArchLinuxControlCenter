"""
Virtual Machines (Virsh/Libvirt) & Network Diagnostics Service.
"""

import subprocess
import shutil
import re
from typing import List
from cachy_control.core.contracts.vm_contract import IVmService, VirshNetwork, ListeningPort

class VmService(IVmService):
    def get_virsh_networks(self) -> List[VirshNetwork]:
        networks: List[VirshNetwork] = []
        if not shutil.which("virsh"):
            return networks

        try:
            res = subprocess.run(["virsh", "net-list", "--all"], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                lines = res.stdout.strip().split("\n")
                # Skip header lines (Name, State, Autostart, Persistent, and separator dashes)
                for line in lines[2:]:
                    parts = line.split()
                    if len(parts) >= 4:
                        networks.append(VirshNetwork(
                            name=parts[0],
                            state=parts[1],
                            autostart=parts[2],
                            persistent=parts[3]
                        ))
        except Exception:
            pass
        return networks

    def get_listening_ports(self) -> List[ListeningPort]:
        ports: List[ListeningPort] = []
        if not shutil.which("ss"):
            return ports

        try:
            res = subprocess.run(["ss", "-tulpn"], capture_output=True, text=True, timeout=2)
            if res.returncode == 0:
                for line in res.stdout.strip().split("\n")[1:]:
                    parts = line.split()
                    if len(parts) >= 5:
                        proto = parts[0]
                        local_addr = parts[4]
                        # extract port
                        port_match = re.search(r":(\d+)$", local_addr)
                        port_num = int(port_match.group(1)) if port_match else 0
                        
                        proc_info = parts[6] if len(parts) >= 7 else "-"
                        # Extract process name & pid if available: users:(("python3",pid=1234,fd=3))
                        proc_name = "-"
                        pid = "-"
                        proc_match = re.search(r'\(\("([^"]+)",pid=(\d+)', proc_info)
                        if proc_match:
                            proc_name = proc_match.group(1)
                            pid = proc_match.group(2)

                        ports.append(ListeningPort(
                            protocol=proto,
                            port=port_num,
                            address=local_addr,
                            process=proc_name,
                            pid=pid
                        ))
        except Exception:
            pass
        return sorted(ports, key=lambda x: x.port)

    def get_start_default_net_command(self) -> str:
        return "sudo virsh net-start default && sudo virsh net-autostart default"

    def get_define_default_net_command(self) -> str:
        return "sudo virsh net-define /usr/share/libvirt/networks/default.xml && sudo virsh net-start default && sudo virsh net-autostart default"
