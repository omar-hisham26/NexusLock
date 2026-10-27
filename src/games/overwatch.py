"""
overwatch.py - Overwatch 2 game profile and server routing for NexusLock
"""
import ipaddress
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from src import config
from src.core import firewall
from src.games.base import BaseGame

OVERWATCH_SERVER_LABELS = {
    "ams1": "🇳🇱 نيذرلاند (Netherlands) — أمستردام (ams1)",
    "gmec2": "🇸🇦 الشرق الأوسط — السعودية (gmec2)",
    "gen1": "🇫🇮 فنلندا (Finland) — هلسنكي (gen1)",
    "gue4": "🇺🇸 أمريكا الشرقية (US East) — فرجينيا (gue4)",
    "ord1": "🇺🇸 أمريكا الوسطى (US Central) — شيكاغو (ord1)",
    "las1": "🇺🇸 أمريكا الغربية (US West) — لاس فيغاس (las1)",
    "gsg1": "🇸🇬 سنغافورة (Singapore) — (gsg1)",
    "gtk1": "🇯🇵 اليابان (Japan) — طوكيو (gtk1)",
    "tpe1": "🇹🇼 تايوان (Taiwan) — (tpe1)",
    "syd2": "🇦🇺 أستراليا (Australia) — سيدني (syd2)",
    "gbr1": "🇧🇷 البرازيل (Brazil) — (gbr1)",
}


