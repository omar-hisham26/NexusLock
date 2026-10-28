"""
firewall.py - Native Windows Firewall rule management via official netsh advfirewall CLI
Uses standard netsh.exe instead of obfuscated PowerShell to avoid antivirus false-positives and improve speed.
"""
import os
import subprocess
import time
from typing import List, Optional, Tuple
from src import i18n

LEGACY_RULE_NAMES = [
    "NexusLock - Overwatch 2 (Server Lock)",
    "NexusLock - Deadlock (Server Lock)",
    "NetherWatch - Overwatch 2 (Netherlands Only)",
    "NetherWatch - Deadlock (Netherlands Only)",
    "NetherWatch - Netherlands Only",
]


def time_now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def run_netsh(args: List[str]) -> Tuple[int, str]:
    """
    Execute netsh.exe advfirewall commands silently without opening a console window.
    Returns (returncode, combined_output).
    """
    flags = 0x08000000 if os.name == "nt" else 0
    cmd = ["netsh", "advfirewall", "firewall"] + args
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            creationflags=flags,
        )
        out = ((result.stdout or "") + "\n" + (result.stderr or "")).strip()
        return result.returncode, out
    except Exception as error:
        return 1, str(error)


def create_block_rule(
    display_name: str,
    group_name: str,
    program_path: str,
    remote_ips: List[str],
) -> bool:
    """
    Create an Outbound Block rule in Windows Firewall for a specific executable and list of IPs.
    Splits into chunks automatically if the IP list is very large.
    """
    clean_ips = [ip.strip() for ip in remote_ips if ip.strip()]
    if not clean_ips:
        raise ValueError(i18n.t("err_empty_ips"))

    norm_path = os.path.normpath(program_path)

    # First remove any existing rules with this name
    remove_block_rules(display_name=display_name, group_name=group_name)

    # Split into chunks of 200 IPs max per rule so command line length is always small
    chunk_size = 200
    for idx in range(0, len(clean_ips), chunk_size):
        chunk = clean_ips[idx : idx + chunk_size]
        ips_arg = ",".join(chunk)
        code, output = run_netsh(
            [
                "add",
                "rule",
                f"name={display_name}",
                "dir=out",
                "action=block",
                f"program={norm_path}",
                f"remoteip={ips_arg}",
                "profile=any",
                "enable=yes",
            ]
        )
        if code != 0:
            low_out = output.lower()
            if "elevation" in low_out or "admin" in low_out or "access is denied" in low_out:
                raise PermissionError(i18n.t("err_admin_required"))
            raise RuntimeError(i18n.t("err_firewall_failed", msg=output))

    return True


def remove_block_rules(display_name: Optional[str] = None, group_name: Optional[str] = None) -> bool:
    """Remove specific firewall rules by rule name."""
    if display_name:
        run_netsh(["delete", "rule", f"name={display_name}"])
    return True


def is_rule_active(display_name: Optional[str] = None, group_name: Optional[str] = None) -> bool:
    """Check if the firewall rule exists and is active using netsh."""
    if not display_name:
        return False
    code, _ = run_netsh(["show", "rule", f"name={display_name}"])
    return code == 0


def clean_all_nexuslock_rules() -> bool:
    """Factory cleanup: remove all NexusLock and legacy NetherWatch rules across all games."""
    for r_name in LEGACY_RULE_NAMES:
        run_netsh(["delete", "rule", f"name={r_name}"])
    return True


clean_all_netherwatch_rules = clean_all_nexuslock_rules
