"""
ZRAM & Memory Tuner Service: Safe command builder for systemd zram generator and kernel swappiness.
"""

class ZramService:
    def get_status_command(self) -> str:
        return "zramctl --output-all && echo '' && echo '=== Active Swap Devices ===' && swapon --show"

    def get_generator_config_command(self, size_mb: int, algo: str, prio: int) -> str:
        valid_algos = {"zstd", "lz4", "lzo", "lz4hc"}
        safe_algo = algo if algo in valid_algos else "zstd"
        safe_size = max(512, int(size_mb))
        safe_prio = max(0, min(32767, int(prio)))

        conf_content = f"[zram0]\\nzram-size = {safe_size}\\ncompression-algorithm = {safe_algo}\\nswap-prio = {safe_prio}\\n"
        return f"sudo mkdir -p /etc/systemd/zram-generator.conf.d && echo -e '{conf_content}' | sudo tee /etc/systemd/zram-generator.conf.d/cachy-zram.conf && sudo systemctl restart systemd-zram-setup@zram0.service 2>/dev/null || (sudo zramctl && echo 'ZRAM updated.')"

    def get_swappiness_command(self, swappiness: int, cluster: int) -> str:
        safe_swap = max(0, min(200, int(swappiness)))
        safe_clust = max(0, min(5, int(cluster)))

        sysctl_content = f"vm.swappiness = {safe_swap}\\nvm.page-cluster = {safe_clust}\\n"
        return f"sudo sysctl vm.swappiness={safe_swap} && sudo sysctl vm.page-cluster={safe_clust} && echo -e '{sysctl_content}' | sudo tee /etc/sysctl.d/99-zram.conf && echo 'Swappiness and page-cluster saved to /etc/sysctl.d/99-zram.conf'"

    def get_reset_command(self) -> str:
        return "sudo swapoff /dev/zram0 2>/dev/null; sudo zramctl --reset /dev/zram0 2>/dev/null; sudo swapon /dev/zram0 2>/dev/null; echo 'ZRAM device reset successfully.'"
