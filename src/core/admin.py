"""
admin.py - UAC elevation checks and privilege management for Windows
"""
import ctypes
import os
import sys
from pathlib import Path


def is_admin() -> bool:
    """Check if the current process has Windows Administrator privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def request_admin(work_dir: Path = None):
    """
    Request UAC elevation and relaunch the application if not already running as Admin.
    """
    if os.name != "nt" or is_admin():
        return True

    if work_dir is None:
        work_dir = Path(__file__).resolve().parent.parent.parent

    try:
        if getattr(sys, "frozen", False):
            exe_path = sys.executable
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", exe_path, "", str(work_dir), 1
            )
        else:
            python_exe = sys.executable
            main_script = str(work_dir / "main.py")
            ret = ctypes.windll.shell32.ShellExecuteW(
                None, "runas", python_exe, f'"{main_script}"', str(work_dir), 1
            )

        if int(ret) > 32:
            sys.exit(0)
        else:
            print("[Warning] App launched without full administrator privileges.")
            return False
    except Exception as e:
        print(f"[Warning] Failed to request admin elevation: {e}")
        return False
