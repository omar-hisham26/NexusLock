"""
network.py - Network utilities: ping latency checks, DNS flushing, and SDR sync
"""
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Optional


def measure_ping(target_ip: str, count: int = 2, timeout_ms: int = 1500) -> Optional[int]:
    """
    Ping a target IP address and return average/last latency in milliseconds.
    Returns None if unreachable or timeout.
    """
    if not target_ip:
        return None

    flags = 0x08000000 if os.name == "nt" else 0
    cmd = ["ping", "-n", str(count), "-w", str(timeout_ms), target_ip]
    try:
        res = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=int((count * timeout_ms) / 1000) + 3,
            creationflags=flags,
        )
        found = re.findall(r"(\d+)\s*ms", res.stdout, re.IGNORECASE)
        if found:
            return int(found[-1])
    except Exception:
        pass
    return None


def flush_dns() -> bool:
    """Flush the Windows DNS resolver cache."""
    flags = 0x08000000 if os.name == "nt" else 0
    try:
        res = subprocess.run(
            ["ipconfig", "/flushdns"],
            capture_output=True,
            creationflags=flags,
            timeout=6,
        )
        return res.returncode == 0
    except Exception:
        return False


def refresh_deadlock_sdr(data_file_path: Path) -> bool:
    """
    Attempt to fetch latest SDR clusters from Valve for Deadlock (AppID: 1422450).
    Saves to data_file_path if successful.
    """
    try:
        import urllib.request
        url = "https://api.steampowered.com/ISteamApps/GetSDRConfig/v1?appid=1422450"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 NetherWatch/3.5"})
        with urllib.request.urlopen(req, timeout=10) as response:
            raw = json.loads(response.read().decode("utf-8"))

        pops = raw.get("pops", {})
        if not pops:
            return False

        deadlock_data = {
            "revision": raw.get("revision"),
            "appid": 1422450,
            "default_target": "ams",
            "servers": {},
        }

        for code, info in sorted(pops.items()):
            relays = info.get("relays", [])
            ips = [r["ipv4"] for r in relays if "ipv4" in r]
            if ips:
                deadlock_data["servers"][code] = {
                    "code": code,
                    "title": info.get("desc", code.upper()),
                    "relays": ips,
                    "ping_ip": ips[0],
                }

        data_file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(data_file_path, "w", encoding="utf-8") as f:
            json.dump(deadlock_data, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False
