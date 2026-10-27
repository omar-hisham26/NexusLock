"""
firewall.py - Low-level Windows Firewall rule management via PowerShell
"""
import base64
import os
import re
import subprocess
import time
from typing import List, Optional


def time_now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def run_powershell(command_text: str) -> str:
    """
    Run a PowerShell command using Base64 encoding to avoid any quoting or encoding issues.
    Executes silently without opening a terminal window.
    """
    flags = 0x08000000 if os.name == "nt" else 0
    try:
        encoded_bytes = command_text.encode("utf-16le")
        encoded_str = base64.b64encode(encoded_bytes).decode("ascii")

        result = subprocess.run(
            [
                "powershell.exe",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-EncodedCommand",
                encoded_str,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=35,
            creationflags=flags,
        )
        out = (result.stdout or "").strip()
        err = (result.stderr or "").strip()

        if result.returncode != 0:
            error_details = err if err else out
            if "#< CLIXML" in error_details:
                err_lines = re.findall(r'<S S="Error">(.*?)</S>', error_details, re.DOTALL)
                if err_lines:
                    error_details = "".join(err_lines).replace("_x000D__x000A_", "\n").replace("_x000A_", "\n").strip()
            return f"ERROR: {error_details}"

        return out if out else err
    except Exception as error:
        return f"ERROR: {error}"


def create_block_rule(
    display_name: str,
    group_name: str,
    program_path: str,
    remote_ips: List[str],
) -> bool:
    """
    Create an Outbound Block rule in Windows Firewall for a specific executable and list of IPs.
    """
    if not remote_ips:
        raise ValueError("قائمة العناوين المراد حظرها فارغة!")

    # Format ips array for PowerShell
    formatted_ips = ",".join(f"'{ip.strip()}'" for ip in remote_ips if ip.strip())
    safe_path = os.path.normpath(program_path).replace("'", "''")
    safe_name = display_name.replace("'", "''")
    safe_group = group_name.replace("'", "''")

    script = f"""
$ErrorActionPreference = 'Stop'

try {{
    Get-NetFirewallRule -DisplayName '{safe_name}' -ErrorAction SilentlyContinue | Remove-NetFirewallRule
}} catch {{ }}

try {{
    Get-NetFirewallRule -Group '{safe_group}' -ErrorAction SilentlyContinue | Remove-NetFirewallRule
}} catch {{ }}

$ips = @({formatted_ips})
New-NetFirewallRule `
    -DisplayName '{safe_name}' `
    -Group '{safe_group}' `
    -Direction Outbound `
    -Action Block `
    -Program '{safe_path}' `
    -RemoteAddress $ips `
    -Profile Any `
    -Enabled True | Out-Null
Write-Output "DONE"
"""
    output = run_powershell(script)
    if "DONE" not in output:
        if "CIM resource was not available" in output or "Access is denied" in output or "UnauthorizedAccess" in output:
            raise PermissionError(
                "ويندوز يرفض تعديل جدار الحماية بدون صلاحيات المسؤول!\n"
                "يرجى تشغيل البرنامج كمسؤول (Run as administrator)."
            )
        clean_msg = output.replace("ERROR: ", "").strip()
        raise RuntimeError(f"فشل إنشاء قاعدة جدار الحماية:\n{clean_msg}")
    return True


def remove_block_rules(display_name: Optional[str] = None, group_name: Optional[str] = None) -> bool:
    """Remove specific firewall rules by DisplayName or Group."""
    cmd_parts = []
    if display_name:
        safe_name = display_name.replace("'", "''")
        cmd_parts.append(f"try {{ Get-NetFirewallRule -DisplayName '{safe_name}' -ErrorAction SilentlyContinue | Remove-NetFirewallRule }} catch {{ }}")
    if group_name:
        safe_group = group_name.replace("'", "''")
        cmd_parts.append(f"try {{ Get-NetFirewallRule -Group '{safe_group}' -ErrorAction SilentlyContinue | Remove-NetFirewallRule }} catch {{ }}")

    cmd_parts.append('Write-Output "DONE"')
    script = "\n".join(cmd_parts)
    output = run_powershell(script)
    return "DONE" in output


def is_rule_active(display_name: Optional[str] = None, group_name: Optional[str] = None) -> bool:
    """Check if the firewall rule exists and is active."""
    checks = []
    if display_name:
        safe_name = display_name.replace("'", "''")
        checks.append(f"$r1 = Get-NetFirewallRule -DisplayName '{safe_name}' -ErrorAction SilentlyContinue")
    else:
        checks.append("$r1 = $null")

    if group_name:
        safe_group = group_name.replace("'", "''")
        checks.append(f"$r2 = Get-NetFirewallRule -Group '{safe_group}' -ErrorAction SilentlyContinue")
    else:
        checks.append("$r2 = $null")

    script = f"""
{'\n'.join(checks)}
if ($r1 -or $r2) {{ Write-Output "YES_ACTIVE" }} else {{ Write-Output "NO_INACTIVE" }}
"""
    output = run_powershell(script)
    return "YES_ACTIVE" in output


def clean_all_nexuslock_rules() -> bool:
    """Factory cleanup: remove all NexusLock and legacy NetherWatch/dropship rules across all games."""
    script = """
Get-NetFirewallRule | Where-Object {
    $_.DisplayName -like '*NexusLock*' -or
    $_.Group -like '*NexusLock*' -or
    $_.DisplayName -like '*NetherWatch*' -or
    $_.Group -like '*NetherWatch*' -or
    $_.DisplayName -like '*dropship*' -or
    $_.Group -like '*Dropship*'
} | Remove-NetFirewallRule -ErrorAction SilentlyContinue
Write-Output "CLEANED"
"""
    output = run_powershell(script)
    return "CLEANED" in output


clean_all_netherwatch_rules = clean_all_nexuslock_rules
