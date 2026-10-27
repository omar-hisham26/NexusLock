"""
app.py - Main GUI Application window and orchestration for NexusLock
"""
import os
import threading
import time
import tkinter as tk
from tkinter import messagebox
from typing import Dict, Union

from src import config
from src.core import admin, firewall, network
from src.games import get_all_games, get_game
from src.games.base import BaseGame
from src.ui import theme
from src.ui.catalog_view import SupportedGamesView
from src.ui.components import create_card
from src.ui.game_view import GameView
from src.ui.sidebar import Sidebar


class NexusLockGUI:
    """Main application GUI managing the sidebar, catalog view, game views, logs and window lifecycle."""

    def __init__(self):
        theme.enable_high_dpi()

        self.root = tk.Tk()
        self.root.title("NexusLock — حظر وملتقط سيرفرات الألعاب")
        self.root.geometry("900x790")
        self.root.minsize(840, 730)
        self.root.configure(bg=theme.BG_APP)
        theme.apply_dark_titlebar(self.root)

        # Window icon
        icon_path = config.ASSETS_DIR / "icon.ico"
        if icon_path.exists():
            try:
                self.root.iconbitmap(str(icon_path))
            except Exception:
                pass

        # Load settings
        self.settings = config.load_settings()
        self.all_games = get_all_games()

        # Selected view: "catalog" or game_id
        self.current_view_id = self.settings.get("selected_view", "catalog")
        if self.current_view_id != "catalog" and not get_game(self.current_view_id):
            self.current_view_id = "catalog"

        self.unblock_on_close_var = tk.BooleanVar(value=self.settings.get("unblock_on_close", False))

        self.game_views: Dict[str, GameView] = {}
        self.catalog_view = None
        self.sidebar = None

        self._build_layout()

        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_close_window)

        # Background monitoring loop
        self.root.after(300, self._initial_startup)
        self.root.after(3000, self._periodic_monitor_loop)

    def _build_layout(self):
        # Main split container: Left Sidebar + Right Content
        main_frame = tk.Frame(self.root, bg=theme.BG_APP)
        main_frame.pack(fill="both", expand=True)

        # 1. Left Sidebar
        self.sidebar = Sidebar(
            parent=main_frame,
            games=self.all_games,
            selected_view_id=self.current_view_id,
            on_view_change=self.switch_view,
        )
        self.sidebar.pack(side="left", fill="y")

        # Vertical Divider
        tk.Frame(main_frame, bg=theme.BORDER_COLOR, width=1).pack(side="left", fill="y")

        # 2. Right Content Area
        right_container = tk.Frame(main_frame, bg=theme.BG_APP, padx=18, pady=14)
        right_container.pack(side="left", fill="both", expand=True)

        # Container for the dynamic View (Catalog or GameView)
        self.view_container = tk.Frame(right_container, bg=theme.BG_APP)
        self.view_container.pack(fill="x")

        # Create Catalog View
        self.catalog_view = SupportedGamesView(
            parent=self.view_container,
            games=self.all_games,
            icon_cache=self.sidebar.icon_cache,
            on_select_game=self.switch_view,
        )

        # Create Views for all games
        for game in self.all_games:
            game_cfg = self.settings.get("games", {}).get(game.game_id, {})
            initial_path = game_cfg.get("game_path", "")
            initial_server = game_cfg.get("target_server", game.default_server_code)
            view = GameView(
                parent=self.view_container,
                game=game,
                initial_path=initial_path,
                initial_server_code=initial_server,
                unblock_on_close_var=self.unblock_on_close_var,
                logger_func=self.add_log,
                on_lock_state_changed=self._on_game_lock_state_changed,
                on_reset_requested=self.factory_reset_all,
            )
            self.game_views[game.game_id] = view

        # Display initially selected view
        if self.current_view_id == "catalog":
            self.catalog_view.pack(fill="x")
        elif self.current_view_id in self.game_views:
            self.game_views[self.current_view_id].pack(fill="x")

        # =========================================================
        # Shared Terminal Activity Log (at bottom of right area)
        # =========================================================
        log_header = tk.Frame(right_container, bg=theme.BG_APP)
        log_header.pack(fill="x", pady=(4, 2))

        tk.Label(
            log_header,
            text="سجل العمليات المباشر",
            fg=theme.TEXT_MUTED,
            bg=theme.BG_APP,
            font=(theme.FONT_FAMILY, 9, "bold"),
        ).pack(side="right")

        log_outer, log_inner = create_card(right_container, bg_color=theme.BG_INPUT, pad_x=10, pad_y=8)
        log_outer.pack(fill="both", expand=True)

        self.log_box = tk.Text(
            log_inner,
            bg=theme.BG_INPUT,
            fg="#cbd5e1",
            bd=0,
            highlightthickness=0,
            font=(theme.FONT_FAMILY, 8),
            wrap="word",
            state="disabled",
            height=4,
        )
        self.log_box.pack(fill="both", expand=True)

        self.log_box.tag_config("success", foreground="#34d399", justify="right")
        self.log_box.tag_config("error", foreground="#f87171", justify="right")
        self.log_box.tag_config("warn", foreground="#fbbf24", justify="right")
        self.log_box.tag_config("info", foreground="#cbd5e1", justify="right")

        # =========================================================
        # Developer & Socials Footer
        # =========================================================
        footer = tk.Frame(right_container, bg=theme.BG_APP)
        footer.pack(fill="x", pady=(8, 0))

        dev_outer, dev_inner = create_card(footer, border_color=theme.BORDER_COLOR, bg_color=theme.BG_CARD, pad_x=12, pad_y=6)
        dev_outer.pack(fill="x")

        tk.Label(
            dev_inner,
            text="المطور",
            fg=theme.TEXT_MUTED,
            bg=theme.BG_CARD,
            font=(theme.FONT_FAMILY, 9, "bold"),
        ).pack(side="right", padx=(8, 0))

        # Battle.net
        bnet_frame = tk.Frame(dev_inner, bg=theme.BG_CARD, cursor="hand2")
        bnet_frame.pack(side="right", padx=(14, 0))

        tk.Label(
            bnet_frame,
            text="🎮 Battle.net:",
            fg=theme.CYBER_BLUE,
            bg=theme.BG_CARD,
            font=(theme.FONT_FAMILY, 8, "bold"),
            cursor="hand2",
        ).pack(side="left")

        bnet_lbl = tk.Label(
            bnet_frame,
            text="BESTDQ#2639",
            fg=theme.TEXT_WHITE,
            bg=theme.BG_CARD,
            font=(theme.FONT_MONO, 8, "bold"),
            cursor="hand2",
        )
        bnet_lbl.pack(side="left", padx=(4, 0))

        # TikTok
        tiktok_frame = tk.Frame(dev_inner, bg=theme.BG_CARD, cursor="hand2")
        tiktok_frame.pack(side="right", padx=(14, 0))

        tk.Label(
            tiktok_frame,
            text="🎵 TikTok:",
            fg=theme.TIKTOK_PINK,
            bg=theme.BG_CARD,
            font=(theme.FONT_FAMILY, 8, "bold"),
            cursor="hand2",
        ).pack(side="left")

        tiktok_lbl = tk.Label(
            tiktok_frame,
            text="@bbooqqww",
            fg=theme.TEXT_WHITE,
            bg=theme.BG_CARD,
            font=(theme.FONT_MONO, 8, "bold"),
            cursor="hand2",
        )
        tiktok_lbl.pack(side="left", padx=(4, 0))

        # Hint
        tk.Label(
            dev_inner,
            text="اضغط على أي حساب للنسخ 📋",
            fg=theme.TEXT_MUTED,
            bg=theme.BG_CARD,
            font=(theme.FONT_FAMILY, 8),
        ).pack(side="left")

        # Copy clipboard handlers
        def copy_bnet(_e=None):
            self.root.clipboard_clear()
            self.root.clipboard_append("BESTDQ#2639")
            self.add_log("تم نسخ حساب Battle.net للمطور (BESTDQ#2639) للحافظة!", "info")

        def copy_tiktok(_e=None):
            self.root.clipboard_clear()
            self.root.clipboard_append("bbooqqww")
            self.add_log("تم نسخ يوزر TikTok للمطور (bbooqqww) للحافظة!", "info")

        for w in (bnet_frame, bnet_lbl):
            w.bind("<Button-1>", copy_bnet)
        for w in (tiktok_frame, tiktok_lbl):
            w.bind("<Button-1>", copy_tiktok)

    def add_log(self, text: str, level: str = "info"):
        """Append a clean, formatted timestamped entry to the activity log."""
        now = time.strftime("%H:%M:%S")

        def _insert():
            self.log_box.configure(state="normal")
            line = f"• {text}   \u200F[{now}]\n"
            self.log_box.insert("end", line, level)
            self.log_box.see("end")
            self.log_box.configure(state="disabled")

        self.root.after(0, _insert)

    def switch_view(self, new_view_id: str):
        """Switch between the Supported Games Catalog and Game Controls."""
        if new_view_id != "catalog" and new_view_id not in self.game_views:
            return

        # Hide current view
        if self.current_view_id == "catalog":
            self.catalog_view.pack_forget()
        elif self.current_view_id in self.game_views:
            self.game_views[self.current_view_id].pack_forget()

        # Show target view
        self.current_view_id = new_view_id
        if new_view_id == "catalog":
            self.catalog_view.pack(fill="x")
            self.add_log("تم فتح شاشة: الألعاب المدعومة في NexusLock", "info")
        else:
            target_view = self.game_views[new_view_id]
            target_view.pack(fill="x")
            target_view.refresh_all()
            game_name = target_view.game.display_name
            self.add_log(f"تم الانتقال إلى إعدادات: {game_name}", "info")

        # Update sidebar active indicator
        if self.sidebar:
            self.sidebar.set_active_view(new_view_id)

        # Save selected view preference
        self.settings["selected_view"] = new_view_id
        config.save_settings(self.settings)

    def _on_game_lock_state_changed(self, game_id: str, is_locked: bool, srv_name: str = ""):
        """Notify sidebar button to update its status badge."""
        if self.sidebar:
            self.sidebar.update_game_lock_status(game_id, is_locked, srv_name)

    def _initial_startup(self):
        """Startup greetings and status announcements."""
        self.add_log("⚡ تم تشغيل NexusLock بنجاح (Multi-Game Server Selector).", "success")
        if not admin.is_admin():
            self.add_log("⚠️ تنبيه: التطبيق يعمل بدون صلاحيات المسؤول، يرجى تشغيله كمسؤول لتطبيق قواعد جدار الحماية.", "warn")

        # Initial check for all games lock status in sidebar
        for game in self.all_games:
            locked = game.is_locked()
            view = self.game_views.get(game.game_id)
            srv_title = view.get_current_server().get("title", "").split("(")[0].strip() if view else ""
            if self.sidebar:
                self.sidebar.update_game_lock_status(game.game_id, locked, srv_title)

    def _periodic_monitor_loop(self):
        """Run periodic check for running games."""
        try:
            if self.current_view_id in self.game_views:
                self.game_views[self.current_view_id].check_game_running()
        except Exception:
            pass
        self.root.after(3000, self._periodic_monitor_loop)

    def factory_reset_all(self):
        """Remove all rules for all games, reset settings, and flush DNS."""
        self.add_log("جاري إجراء ضبط المصنع وحذف جميع قواعد NexusLock...", "warn")
        firewall.clean_all_nexuslock_rules()
        network.flush_dns()

        # Delete settings file
        s_file = config.get_settings_file_path()
        if s_file.exists():
            try:
                s_file.unlink()
            except Exception:
                pass

        # Reset views
        for game_id, view in self.game_views.items():
            view.game_path_var.set("")
            view.update_firewall_status()
            if self.sidebar:
                self.sidebar.update_game_lock_status(game_id, False)

        self.add_log("✅ اكتمل ضبط المصنع وتم تنظيف جدار الحماية بالكامل.", "success")
        messagebox.showinfo("ضبط المصنع", "تمت استعادة الإعدادات الأصلية وتنظيف قواعد جدار الحماية بنجاح!")

    def on_close_window(self):
        """Handle window closing; unblock games if the user enabled that option."""
        if self.unblock_on_close_var.get():
            try:
                for game in self.all_games:
                    game.disable_lock()
            except Exception:
                pass
        self.root.destroy()

    def run(self):
        self.root.mainloop()


# Backward compatibility alias
NetherWatchGUI = NexusLockGUI
