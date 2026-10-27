"""
updater.py - Automatic GitHub Releases check and seamless background updater
"""
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path
from typing import Optional, Callable, Dict, Any, Tuple

from src import config


def parse_version(v_str: str) -> Tuple[int, ...]:
    """Parse version string like 'v4.1.0' into tuple (4, 1, 0) for safe comparison."""
    if not v_str:
        return (0,)
    clean = re.sub(r"[^\d.]", "", str(v_str).strip())
    parts = []
    for p in clean.split("."):
        if p.isdigit():
            parts.append(int(p))
    return tuple(parts) if parts else (0,)


def check_for_update(
    repo: str = config.GITHUB_REPO,
    current_version: str = config.VERSION,
    timeout: int = 4,
) -> Optional[Dict[str, Any]]:
    """
    Query GitHub API for latest release and compare versions.
    Returns release info dict if an update is available, else None.
    """
    api_url = f"https://api.github.com/repos/{repo}/releases/latest"
    req = urllib.request.Request(
        api_url,
        headers={
            "User-Agent": f"NexusLock-Updater/{current_version}",
            "Accept": "application/vnd.github.v3+json",
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status != 200:
                return None
            data = json.loads(response.read().decode("utf-8"))

        remote_tag = data.get("tag_name", "")
        remote_ver = parse_version(remote_tag)
        local_ver = parse_version(current_version)

        if remote_ver > local_ver:
            # Look for executable asset (NexusLock.exe or .exe)
            assets = data.get("assets", [])
            chosen_asset = None
            for asset in assets:
                name = asset.get("name", "").lower()
                if name == "nexuslock.exe":
                    chosen_asset = asset
                    break
                if name.endswith(".exe") and "setup" not in name:
                    chosen_asset = asset

            # Fallback to setup if standalone exe not found
            if not chosen_asset and assets:
                for asset in assets:
                    if asset.get("name", "").lower().endswith(".exe"):
                        chosen_asset = asset
                        break

            if chosen_asset:
                return {
                    "version": remote_tag,
                    "release_name": data.get("name", remote_tag),
                    "download_url": chosen_asset.get("browser_download_url"),
                    "filename": chosen_asset.get("name"),
                    "size": chosen_asset.get("size", 0),
                    "notes": data.get("body", ""),
                }
    except Exception:
        # Silently pass on network timeouts or rate limits so app launches normally
        pass
    return None


def download_and_install_update(
    download_url: str,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> bool:
    """
    Stream download the update, write a self-executing batch script to swap the binary,
    and restart the process.
    """
    try:
        req = urllib.request.Request(
            download_url,
            headers={"User-Agent": f"NexusLock-Updater/{config.VERSION}"},
        )

        # Download to a temporary file
        temp_dir = Path(tempfile.gettempdir())
        new_exe_path = temp_dir / "NexusLock_new.exe"

        with urllib.request.urlopen(req, timeout=30) as response:
            total_size = response.headers.get("Content-Length")
            total_bytes = int(total_size) if total_size and total_size.isdigit() else 0
            downloaded = 0
            chunk_size = 64 * 1024

            with open(new_exe_path, "wb") as out_file:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    out_file.write(chunk)
                    downloaded += len(chunk)
                    if total_bytes > 0 and progress_callback:
                        percent = int((downloaded / total_bytes) * 100)
                        progress_callback(min(percent, 100))

        if progress_callback:
            progress_callback(100)

        # Target executable to replace
        if getattr(sys, "frozen", False):
            target_exe = Path(sys.executable).resolve()
        else:
            target_exe = config.CURRENT_DIR / "NexusLock.exe"

        # Create self-deleting Windows updater batch script
        updater_bat = temp_dir / "nexuslock_updater.bat"
        pid = os.getpid()

        script_content = f"""@echo off
setlocal
:: Wait for old NexusLock process (PID {pid}) to terminate
:WAIT_LOOP
tasklist /FI "PID eq {pid}" 2>NUL | find "{pid}" >NUL
if "%ERRORLEVEL%"=="0" (
    timeout /t 1 /nobreak >nul
    goto WAIT_LOOP
)

:: Replace executable
copy /y "{new_exe_path}" "{target_exe}" >nul
del /f /q "{new_exe_path}" >nul

:: Launch updated app
start "" "{target_exe}"

:: Delete this updater script
(goto) 2>nul & del "%~f0"
"""
        with open(updater_bat, "w", encoding="utf-8") as f:
            f.write(script_content)

        # Launch the batch script silently
        flags = 0x08000000 if os.name == "nt" else 0
        subprocess.Popen(
            ["cmd.exe", "/c", str(updater_bat)],
            creationflags=flags,
            close_fds=True,
        )

        # Exit current application
        sys.exit(0)
    except Exception as e:
        print(f"Update failed: {e}")
        return False
