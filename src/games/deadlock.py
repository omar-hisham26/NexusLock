"""
deadlock.py - Deadlock game profile and Steam Datagram Relay (SDR) routing
"""
import ipaddress
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from src import config
from src.core import firewall
from src.games.base import BaseGame

DEADLOCK_SERVER_LABELS = {
    "ams": "🇳🇱 نيذرلاند (Netherlands) — أمستردام (ams)",
    "fra": "🇩🇪 ألمانيا (Germany) — فرانكفورت (fra)",
    "dxb": "🇦🇪 الشرق الأوسط (Middle East) — دبي (dxb)",
    "dfjr": "🇦🇪 الإمارات — الفجيرة (dfjr)",
    "dfra": "🇩🇪 ألمانيا — فرانكفورت 2 (dfra)",
    "lhr": "🇬🇧 بريطانيا (UK) — لندن (lhr)",
    "dlhr": "🇬🇧 بريطانيا — لندن 2 (dlhr)",
    "par": "🇫🇷 فرنسا (France) — باريس (par)",
    "mad": "🇪🇸 إسبانيا (Spain) — مدريد (mad)",
    "vie": "🇦🇹 النمسا (Austria) — فيينا (vie)",
    "dvie": "🇦🇹 النمسا — فيينا 2 (dvie)",
    "sto": "🇸🇪 السويد (Sweden) — ستوكهولم (sto)",
    "sto2": "🇸🇪 السويد — ستوكهولم 2 (sto2)",
    "waw": "🇵🇱 بولندا (Poland) — وارسو (waw)",
    "hel": "🇫🇮 فنلندا (Finland) — هلسنكي (hel)",
    "iad": "🇺🇸 أمريكا الشرقية (US East) — (iad)",
    "ord": "🇺🇸 أمريكا الوسطى (US Central) — (ord)",
    "atl": "🇺🇸 أمريكا — أتلانتا (atl)",
    "dfw": "🇺🇸 أمريكا — دالاس (dfw)",
    "lax": "🇺🇸 أمريكا الغربية (US West) — (lax)",
    "sea": "🇺🇸 أمريكا — سياتل (sea)",
    "sgp": "🇸🇬 سنغافورة (Singapore) — (sgp)",
    "hkg": "🇭🇰 هونغ كونغ (Hong Kong) — (hkg)",
    "tyo": "🇯🇵 اليابان (Japan) — طوكيو (tyo)",
    "seo": "🇰🇷 كوريا (Korea) — سيول (seo)",
    "bom2": "🇮🇳 الهند — مومباي (bom2)",
    "maa2": "🇮🇳 الهند — تشيناي (maa2)",
    "jnb": "🇿🇦 جنوب أفريقيا (South Africa) — (jnb)",
    "gru": "🇧🇷 البرازيل (Brazil) — (gru)",
    "eze": "🇦🇷 الأرجنتين (Argentina) — (eze)",
    "scl": "🇨🇱 تشيلي (Chile) — (scl)",
    "lim": "🇵🇪 بيرو (Peru) — (lim)",
    "syd": "🇦🇺 أستراليا (Australia) — سيدني (syd)",
    "gum": "🇬🇺 غوام (gum)",
}