class OverwatchGame(BaseGame):
    game_id = "overwatch"
    display_name = "Overwatch 2"
    tagline = "Blizzard Entertainment (Battle.net / Steam)"
    icon_filename = "overwatch.png"
    rule_name = "NexusLock - Overwatch 2 (Server Lock)"
    group_name = "NexusLock_OW2"
    exe_names = ["Overwatch.exe"]
    default_server_code = "ams1"

    def __init__(self):
        self._servers_file = self._find_servers_file()

    def _find_servers_file(self) -> Path:
        for candidate in [
            config.DATA_DIR / "overwatch_servers.json",
            config.CURRENT_DIR / "data" / "overwatch_servers.json",
            config.DATA_DIR / "servers.json",
        ]:
            if candidate.exists():
                return candidate
        return config.DATA_DIR / "overwatch_servers.json"

    def get_raw_servers(self) -> List[Dict[str, Any]]:
        if not self._servers_file.exists():
            return []
        try:
            with open(self._servers_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("servers", {}).get("overwatch", [])
        except Exception:
            return []

    def get_servers_list(self) -> List[Dict[str, Any]]:
        raw = self.get_raw_servers()
        results = []
        for srv in raw:
            token = srv.get("token", "")
            title = OVERWATCH_SERVER_LABELS.get(token, srv.get("title", token).title())
            results.append({
                "code": token,
                "title": title,
                "ping_ip": srv.get("ping", ""),
            })
        return results

    def get_blocked_ips(self, target_server_code: Optional[str] = None) -> List[str]:
        target = (target_server_code or self.default_server_code).lower()
        servers = self.get_raw_servers()
        if not servers:
            return []

        v4_nets, v6_nets = [], []
        for srv in servers:
            token = srv.get("token", "").lower()
            title = srv.get("title", "").lower()

            # Skip target destination (do not block the user's chosen server)
            if token == target:
                continue
            if target == "ams1" and "netherlands" in title:
                continue

            raw_blocks = srv.get("block", "").split(",")
            for raw_ip in raw_blocks:
                ip = raw_ip.strip()
                if not ip:
                    continue
                try:
                    net = ipaddress.ip_network(ip, strict=False)
                    if net.version == 4:
                        v4_nets.append(net)
                    else:
                        v6_nets.append(net)
                except ValueError:
                    pass

        collapsed = list(ipaddress.collapse_addresses(v4_nets)) + list(ipaddress.collapse_addresses(v6_nets))
        return [str(net) for net in collapsed]

    def resolve_executable_path(self, input_path: str) -> str:
        if not input_path:
            return ""
        clean_path = os.path.normpath(str(input_path).strip().strip('"').strip("'"))

        if os.path.isdir(clean_path):
            for candidate in [
                os.path.join(clean_path, "_retail_", "Overwatch.exe"),
                os.path.join(clean_path, "Overwatch.exe"),
            ]:
                if os.path.isfile(candidate):
                    return os.path.normpath(candidate)

        if os.path.isfile(clean_path) and not clean_path.lower().endswith(r"\_retail_\overwatch.exe"):
            parent_dir = os.path.dirname(clean_path)
            retail_candidate = os.path.join(parent_dir, "_retail_", "Overwatch.exe")
            if os.path.isfile(retail_candidate):
                return os.path.normpath(retail_candidate)

        return clean_path if os.path.isfile(clean_path) else ""

    def find_game_automatically(self) -> str:
        candidates = [
            r"Program Files (x86)\Overwatch\_retail_\Overwatch.exe",
            r"Program Files\Overwatch\_retail_\Overwatch.exe",
            r"Program Files (x86)\Steam\steamapps\common\Overwatch\_retail_\Overwatch.exe",
            r"Program Files\Steam\steamapps\common\Overwatch\_retail_\Overwatch.exe",
            r"SteamLibrary\steamapps\common\Overwatch\_retail_\Overwatch.exe",
            r"Steam\steamapps\common\Overwatch\_retail_\Overwatch.exe",
            r"Overwatch\_retail_\Overwatch.exe",
            r"Games\Overwatch\_retail_\Overwatch.exe",
            r"Games\SteamLibrary\steamapps\common\Overwatch\_retail_\Overwatch.exe",
        ]
        for drive in ["C", "D", "E", "F", "G", "H"]:
            for rel in candidates:
                full = f"{drive}:\\{rel}"
                if os.path.isfile(full):
                    return os.path.normpath(full)

        out = firewall.run_powershell(
            "$p = Get-Process -Name Overwatch -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Path; if ($p) { $p }"
        )
        if out and os.path.isfile(out.strip()):
            return self.resolve_executable_path(out.strip())

        out = firewall.run_powershell(
            "Get-NetFirewallRule -DisplayName 'Overwatch Application' -ErrorAction SilentlyContinue | "
            "Get-NetFirewallApplicationFilter | Select-Object -First 1 -ExpandProperty Program"
        )
        if out and os.path.isfile(out.strip()):
            return self.resolve_executable_path(out.strip())

        return ""

    def disable_lock(self) -> bool:
        """Clean any NexusLock and legacy NetherWatch/dropship rules for Overwatch."""
        firewall.remove_block_rules(display_name=self.rule_name, group_name=self.group_name)
        legacy_script = """
Get-NetFirewallRule | Where-Object {
    $_.DisplayName -like '*NexusLock*Overwatch*' -or
    $_.Group -eq 'NexusLock_OW2' -or
    $_.DisplayName -like '*NetherWatch*Overwatch*' -or
    $_.DisplayName -eq 'NetherWatch - Netherlands Only' -or
    $_.Group -eq 'NetherWatch_Rules' -or
    $_.Group -eq 'Dropship_Netherlands' -or
    $_.Group -eq 'stormy/dropship/v3'
} | Remove-NetFirewallRule -ErrorAction SilentlyContinue
Write-Output "DONE"
"""
        firewall.run_powershell(legacy_script)
        return True

    def is_locked(self) -> bool:
        script = f"""
$r1 = Get-NetFirewallRule -DisplayName '{self.rule_name}' -ErrorAction SilentlyContinue
$r2 = Get-NetFirewallRule -Group '{self.group_name}' -ErrorAction SilentlyContinue
$r3 = Get-NetFirewallRule | Where-Object {{ $_.DisplayName -like '*NexusLock*Overwatch*' -or $_.DisplayName -like '*NetherWatch*Overwatch*' }}
if ($r1 -or $r2 -or $r3) {{ Write-Output "YES" }} else {{ Write-Output "NO" }}
"""
        out = firewall.run_powershell(script)
        return "YES" in out
