"""
splash.py - Discord-style frameless startup splash screen with automatic updater
"""
import threading
import time
import tkinter as tk
from typing import Callable, Optional
from src import config
from src.core import updater
from src.ui import theme
from src.ui.components import draw_rounded_rect


class DiscordSplash(tk.Tk):
    """
    Frameless, centered Discord-like startup splash window.
    Checks for updates on GitHub, downloads if needed, or boots the main app.
    """

    def __init__(self, on_ready_callback: Callable[[], None]):
        super().__init__()
        self.on_ready = on_ready_callback
        theme.enable_high_dpi()

        # Frameless window (no standard Windows border or titlebar)
        self.overrideredirect(True)
        self.configure(bg=theme.BG_APP)

        # Center on screen
        width = 380
        height = 250
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        pos_x = (screen_w - width) // 2
        pos_y = (screen_h - height) // 2
        self.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

        self.anim_pos = 0
        self.anim_dir = 1
        self.is_downloading = False
        self.progress_percent = 0
        self.is_closing = False

        self._build_ui()
        self._load_icon()

        # Start animation loop
        self.after(30, self._pulse_animation)

        # Start update check thread
        threading.Thread(target=self._run_update_check, daemon=True).start()

    def _build_ui(self):
        # 1px border container
        outer = tk.Frame(self, bg=theme.BORDER_COLOR, padx=1, pady=1)
        outer.pack(fill="both", expand=True)

        inner = tk.Frame(outer, bg=theme.BG_APP, padx=20, pady=24)
        inner.pack(fill="both", expand=True)

        # App Icon
        self.icon_lbl = tk.Label(inner, bg=theme.BG_APP)
        self.icon_lbl.pack(pady=(4, 8))

        # Title
        tk.Label(
            inner,
            text="⚡ NEXUSLOCK",
            fg=theme.TEXT_WHITE,
            bg=theme.BG_APP,
            font=(theme.FONT_FAMILY, 15, "bold"),
        ).pack()

        # Version
        tk.Label(
            inner,
            text=f"Version {config.VERSION}",
            fg=theme.TEXT_MUTED,
            bg=theme.BG_APP,
            font=(theme.FONT_FAMILY, 8),
        ).pack(pady=(1, 16))

        # Progress Canvas
        self.progress_canvas = tk.Canvas(
            inner,
            width=280,
            height=6,
            bg="#131824",
            highlightthickness=0,
            bd=0,
        )
        self.progress_canvas.pack(pady=(0, 10))

        # Status Label
        self.status_lbl = tk.Label(
            inner,
            text="Checking for updates...",
            fg=theme.TEXT_MUTED,
            bg=theme.BG_APP,
            font=(theme.FONT_FAMILY, 9),
        )
        self.status_lbl.pack()

    def _load_icon(self):
        icon_path = config.ASSETS_DIR / "app_icon.png"
        if icon_path.exists():
            try:
                full = tk.PhotoImage(file=str(icon_path))
                # Scale down to ~56px
                factor = max(1, full.width() // 56)
                scaled = full.subsample(factor, factor)
                self.icon_img = scaled
                self.icon_lbl.configure(image=self.icon_img)
            except Exception:
                pass

    def _pulse_animation(self):
        if self.is_closing:
            return

        self.progress_canvas.delete("all")
        w = 280
        h = 6

        if not self.is_downloading:
            # Discord style back-and-forth glowing glide
            bar_w = 70
            draw_rounded_rect(self.progress_canvas, 0, 0, w, h, 3, fill="#131824", outline="")
            draw_rounded_rect(
                self.progress_canvas,
                self.anim_pos,
                0,
                self.anim_pos + bar_w,
                h,
                3,
                fill=theme.CYBER_BLUE,
                outline="",
            )
            self.anim_pos += self.anim_dir * 5
            if self.anim_pos >= w - bar_w:
                self.anim_dir = -1
            elif self.anim_pos <= 0:
                self.anim_dir = 1
        else:
            # Download percentage fill
            draw_rounded_rect(self.progress_canvas, 0, 0, w, h, 3, fill="#131824", outline="")
            fill_w = max(4, int((self.progress_percent / 100.0) * w))
            draw_rounded_rect(
                self.progress_canvas,
                0,
                0,
                fill_w,
                h,
                3,
                fill=theme.GREEN,
                outline="",
            )

        self.after(30, self._pulse_animation)

    def _set_status(self, text: str, fg_color: str = theme.TEXT_MUTED):
        if not self.is_closing:
            self.status_lbl.configure(text=text, fg=fg_color)

    def _run_update_check(self):
        """Background thread checking for GitHub releases."""
        time.sleep(0.4)  # Small natural pause for splash display
        self.after(0, lambda: self._set_status("جاري البحث عن تحديثات...", theme.CYBER_BLUE))

        update_info = updater.check_for_update(timeout=4)

        if update_info:
            ver = update_info.get("version", "")
            download_url = update_info.get("download_url")

            if download_url:
                self.is_downloading = True
                self.after(0, lambda: self._set_status(f"تم العثور على تحديث {ver}! جاري التنزيل...", theme.AMBER))

                def on_progress(p: int):
                    self.progress_percent = p
                    self.after(0, lambda: self._set_status(f"جاري تنزيل التحديث ({p}%)...", theme.GREEN))

                # Download and restart
                ok = updater.download_and_install_update(download_url, progress_callback=on_progress)
                if ok:
                    return

        # Up to date or check completed
        self.after(0, lambda: self._set_status("البرنامج محدث! جاري التشغيل...", theme.GREEN))
        time.sleep(0.6)
        self.after(0, self._launch_main_app)

    def _launch_main_app(self):
        self.is_closing = True
        self.destroy()
        if self.on_ready:
            self.on_ready()
