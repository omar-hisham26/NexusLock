"""
firewall.py - Windows Firewall management and ping checks for Overwatch
App Name: NetherWatch (Netherlands server lock tool)
"""
import base64
import ctypes
import ipaddress
import json
import os
import re
import subprocess
import sys
from pathlib import Path

# -------------------------------------------------------------
# App settings and constants (NetherWatch)
# -------------------------------------------------------------
APP_NAME = "NetherWatch"
RULE_NAME = "NetherWatch - Netherlands Only"
FIREWALL_GROUP = "NetherWatch_Rules"
GAME_EXE_NAME = "Overwatch.exe"
NETHERLANDS_SERVER_IP = "137.221.78.60"  # Target server IP used for ping tests

# Paths
if getattr(sys, "frozen", False):
    CURRENT_DIR = Path(sys.executable).resolve().parent
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", CURRENT_DIR))
else:
    # In development mode, project root is the parent of src/
    CURRENT_DIR = Path(__file__).resolve().parent.parent
    BUNDLE_DIR = CURRENT_DIR

# Look for servers.json in executable directory first, then bundle directory
SERVERS_FILE = CURRENT_DIR / "data" / "servers.json"
if not SERVERS_FILE.exists() and (BUNDLE_DIR / "data" / "servers.json").exists():
    SERVERS_FILE = BUNDLE_DIR / "data" / "servers.json"


def get_settings_file():
    """
    Get the settings file path.
    Prefers %APPDATA%/NetherWatch/settings.json so settings persist reliably
    even when installed in Program Files, with a local fallback.
    """
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / APP_NAME / "settings.json"
    return CURRENT_DIR / "data" / "settings.json"


SETTINGS_FILE = get_settings_file()


