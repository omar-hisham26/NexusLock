"""
base.py - Base abstract class for supported game profiles in NexusLock
"""
from abc import ABC, abstractmethod
import os
import subprocess
from typing import List, Dict, Any, Optional
from src.core import firewall, admin


class BaseGame(ABC):
    """Abstract base class representing a supported game in NexusLock."""

    game_id: str = "base"
    display_name: str = "Base Game"
    tagline: str = "Game Profile"
    icon_filename: str = "icon.ico"
    rule_name: str = "NexusLock - Base"
    group_name: str = "NexusLock_Base"
    exe_names: List[str] = []
    default_server_code: str = "ams"

    def is_running(self) -> bool:
        """Check if any of the game's executable processes are running."""
        flags = 0x08000000 if os.name == "nt" else 0
        for exe in self.exe_names:
            try:
                res = subprocess.run(
                    ["tasklist", "/FI", f"IMAGENAME eq {exe}", "/FO", "CSV", "/NH"],
                    capture_output=True,
                    text=True,
                    creationflags=flags,
                    timeout=3,
                )
                if exe.lower() in res.stdout.lower():
                    return True
            except Exception:
                pass
        return False

    @abstractmethod
    def find_game_automatically(self) -> str:
        """Scan system drives and processes to locate the game executable."""
        pass

    @abstractmethod
    def resolve_executable_path(self, input_path: str) -> str:
        """Normalize and validate the path, finding the real game binary if folder or launcher was chosen."""
        pass

    @abstractmethod
    def get_servers_list(self) -> List[Dict[str, Any]]:
        """Return standardized list of available servers: [{'code': ..., 'title': ..., 'ping_ip': ...}]"""
        pass

    def get_server_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        """Find a server dict by its token/code."""
        code_lower = (code or "").lower().strip()
        for srv in self.get_servers_list():
            if srv.get("code", "").lower() == code_lower:
                return srv
        servers = self.get_servers_list()
        return servers[0] if servers else None

    @abstractmethod
    def get_blocked_ips(self, target_server_code: Optional[str] = None) -> List[str]:
        """Return the list of IP ranges or addresses to block for all servers except the target server."""
        pass

    def enable_lock(self, game_path: str, target_server_code: Optional[str] = None) -> int:
        """Enable firewall block rule for this game, preserving only the target server."""
        if not game_path:
            raise ValueError(f"مسار اللعبة فارغ! يرجى تحديد مسار ملف {self.display_name} أولاً.")

        resolved = self.resolve_executable_path(game_path)
        if not resolved or not os.path.isfile(resolved):
            raise FileNotFoundError(f"لم يتم العثور على ملف تشغيل اللعبة في المسار:\n{game_path}")

        target_code = target_server_code or self.default_server_code
        blocked_ips = self.get_blocked_ips(target_code)
        if not blocked_ips:
            raise ValueError("قائمة العناوين المراد حظرها فارغة!")

        # Remove previous rule then create new one
        self.disable_lock()
        firewall.create_block_rule(
            display_name=self.rule_name,
            group_name=self.group_name,
            program_path=resolved,
            remote_ips=blocked_ips,
        )
        return len(blocked_ips)

    def disable_lock(self) -> bool:
        """Disable and remove firewall rules for this game."""
        return firewall.remove_block_rules(display_name=self.rule_name, group_name=self.group_name)

    def is_locked(self) -> bool:
        """Check if this game's lock rule is active in Windows Firewall."""
        return firewall.is_rule_active(display_name=self.rule_name, group_name=self.group_name)
