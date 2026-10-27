"""
config.py - Centralized configuration and settings management for NexusLock
Supports multi-game profiles (Overwatch 2, Deadlock, and future games)
"""
import json
import os
import sys
from pathlib import Path

# Application branding
APP_NAME = "NexusLock"
APP_TITLE = "NexusLock — تبليك سيرفرات الألعاب"
VERSION = "1.0.0"
GITHUB_REPO = "omar-hisham26/NexusLock"

# Runtime directories
if getattr(sys, "frozen", False):
    CURRENT_DIR = Path(sys.executable).resolve().parent
    BUNDLE_DIR = Path(getattr(sys, "_MEIPASS", CURRENT_DIR))
else:
    CURRENT_DIR = Path(__file__).resolve().parent.parent
    BUNDLE_DIR = CURRENT_DIR

# Asset and Data directories
DATA_DIR = CURRENT_DIR / "data"
if not DATA_DIR.exists() and (BUNDLE_DIR / "data").exists():
    DATA_DIR = BUNDLE_DIR / "data"

ASSETS_DIR = CURRENT_DIR / "assets"
if not ASSETS_DIR.exists() and (BUNDLE_DIR / "assets").exists():
    ASSETS_DIR = BUNDLE_DIR / "assets"


def get_settings_file_path() -> Path:
    """
    Get user settings path in %APPDATA%/NexusLock/settings.json
    Fallback to local data/settings.json if APPDATA is unavailable.
    """
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / APP_NAME / "settings.json"
    return DATA_DIR / "settings.json"


SETTINGS_FILE = get_settings_file_path()

# Default initial configuration
DEFAULT_CONFIG = {
    "selected_view": "overwatch",  # "catalog" or game_id
    "unblock_on_close": False,
    "games": {
        "overwatch": {
            "game_path": "",
            "target_server": "ams1",
        },
        "deadlock": {
            "game_path": "",
            "target_server": "ams",
        },
    },
}


def load_settings() -> dict:
    """Load settings with backward compatibility for older NetherWatch configs."""
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))

    # Look in NexusLock APPDATA, legacy NetherWatch APPDATA, then local data/
    appdata = os.environ.get("APPDATA")
    paths_to_check = [
        SETTINGS_FILE,
        Path(appdata) / "NetherWatch" / "settings.json" if appdata else None,
        DATA_DIR / "settings.json",
    ]

    for path in paths_to_check:
        if path and path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                if isinstance(saved, dict):
                    # Handle legacy single-game format
                    if "game_path" in saved and "games" not in saved:
                        legacy_path = saved.get("game_path", "")
                        cfg["games"]["overwatch"]["game_path"] = legacy_path
                        if "unblock_on_close" in saved:
                            cfg["unblock_on_close"] = bool(saved["unblock_on_close"])
                    else:
                        if "selected_view" in saved:
                            cfg["selected_view"] = saved["selected_view"]
                        elif "selected_game" in saved:
                            cfg["selected_view"] = saved["selected_game"]

                        if "unblock_on_close" in saved:
                            cfg["unblock_on_close"] = bool(saved["unblock_on_close"])

                        if "games" in saved and isinstance(saved["games"], dict):
                            for g_id, g_data in saved["games"].items():
                                if g_id in cfg["games"]:
                                    cfg["games"][g_id].update(g_data)
                                else:
                                    cfg["games"][g_id] = g_data
                break
            except Exception:
                pass
    return cfg


def save_settings(data: dict) -> bool:
    """Save user settings safely to APPDATA and locally for portable mode."""
    try:
        target = get_settings_file_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        try:
            local_target = DATA_DIR / "settings.json"
            local_target.parent.mkdir(parents=True, exist_ok=True)
            with open(local_target, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass
        return True
    except Exception as e:
        print(f"[Warning] Failed to save settings: {e}")
        return False