# -------------------------------------------------------------
# 1. Administrator privileges check
# -------------------------------------------------------------
def is_admin():
    """Check if the app is currently running as Administrator in Windows"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def request_admin():
    """Request UAC administrator permission and relaunch if needed"""
    if os.name == "nt" and not is_admin():
        work_dir = str(CURRENT_DIR)
        try:
            if getattr(sys, "frozen", False):
                # When running as compiled executable (.exe)
                exe_path = sys.executable
                ret = ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", exe_path, "", work_dir, 1
                )
            else:
                # When running as Python script
                python_exe = sys.executable
                main_script = str(CURRENT_DIR / "main.py")
                ret = ctypes.windll.shell32.ShellExecuteW(
                    None, "runas", python_exe, f'"{main_script}"', work_dir, 1
                )
            # In Windows, values greater than 32 mean the elevated process started successfully
            if int(ret) > 32:
                sys.exit(0)
            else:
                print("[تنبيه] تم تشغيل التطبيق بدون صلاحيات المسؤول الكاملة.")
        except Exception as e:
            print(f"[تحذير] تعذر طلب صلاحيات المسؤول: {e}")


# -------------------------------------------------------------
# 2. Run PowerShell commands silently without console popups
# -------------------------------------------------------------
def run_powershell(command_text):
    """Run a PowerShell command using Base64 encoding to avoid any character encoding or long string issues"""
    flags = 0x08000000 if os.name == "nt" else 0
    try:
        # Encode command as UTF-16LE and Base64 (standard for PowerShell -EncodedCommand)
        encoded_bytes = command_text.encode("utf-16le")
        encoded_str = base64.b64encode(encoded_bytes).decode("ascii")

        result = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded_str],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
            creationflags=flags,
        )
        out = (result.stdout or "").strip()
        err = (result.stderr or "").strip()

        # Log error to file if command failed
        if result.returncode != 0:
            error_details = err if err else out
            if "#< CLIXML" in error_details:
                # Extract clean error messages from CLIXML
                err_lines = re.findall(r'<S S="Error">(.*?)</S>', error_details, re.DOTALL)
                if err_lines:
                    error_details = "".join(err_lines).replace("_x000D__x000A_", "\n").replace("_x000D_", "\r").replace("_x000A_", "\n").strip()
            try:
                with open(CURRENT_DIR / "error.log", "a", encoding="utf-8") as f:
                    f.write(f"\n[PowerShell Error {time_now()}]\nCommand: {command_text[:120]}...\nError: {error_details}\n")
            except Exception:
                pass
            return f"ERROR: {error_details}"

        return out if out else err
    except Exception as error:
        return f"ERROR: {error}"


def time_now():
    import time
    return time.strftime("%Y-%m-%d %H:%M:%S")


# -------------------------------------------------------------
# 3. Read servers and extract IP ranges to block
# -------------------------------------------------------------
def get_blocked_ips_list():
    """
    Read servers.json and extract IP ranges of all servers except Netherlands (ams1),
    collapsing overlapping subnets to optimize Windows Firewall performance
    """
    if not SERVERS_FILE.exists():
        return []

    with open(SERVERS_FILE, "r", encoding="utf-8") as file:
        data = json.load(file)

    server_list = data.get("servers", {}).get("overwatch", [])
    v4_nets, v6_nets = [], []

    for server in server_list:
        token = server.get("token", "")
        title = server.get("title", "").lower()

        # Skip Netherlands server because this is our desired destination
        if token == "ams1" or "netherlands" in title:
            continue

        # Collect IP ranges for all other servers
        raw_ips = server.get("block", "").split(",")
        for ip in raw_ips:
            ip = ip.strip()
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

    # Collapse IP ranges to minimize number of firewall rules
    collapsed = list(ipaddress.collapse_addresses(v4_nets)) + list(ipaddress.collapse_addresses(v6_nets))
    return [str(net) for net in collapsed]


# -------------------------------------------------------------
# 4. Windows Firewall rule management
# -------------------------------------------------------------
def enable_netherlands_lock(game_path):
    """
    Block all other servers in Windows Firewall for Overwatch.exe so the game only routes to Netherlands
    """
    if not game_path:
        raise ValueError("مسار اللعبة فارغ، يرجى تحديد مسار Overwatch.exe أولاً.")

    # Clean and normalize path: strip quotes, whitespace, and convert forward slashes to backslashes
    clean_path = os.path.normpath(str(game_path).strip().strip('"').strip("'"))

    # If the user selected the game folder instead of Overwatch.exe, search inside it
    if os.path.isdir(clean_path):
        for candidate in [
            os.path.join(clean_path, "_retail_", GAME_EXE_NAME),
            os.path.join(clean_path, GAME_EXE_NAME),
        ]:
            if os.path.isfile(candidate):
                clean_path = candidate
                break

    # If the user selected the root launcher (e.g. Steam Overwatch.exe), automatically redirect to _retail_\Overwatch.exe
    if os.path.isfile(clean_path) and not clean_path.lower().endswith(r"\_retail_\overwatch.exe"):
        parent_dir = os.path.dirname(clean_path)
        retail_candidate = os.path.join(parent_dir, "_retail_", GAME_EXE_NAME)
        if os.path.isfile(retail_candidate):
            clean_path = retail_candidate

    if not os.path.isfile(clean_path):
        raise FileNotFoundError(f"لم يتم العثور على ملف تشغيل اللعبة ({GAME_EXE_NAME}) في المسار:\n{clean_path}")

    # Remove any existing rules first
    disable_netherlands_lock()

    # Get the list of IPs to block
    blocked_ips = get_blocked_ips_list()
    if not blocked_ips:
        raise ValueError("قائمة الآيبيات فارغة، تأكد من وجود ملف data/servers.json")

    ips_formatted = ",".join(f"'{ip}'" for ip in blocked_ips)
    safe_path = clean_path.replace("'", "''")

    script = f"""
$ErrorActionPreference = 'Stop'

try {{
    Get-NetFirewallRule -DisplayName '{RULE_NAME}' -ErrorAction SilentlyContinue | Remove-NetFirewallRule
}} catch {{ }}

try {{
    Get-NetFirewallRule -Group '{FIREWALL_GROUP}' -ErrorAction SilentlyContinue | Remove-NetFirewallRule
}} catch {{ }}

