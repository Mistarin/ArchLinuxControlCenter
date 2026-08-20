"""
Cleanup Service: Generates safe, quoted maintenance and cache wipe commands.
"""

import shlex
from pathlib import Path

class CleanupService:
    def get_clean_dolphin_command(self) -> str:
        return "killall dolphin 2>/dev/null; rm -f ~/.config/dolphinrc ~/.local/share/dolphin/view_properties/global/.directory && echo 'Dolphin configuration and local share cache reset successfully.'"

    def get_clean_pacman_cache_command(self) -> str:
        return "sudo paccache -r -k 2 && (yay -Sc --noconfirm 2>/dev/null || paru -Sc --noconfirm 2>/dev/null || true) && echo 'Package cache cleaned.'"

    def get_clean_flatpak_command(self) -> str:
        return "flatpak uninstall --unused -y"

    def get_vacuum_journal_command(self) -> str:
        return "sudo journalctl --vacuum-size=100M"

    def get_clean_shader_cache_command(self, app_id: str) -> str:
        clean_id = "".join(c for c in app_id if c.isdigit())
        if not clean_id:
            clean_id = "275850"
        steam_base = str(Path.home() / ".local" / "share" / "Steam" / "steamapps" / "shadercache" / clean_id)
        return f"rm -rf {shlex.quote(steam_base)} && echo 'Cleaned Steam shader cache for AppID {clean_id}'"

    def get_open_shader_dir_command(self, app_id: str) -> str:
        clean_id = "".join(c for c in app_id if c.isdigit())
        if not clean_id:
            clean_id = "275850"
        steam_base = str(Path.home() / ".local" / "share" / "Steam" / "steamapps" / "shadercache" / clean_id)
        return f"mkdir -p {shlex.quote(steam_base)} && (dolphin {shlex.quote(steam_base)} 2>/dev/null || xdg-open {shlex.quote(steam_base)}) &"

    def get_easyeffects_language_command(self, locale: str = "en_US") -> str:
        safe_locale = shlex.quote(f"{locale}.UTF-8")
        return f"flatpak override --user com.github.wwmm.easyeffects --env=LC_ALL={safe_locale} --env=LANG={safe_locale} && echo 'EasyEffects locale set to {locale}.'"

    def get_easyeffects_reset_command(self) -> str:
        return "flatpak override --user --reset com.github.wwmm.easyeffects && echo 'EasyEffects language overrides reset to system default.'"
