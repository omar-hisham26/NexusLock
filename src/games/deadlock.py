"""
deadlock.py - Deadlock game profile and Steam Datagram Relay (SDR) routing
"""
import ipaddress
import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional

from src import config, i18n
from src.core import firewall
from src.games.base import BaseGame

DEADLOCK_SERVER_LABELS = {
    "ar": {
        "ams": "🇳🇱 هولندا — أمستردام",
        "fra": "🇩🇪 ألمانيا — فرانكفورت 1",
        "dxb": "🇦🇪 الشرق الأوسط — دبي",
        "dfjr": "🇦🇪 الإمارات — الفجيرة",
        "dfra": "🇩🇪 ألمانيا — فرانكفورت 2",
        "lhr": "🇬🇧 بريطانيا — لندن 1",
        "dlhr": "🇬🇧 بريطانيا — لندن 2",
        "par": "🇫🇷 فرنسا — باريس",
        "mad": "🇪🇸 إسبانيا — مدريد",
        "vie": "🇦🇹 النمسا — فيينا 1",
        "dvie": "🇦🇹 النمسا — فيينا 2",
        "sto": "🇸🇪 السويد — ستوكهولم 1",
        "sto2": "🇸🇪 السويد — ستوكهولم 2",
        "waw": "🇵🇱 بولندا — وارسو",
        "hel": "🇫🇮 فنلندا — هلسنكي",
        "iad": "🇺🇸 أمريكا الشرقية — فرجينيا",
        "ord": "🇺🇸 أمريكا الوسطى — شيكاغو",
        "atl": "🇺🇸 أمريكا الجنوبية — أتلانتا",
        "dfw": "🇺🇸 أمريكا الوسطى — دالاس",
        "lax": "🇺🇸 أمريكا الغربية — لوس أنجلوس",
        "sea": "🇺🇸 أمريكا الشمالية — سياتل",
        "sgp": "🇸🇬 سنغافورة",
        "hkg": "🇭🇰 هونغ كونغ",
        "tyo": "🇯🇵 اليابان — طوكيو",
        "seo": "🇰🇷 كوريا الجنوبية — سيول",
        "bom2": "🇮🇳 الهند — مومباي",
        "maa2": "🇮🇳 الهند — تشيناي",
        "jnb": "🇿🇦 جنوب أفريقيا — جوهانسبرغ",
        "gru": "🇧🇷 البرازيل — ساو باولو",
        "eze": "🇦🇷 الأرجنتين — بوينس آيرس",
        "scl": "🇨🇱 تشيلي — سانتياغو",
        "lim": "🇵🇪 بيرو — ليما",
        "syd": "🇦🇺 أستراليا — سيدني",
        "gum": "🇬🇺 غوام",
    },
    "en": {
        "ams": "🇳🇱 Netherlands — Amsterdam (ams)",
        "fra": "🇩🇪 Germany — Frankfurt (fra)",
        "dxb": "🇦🇪 Middle East — Dubai (dxb)",
        "dfjr": "🇦🇪 UAE — Fujairah (dfjr)",
        "dfra": "🇩🇪 Germany — Frankfurt 2 (dfra)",
        "lhr": "🇬🇧 United Kingdom — London (lhr)",
        "dlhr": "🇬🇧 United Kingdom — London 2 (dlhr)",
        "par": "🇫🇷 France — Paris (par)",
        "mad": "🇪🇸 Spain — Madrid (mad)",
        "vie": "🇦🇹 Austria — Vienna (vie)",
        "dvie": "🇦🇹 Austria — Vienna 2 (dvie)",
        "sto": "🇸🇪 Sweden — Stockholm (sto)",
        "sto2": "🇸🇪 Sweden — Stockholm 2 (sto2)",
        "waw": "🇵🇱 Poland — Warsaw (waw)",
        "hel": "🇫🇮 Finland — Helsinki (hel)",
        "iad": "🇺🇸 US East — Virginia (iad)",
        "ord": "🇺🇸 US Central — Chicago (ord)",
        "atl": "🇺🇸 US South — Atlanta (atl)",
        "dfw": "🇺🇸 US Central — Dallas (dfw)",
        "lax": "🇺🇸 US West — Los Angeles (lax)",
        "sea": "🇺🇸 US Northwest — Seattle (sea)",
        "sgp": "🇸🇬 Singapore — (sgp)",
        "hkg": "🇭🇰 Hong Kong — (hkg)",
        "tyo": "🇯🇵 Japan — Tokyo (tyo)",
        "seo": "🇰🇷 South Korea — Seoul (seo)",
        "bom2": "🇮🇳 India — Mumbai (bom2)",
        "maa2": "🇮🇳 India — Chennai (maa2)",
        "jnb": "🇿🇦 South Africa — Johannesburg (jnb)",
        "gru": "🇧🇷 Brazil — Sao Paulo (gru)",
        "eze": "🇦🇷 Argentina — Buenos Aires (eze)",
        "scl": "🇨🇱 Chile — Santiago (scl)",
        "lim": "🇵🇪 Peru — Lima (lim)",
        "syd": "🇦🇺 Australia — Sydney (syd)",
        "gum": "🇬🇺 Guam — (gum)",
    },
}


class DeadlockGame(BaseGame):
    game_id = "deadlock"
    display_name = "Deadlock"
    display_name_ar = "ديدلوك"
    tagline = "Valve Corporation (Steam SDR Network)"
    tagline_ar = "شركة فالف — شبكة ستيم"
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
        lang = i18n.get_lang()
        labels = DEADLOCK_SERVER_LABELS.get(lang, DEADLOCK_SERVER_LABELS["ar"])
        results = []
        # Put Netherlands (ams) first, then Germany (fra) and Dubai (dxb)
        priority_order = ["ams", "fra", "dxb", "lhr", "par", "mad", "vie", "sto"]
        added = set()

        for code in priority_order:
            if code in raw:
                info = raw[code]
                results.append({
                    "code": code,
                    "title": labels.get(code, info.get("title", code.upper())),
                    "ping_ip": info.get("ping_ip", ""),
                })
                added.add(code)

        for code, info in sorted(raw.items()):
            if code not in added:
                title = labels.get(code, info.get("title", code.upper()))
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

        if os.name == "nt":
            try:
                import winreg
                with winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Steam App 1422450",
                ) as key:
                    install_loc, _ = winreg.QueryValueEx(key, "InstallLocation")
                    if install_loc:
                        resolved = self.resolve_executable_path(install_loc)
                        if resolved:
                            return resolved
            except Exception:
                pass

        return ""
