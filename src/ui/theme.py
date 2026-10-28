"""
theme.py - Modern Cyber-Gaming visual theme, CustomTkinter styling, Pillow LANCZOS icons, and Windows 11 DWM integration
"""
import ctypes
import os
from pathlib import Path
from typing import Optional, Tuple
import customtkinter as ctk
from PIL import Image

# Initialize CustomTkinter appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Visual color palette (Modern Cyber Obsidian - ExitLag / Discord inspired)
BG_APP = "#080b12"           # Deepest obsidian main background
BG_SIDEBAR = "#0c101a"       # Left sidebar surface
BG_CARD = "#121826"          # Elevated card surface
BG_CARD_HOVER = "#182236"    # Card hover state
BG_HEADER_CARD = "#0f172a"   # Hero banner surface
BG_INPUT = "#0a0e17"         # Deep input & terminal surface

BORDER_COLOR = "#1f293d"     # Crisp subtle 1px border
BORDER_HOVER = "#2e3d59"     # Hovered card border
BORDER_ACTIVE = "#10b981"    # Glowing emerald border when locked
BORDER_SELECTED = "#0ea5e9"  # Glowing cyan border for selected navigation item

TEXT_WHITE = "#f8fafc"       # Primary crisp white text
TEXT_MUTED = "#94a3b8"       # Secondary slate text
TEXT_DIM = "#64748b"         # Dimmed / caption text

GREEN = "#10b981"            # Emerald primary action
GREEN_HOVER = "#059669"
GREEN_BG = "#06241b"
GREEN_BORDER = "#059669"

RED = "#ef4444"              # Crimson danger / unlock action
RED_HOVER = "#dc2626"
RED_BG = "#2a0c12"
RED_BORDER = "#b91c1c"

AMBER = "#f59e0b"            # Warning / Ping medium
AMBER_HOVER = "#d97706"
AMBER_BG = "#291b07"
AMBER_BORDER = "#b45309"

BTN_DARK = "#1c2539"         # Secondary modern button
BTN_DARK_HOVER = "#283552"

CYBER_BLUE = "#38bdf8"       # Neon cyan accent
CYBER_BLUE_BG = "#0c2238"
PRIMARY_BLUE = "#0284c7"
PRIMARY_BLUE_HOVER = "#0369a1"

TIKTOK_PINK = "#f43f5e"      # Social accent
OW_ORANGE = "#f97316"        # Overwatch accent
DEADLOCK_GOLD = "#eab308"    # Deadlock accent

FONT_FAMILY = "Segoe UI"
FONT_MONO = "Consolas"


def enable_high_dpi():
    """Enable high-DPI scaling on Windows for razor-sharp rendering."""
    if os.name == "nt":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def apply_dark_titlebar(window, round_corners: bool = True):
    """
    Enable Windows 10/11 dark titlebar, custom obsidian caption color,
    and Windows 11 native smooth rounded window corners.
    """
    if os.name != "nt":
        return
    try:
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        if not hwnd:
            hwnd = window.winfo_id()

        # DWMWA_USE_IMMERSIVE_DARK_MODE = 20 (and 19 for older Win10)
        dark_val = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(dark_val), ctypes.sizeof(dark_val))
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(dark_val), ctypes.sizeof(dark_val))

        # DWMWA_WINDOW_CORNER_PREFERENCE = 33 (2 = DWMWCP_ROUND on Windows 11)
        if round_corners:
            corner_pref = ctypes.c_int(2)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                hwnd, 33, ctypes.byref(corner_pref), ctypes.sizeof(corner_pref)
            )

        # DWMWA_CAPTION_COLOR = 35 (COLORREF is 0x00BBGGRR: #080b12 -> 0x00120b08)
        caption_color = ctypes.c_int(0x00120B08)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd, 35, ctypes.byref(caption_color), ctypes.sizeof(caption_color)
        )
    except Exception:
        pass


def load_ctk_image(path: Path, size: Tuple[int, int]) -> Optional[ctk.CTkImage]:
    """Load an image file with Pillow LANCZOS resampling into a crisp CTkImage."""
    if not path or not path.exists():
        return None
    try:
        pil_img = Image.open(str(path)).convert("RGBA")
        pil_img = pil_img.resize((size[0] * 2, size[1] * 2), Image.Resampling.LANCZOS)
        return ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=size)
    except Exception as e:
        print(f"Failed to load CTkImage {path}: {e}")
        return None
