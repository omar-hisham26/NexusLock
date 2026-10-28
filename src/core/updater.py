"""
updater.py - Automatic GitHub Releases check and update installer launcher
"""
import json
import os
import re
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
            "User-Agent": f"NexusLock/{current_version}",
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
            assets = data.get("assets", [])
            chosen_asset = None
            for asset in assets:
                name = asset.get("name", "").lower()
                if "setup" in name and name.endswith(".exe"):
                    chosen_asset = asset
                    break
                if name.endswith(".exe"):
                    chosen_asset = asset

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
        pass
    return None


def download_and_install_update(
    download_url: str,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> bool:
    """
    Download the latest installer package and launch it cleanly via Windows Shell.
    """
    try:
        req = urllib.request.Request(
            download_url,
            headers={"User-Agent": f"NexusLock/{config.VERSION}"},
        )

        temp_dir = Path(tempfile.gettempdir())
        installer_path = temp_dir / "NexusLock-Update-Setup.exe"

        with urllib.request.urlopen(req, timeout=30) as response:
            total_size = response.headers.get("Content-Length")
            total_bytes = int(total_size) if total_size and total_size.isdigit() else 0
            downloaded = 0
            chunk_size = 64 * 1024

            with open(installer_path, "wb") as out_file:
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

        if os.name == "nt" and hasattr(os, "startfile"):
            os.startfile(str(installer_path))
            sys.exit(0)
        return False
    except Exception as e:
        print(f"Update failed: {e}")
        return False
