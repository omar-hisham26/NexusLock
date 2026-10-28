"""
splash.py - Modern CustomTkinter frameless startup splash screen with automatic updater
"""
import threading
import time
from typing import Callable, Optional
import customtkinter as ctk
from src import config, i18n
from src.core import updater
from src.ui import theme


class DiscordSplash(ctk.CTk):
    """
    Frameless, centered Discord-like startup splash window built with CustomTkinter.
    Checks for updates on GitHub, downloads if needed, or boots the main app.
    """

    def __init__(self, on_ready_callback: Callable[[], None]):
        super().__init__()
        self.on_ready = on_ready_callback
        theme.enable_high_dpi()

        # Load language preference early
        saved_settings = config.load_settings()
        i18n.set_lang(saved_settings.get("language", "ar"))

        # Frameless window
        self.overrideredirect(True)
        self.configure(fg_color=theme.BG_APP)
        theme.apply_dark_titlebar(self, round_corners=True)

        # Center on screen
        width = 400
        height = 270
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        pos_x = (screen_w - width) // 2
        pos_y = (screen_h - height) // 2
        self.geometry(f"{width}x{height}+{pos_x}+{pos_y}")

        self.is_downloading = False
        self.is_closing = False
        self.icon_img: Optional[ctk.CTkImage] = None

        self._build_ui()

        # Start update check thread
        threading.Thread(target=self._run_update_check, daemon=True).start()

    def _build_ui(self):
        card = ctk.CTkFrame(
            self,
            fg_color=theme.BG_CARD,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            corner_radius=16,
        )
        card.pack(fill="both", expand=True, padx=4, pady=4)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24, pady=24)

        # High-DPI App Icon (LANCZOS 64x64)
        icon_path = config.ASSETS_DIR / "app_icon.png"
        self.icon_img = theme.load_ctk_image(icon_path, (64, 64))
        if self.icon_img:
            ctk.CTkLabel(
                inner,
                text="",
                image=self.icon_img,
                width=64,
                height=64,
            ).pack(pady=(4, 10))

        # Title
        ctk.CTkLabel(
            inner,
            text=i18n.t("app_brand_title"),
            text_color=theme.TEXT_WHITE,
            font=(theme.FONT_FAMILY, 20, "bold"),
        ).pack()

        # Version Badge
        ctk.CTkLabel(
            inner,
            text=i18n.t("version_badge", ver=config.VERSION),
            text_color=theme.CYBER_BLUE,
            font=(theme.FONT_FAMILY, 11, "bold"),
        ).pack(pady=(2, 18))

        # Smooth Rounded Progress Bar
        self.progress_bar = ctk.CTkProgressBar(
            inner,
            width=290,
            height=8,
            corner_radius=4,
            fg_color=theme.BG_INPUT,
            progress_color=theme.CYBER_BLUE,
            mode="indeterminate",
            indeterminate_speed=1.4,
        )
        self.progress_bar.pack(pady=(0, 12))
        self.progress_bar.start()

        # Status Label
        self.status_lbl = ctk.CTkLabel(
            inner,
            text=i18n.t("splash_checking"),
            text_color=theme.TEXT_MUTED,
            font=(theme.FONT_FAMILY, 12),
        )
        self.status_lbl.pack()

    def _set_status(self, text: str, fg_color: str = theme.TEXT_MUTED):
        if not self.is_closing:
            try:
                self.status_lbl.configure(text=text, text_color=fg_color)
            except Exception:
                pass

    def _run_update_check(self):
        """Background thread checking for GitHub releases."""
        time.sleep(0.4)
        self.after(0, lambda: self._set_status(i18n.t("splash_checking"), theme.CYBER_BLUE))

        update_info = updater.check_for_update(timeout=4)

        if update_info:
            ver = update_info.get("version", "")
            download_url = update_info.get("download_url")

            if download_url:
                self.is_downloading = True

                def switch_to_determinate():
                    if not self.is_closing:
                        self.progress_bar.stop()
                        self.progress_bar.configure(mode="determinate", progress_color=theme.GREEN)
                        self.progress_bar.set(0)
                        self._set_status(i18n.t("splash_found", ver=ver), theme.AMBER)

                self.after(0, switch_to_determinate)

                def on_progress(p: int):
                    def _upd():
                        if not self.is_closing:
                            self.progress_bar.set(max(0.02, p / 100.0))
                            self._set_status(i18n.t("splash_downloading", p=p), theme.GREEN)
                    self.after(0, _upd)

                ok = updater.download_and_install_update(download_url, progress_callback=on_progress)
                if ok:
                    return

        # Up to date or check completed
        self.after(0, lambda: self._set_status(i18n.t("splash_ready"), theme.GREEN))
        time.sleep(0.5)
        self.after(0, self._launch_main_app)

    def _launch_main_app(self):
        self.is_closing = True
        try:
            self.progress_bar.stop()
            self.destroy()
        except Exception:
            pass
        if self.on_ready:
            self.on_ready()
