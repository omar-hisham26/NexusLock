"""
theme.py - Visual styling, colors, DPI awareness, and dark titlebar for Windows
"""
import ctypes
import os

# Visual color palette (Cyber Dark)
BG_APP = "#0b0e14"           # Main background
BG_SIDEBAR = "#0e131d"       # Left sidebar background
BG_CARD = "#131824"          # Card background
BG_CARD_HOVER = "#182030"    # Hover card
BG_INPUT = "#090d14"         # Input and log terminal background

BORDER_COLOR = "#21293d"     # Subtle card border
BORDER_ACTIVE = "#10b981"    # Green border when locked
BORDER_SELECTED = "#38bdf8"  # Selected item border

TEXT_WHITE = "#f8fafc"       # Primary text
TEXT_MUTED = "#8b98b1"       # Secondary text
TEXT_DIM = "#56637a"         # Dimmed / disabled text

GREEN = "#10b981"            # Emerald active
GREEN_HOVER = "#059669"
GREEN_BG = "#07261d"

RED = "#ef4444"              # Red inactive
RED_HOVER = "#dc2626"
RED_BG = "#280a0e"

AMBER = "#f59e0b"            # Warning
AMBER_HOVER = "#d97706"
AMBER_BG = "#2b1d08"

BTN_DARK = "#1e2638"         # Neutral dark button
BTN_DARK_HOVER = "#2a354d"

CYBER_BLUE = "#38bdf8"       # Accent blue
TIKTOK_PINK = "#f43f5e"      # Social accent
OW_ORANGE = "#f97316"        # Overwatch accent
DEADLOCK_GOLD = "#eab308"    # Deadlock accent

FONT_FAMILY = "Segoe UI"
FONT_MONO = "Consolas"


def enable_high_dpi():
    """Make fonts and UI razor-sharp on high-resolution screens."""
    if os.name == "nt":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def apply_dark_titlebar(window):
    """Enable dark titlebar on Windows 10 and 11."""
    if os.name != "nt":
        return
    try:
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        value = ctypes.c_int(2)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(value), ctypes.sizeof(value))
    except Exception:
        pass