class DeadlockGame(BaseGame):
    game_id = "deadlock"
    display_name = "Deadlock"
    tagline = "Valve Corporation (Steam SDR Network)"
    icon_filename = "deadlock.png"
    rule_name = "NexusLock - Deadlock (Server Lock)"
    group_name = "NexusLock_Deadlock"
    exe_names = ["project8.exe", "deadlock.exe"]
    default_server_code = "ams"

    def __init__(self):
        self._servers_file = self._find_servers_file()

    def _find_servers_file(self) -> Path:
        for candidate in [
            config.DATA_DIR / "deadlock_servers.json",
            config.CURRENT_DIR / "data" / "deadlock_servers.json",
        ]:
            if candidate.exists():
                return candidate
        return config.DATA_DIR / "deadlock_servers.json"

    def get_raw_servers_dict(self) -> Dict[str, Any]:
        if not self._servers_file.exists():
            return {}
        try:
            with open(self._servers_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("servers", {})
        except Exception:
            return {}

    def get_servers_list(self) -> List[Dict[str, Any]]:
        raw = self.get_raw_servers_dict()
        results = []
        # Put Netherlands (ams) first, then Germany (fra) and Dubai (dxb)
        priority_order = ["ams", "fra", "dxb", "lhr", "par", "mad", "vie", "sto"]
        added = set()

        for code in priority_order:
            if code in raw:
                info = raw[code]
                results.append({
                    "code": code,
                    "title": DEADLOCK_SERVER_LABELS.get(code, info.get("title", code.upper())),
                    "ping_ip": info.get("ping_ip", ""),
                })
                added.add(code)

        for code, info in sorted(raw.items()):
            if code not in added:
                title = DEADLOCK_SERVER_LABELS.get(code, info.get("title", code.upper()))
                results.append({
                    "code": code,
                    "title": title,
                    "ping_ip": info.get("ping_ip", ""),
                })
        return results

    def get_blocked_ips(self, target_server_code: Optional[str] = None) -> List[str]:
        target = (target_server_code or self.default_server_code).lower()
        servers = self.get_raw_servers_dict()
        if not servers:
            return []

        v4_nets = []
        for code, info in servers.items():
            if code.lower() == target:
                continue  # Do not block target destination

            relays = info.get("relays", [])
            for ip_str in relays:
                ip_str = ip_str.strip()
                if not ip_str:
                    continue
                try:
                    net = ipaddress.ip_network(ip_str, strict=False)
                    v4_nets.append(net)
                except ValueError:
                    pass

        collapsed = list(ipaddress.collapse_addresses(v4_nets))
        return [str(net) for net in collapsed]

    def resolve_executable_path(self, input_path: str) -> str:
        if not input_path:
            return ""
        clean_path = os.path.normpath(str(input_path).strip().strip('"').strip("'"))

        if os.path.isdir(clean_path):
            candidates = [
                os.path.join(clean_path, "game", "bin", "win64", "project8.exe"),
                os.path.join(clean_path, "bin", "win64", "project8.exe"),
                os.path.join(clean_path, "deadlock.exe"),
                os.path.join(clean_path, "project8.exe"),
            ]
            for cand in candidates:
                if os.path.isfile(cand):
                    return os.path.normpath(cand)

        if os.path.isfile(clean_path):
            base_name = os.path.basename(clean_path).lower()
            if base_name == "deadlock.exe":
                game_dir = os.path.dirname(clean_path)
                p8_candidate = os.path.join(game_dir, "game", "bin", "win64", "project8.exe")
                if os.path.isfile(p8_candidate):
                    return os.path.normpath(p8_candidate)
            return clean_path

        return ""

    def find_game_automatically(self) -> str:
        candidates = [
            r"Program Files (x86)\Steam\steamapps\common\Deadlock\game\bin\win64\project8.exe",
            r"Program Files\Steam\steamapps\common\Deadlock\game\bin\win64\project8.exe",
            r"SteamLibrary\steamapps\common\Deadlock\game\bin\win64\project8.exe",
            r"Steam\steamapps\common\Deadlock\game\bin\win64\project8.exe",
            r"Games\Deadlock\game\bin\win64\project8.exe",
            r"Games\SteamLibrary\steamapps\common\Deadlock\game\bin\win64\project8.exe",
            r"SteamLibrary\steamapps\common\Deadlock\deadlock.exe",
            r"Steam\steamapps\common\Deadlock\deadlock.exe",
        ]
        for drive in ["C", "D", "E", "F", "G", "H"]:
            for rel in candidates:
                full = f"{drive}:\\{rel}"
                if os.path.isfile(full):
                    return self.resolve_executable_path(full)

        out = firewall.run_powershell(
            "$p = Get-Process -Name project8, deadlock -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Path; if ($p) { $p }"
        )
        if out and os.path.isfile(out.strip()):
            return self.resolve_executable_path(out.strip())

        return ""