$ips = @({ips_formatted})
New-NetFirewallRule `
    -DisplayName '{RULE_NAME}' `
    -Group '{FIREWALL_GROUP}' `
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
                "نظام ويندوز يرفض تعديل جدار الحماية بدون صلاحيات المسؤول!\n\n"
                "الحل:\n"
                "1. أغلق البرنامج.\n"
                "2. اضغط كليك يمين على NetherWatch.exe واختر:\n"
                "   'تشغيل كمسؤول' (Run as administrator).\n"
                "3. وافق على رسالة ويندوز ثم أعد التفعيل."
            )
        clean_msg = output.replace("ERROR: ", "").strip()
        raise RuntimeError(f"فشل إضافة قاعدة الحظر في جدار الحماية:\n{clean_msg}")
    return len(blocked_ips)


def disable_netherlands_lock():
    """Remove firewall block rules and allow connections to all servers worldwide"""
    script = f"""
try {{ Get-NetFirewallRule -DisplayName '{RULE_NAME}' -ErrorAction SilentlyContinue | Remove-NetFirewallRule }} catch {{ }}
try {{ Get-NetFirewallRule -Group '{FIREWALL_GROUP}' -ErrorAction SilentlyContinue | Remove-NetFirewallRule }} catch {{ }}
try {{ Get-NetFirewallRule -Group 'Dropship_Netherlands' -ErrorAction SilentlyContinue | Remove-NetFirewallRule }} catch {{ }}
try {{ Get-NetFirewallRule -Group 'stormy/dropship/v3' -ErrorAction SilentlyContinue | Remove-NetFirewallRule }} catch {{ }}
try {{ Get-NetFirewallRule | Where-Object {{ $_.DisplayName -like '*NetherWatch*' -or $_.DisplayName -like '*dropship*' }} | Remove-NetFirewallRule -ErrorAction SilentlyContinue }} catch {{ }}
Write-Output "DONE"
"""
    output = run_powershell(script)
    return "DONE" in output


def is_lock_active():
    """Check if the blocking rule is currently active in Windows Firewall"""
    script = f"""
$r1 = Get-NetFirewallRule -DisplayName '{RULE_NAME}' -ErrorAction SilentlyContinue
$r2 = Get-NetFirewallRule -Group '{FIREWALL_GROUP}' -ErrorAction SilentlyContinue
$r3 = Get-NetFirewallRule -Group 'Dropship_Netherlands' -ErrorAction SilentlyContinue
$r4 = Get-NetFirewallRule -Group 'stormy/dropship/v3' -ErrorAction SilentlyContinue
if ($r1 -or $r2 -or $r3 -or $r4) {{ Write-Output "YES_LOCKED" }} else {{ Write-Output "NO_OPEN" }}
"""
    output = run_powershell(script)
    return "YES_LOCKED" in output


def flush_dns():
    """Flush Windows DNS resolver cache"""
    flags = 0x08000000 if os.name == "nt" else 0
    try:
        res = subprocess.run(["ipconfig", "/flushdns"], capture_output=True, creationflags=flags, timeout=6)
        return res.returncode == 0
    except Exception:
        return False


def reset_everything_to_default():
    """
    Factory reset:
    1. Remove all NetherWatch and legacy firewall rules
    2. Flush Windows DNS cache
    3. Delete settings file
    """
    clean_script = f"""
Remove-NetFirewallRule -Group '{FIREWALL_GROUP}' -ErrorAction SilentlyContinue
Remove-NetFirewallRule -DisplayName '{RULE_NAME}' -ErrorAction SilentlyContinue
Remove-NetFirewallRule -Group 'Dropship_Netherlands' -ErrorAction SilentlyContinue
Remove-NetFirewallRule -Group 'stormy/dropship/v3' -ErrorAction SilentlyContinue
Get-NetFirewallRule | Where-Object {{ $_.DisplayName -like '*NetherWatch*' -or $_.DisplayName -like '*dropship*' }} | Remove-NetFirewallRule -ErrorAction SilentlyContinue
Write-Output "CLEANED"
"""
    run_powershell(clean_script)
    flush_dns()

    for s_file in (get_settings_file(), CURRENT_DIR / "data" / "settings.json"):
        if s_file.exists():
            try:
                s_file.unlink()
            except Exception:
                pass

    return True


# -------------------------------------------------------------
# 5. Ping tests and game process detection
# -------------------------------------------------------------
def check_netherlands_ping():
    """Ping Netherlands server (ams1) and return latency in milliseconds (ms)"""
    flags = 0x08000000 if os.name == "nt" else 0
    cmd = ["ping", "-n", "2", "-w", "1500", NETHERLANDS_SERVER_IP]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=6, creationflags=flags)
        found = re.findall(r"(\d+)\s*ms", res.stdout, re.IGNORECASE)
        if found:
            return int(found[-1])
    except Exception:
        pass
    return None


def is_overwatch_running():
    """Check if Overwatch process is currently running on the system"""
    flags = 0x08000000 if os.name == "nt" else 0
    try:
        res = subprocess.run(
            ["tasklist", "/FI", f"IMAGENAME eq {GAME_EXE_NAME}", "/FO", "CSV", "/NH"],
            capture_output=True,
            text=True,
            creationflags=flags,
            timeout=4,
        )
        return GAME_EXE_NAME.lower() in res.stdout.lower()
    except Exception:
        return False


def find_game_automatically():
    """Search for Overwatch.exe in common installation paths (Battle.net and Steam across all drives)"""
    candidate_subpaths = [
        r"Program Files (x86)\Overwatch\_retail_\Overwatch.exe",
        r"Program Files\Overwatch\_retail_\Overwatch.exe",
        r"Program Files (x86)\Steam\steamapps\common\Overwatch\_retail_\Overwatch.exe",
        r"Program Files\Steam\steamapps\common\Overwatch\_retail_\Overwatch.exe",
        r"SteamLibrary\steamapps\common\Overwatch\_retail_\Overwatch.exe",
        r"Steam\steamapps\common\Overwatch\_retail_\Overwatch.exe",
        r"Overwatch\_retail_\Overwatch.exe",
        r"Games\Overwatch\_retail_\Overwatch.exe",
        r"Games\SteamLibrary\steamapps\common\Overwatch\_retail_\Overwatch.exe",
        # Fallback to root launcher (which will be redirected to _retail_)
        r"SteamLibrary\steamapps\common\Overwatch\Overwatch.exe",
        r"Steam\steamapps\common\Overwatch\Overwatch.exe",
    ]
    drives = ["C", "D", "E", "F", "G", "H"]
    for d in drives:
        for sub in candidate_subpaths:
            full = f"{d}:\\{sub}"
            if os.path.exists(full):
                if not full.lower().endswith(r"\_retail_\overwatch.exe"):
                    retail = os.path.join(os.path.dirname(full), "_retail_", GAME_EXE_NAME)
                    if os.path.isfile(retail):
                        return os.path.normpath(retail)
                return os.path.normpath(full)

    # If the game is already running, get its executable path directly
    out = run_powershell(
        "$p = Get-Process -Name Overwatch -ErrorAction SilentlyContinue | Select-Object -First 1 -ExpandProperty Path; if ($p) { $p }"
    )
    if out and os.path.exists(out):
        return os.path.normpath(out.strip())

    # Check path registered in Windows Firewall by Blizzard
    out = run_powershell(
        "Get-NetFirewallRule -DisplayName 'Overwatch Application' -ErrorAction SilentlyContinue | "
        "Get-NetFirewallApplicationFilter | Select-Object -First 1 -ExpandProperty Program"
    )
    if out and os.path.exists(out) and Path(out).name.lower() == GAME_EXE_NAME.lower():
        return os.path.normpath(out.strip())

    return ""


# -------------------------------------------------------------
# 6. User settings persistence
# -------------------------------------------------------------
def load_saved_settings():
    """Load saved settings from %APPDATA% or local data/settings.json"""
    primary = get_settings_file()
    fallback = CURRENT_DIR / "data" / "settings.json"

    file_to_load = None
    if primary.exists():
        file_to_load = primary
    elif fallback.exists():
        file_to_load = fallback

    if file_to_load:
        try:
            with open(file_to_load, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "game_path" in data and data["game_path"]:
                    data["game_path"] = os.path.normpath(str(data["game_path"]).strip().strip('"').strip("'"))
                return data
        except Exception:
            pass
    return {"game_path": "", "unblock_on_close": False}


def save_settings(data):
    """Save user settings to APPDATA and locally if possible"""
    try:
        if "game_path" in data and data["game_path"]:
            data["game_path"] = os.path.normpath(str(data["game_path"]).strip().strip('"').strip("'"))

        # 1. Save to APPDATA (primary, permanent, user-writable)
        target = get_settings_file()
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # 2. Also save to local data/ folder if writable (for portable mode)
        local_target = CURRENT_DIR / "data" / "settings.json"
        try:
            local_target.parent.mkdir(parents=True, exist_ok=True)
            with open(local_target, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
        return True
    except Exception as e:
        print(f"[Warning] Failed to save settings: {e}")
        return False
