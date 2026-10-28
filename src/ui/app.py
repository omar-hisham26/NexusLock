"""
app.py - Modern CustomTkinter Main GUI Application window and orchestration for NexusLock
"""
import time
import tkinter as tk
from typing import Any, Dict, List
import customtkinter as ctk

from src import config, i18n
from src.core import admin, firewall, network
from src.games import get_all_games, get_game
from src.ui import theme
from src.ui.components import ModernModal, create_card
from src.ui.game_view import GameView
from src.ui.sidebar import Sidebar


class NexusLockGUI:
    """Main application GUI managing the sidebar, game views, live logs and window lifecycle."""

    def __init__(self):
        theme.enable_high_dpi()

        # Load settings and initialize language before building UI
        self.settings = config.load_settings()
        i18n.set_lang(self.settings.get("language", "ar"))

        self.root = ctk.CTk()
        self.root.title(i18n.t("app_window_title"))
        self.root.geometry("940x815")
        self.root.minsize(880, 750)
        self.root.configure(fg_color=theme.BG_APP)
        theme.apply_dark_titlebar(self.root, round_corners=True)

        # Window icon
        icon_path = config.ASSETS_DIR / "icon.ico"
        if icon_path.exists():
            try:
                self.root.iconbitmap(str(icon_path))
            except Exception:
                pass

        self.all_games = get_all_games()

        # Selected game view
        self.current_view_id = self.settings.get("selected_view", "overwatch")
        if not get_game(self.current_view_id):
            self.current_view_id = self.all_games[0].game_id if self.all_games else "overwatch"

        self.unblock_on_close_var = tk.BooleanVar(value=self.settings.get("unblock_on_close", False))

        self.game_views: Dict[str, GameView] = {}
        self.sidebar = None
        self.log_history: List[Dict[str, Any]] = []

        self._build_layout()

        # Handle window closing
        self.root.protocol("WM_DELETE_WINDOW", self.on_close_window)

        # Background monitoring loop
        self.root.after(300, self._initial_startup)
        self.root.after(3000, self._periodic_monitor_loop)

    def _build_layout(self):
        # Main split container: Left Sidebar + Right Content
        main_frame = ctk.CTkFrame(self.root, fg_color=theme.BG_APP, corner_radius=0)
        main_frame.pack(fill="both", expand=True)

        # 1. Left Sidebar
        self.sidebar = Sidebar(
            parent=main_frame,
            games=self.all_games,
            selected_view_id=self.current_view_id,
            on_view_change=self.switch_view,
            on_lang_change=self.change_language,
        )
        self.sidebar.pack(side="left", fill="y")

        # Vertical Divider
        ctk.CTkFrame(main_frame, fg_color=theme.BORDER_COLOR, width=1, corner_radius=0).pack(side="left", fill="y")

        # 2. Right Content Area
        right_container = ctk.CTkFrame(main_frame, fg_color=theme.BG_APP, corner_radius=0)
        right_container.pack(side="left", fill="both", expand=True, padx=20, pady=16)

        # Container for the active GameView
        self.view_container = ctk.CTkFrame(right_container, fg_color="transparent")
        self.view_container.pack(fill="x")

        # =========================================================
        # Shared Terminal Activity Log (created before GameViews so initial logs render)
        # =========================================================
        log_header = ctk.CTkFrame(right_container, fg_color="transparent")
        log_header.pack(fill="x", pady=(4, 4))

        self.log_header_lbl = ctk.CTkLabel(
            log_header,
            text=i18n.t("log_header"),
            text_color=theme.TEXT_DIM,
            font=(theme.FONT_FAMILY, 11, "bold"),
        )
        self.log_header_lbl.pack(side="right" if i18n.is_rtl() else "left")

        log_outer, log_inner = create_card(
            right_container,
            bg_color=theme.BG_INPUT,
            border_color=theme.BORDER_COLOR,
            pad_x=12,
            pad_y=8,
            radius=14,
        )
        log_outer.pack(fill="both", expand=True)

        self.log_box = tk.Text(
            log_inner,
            bg=theme.BG_INPUT,
            fg="#cbd5e1",
            bd=0,
            highlightthickness=0,
            font=(theme.FONT_FAMILY, 9),
            wrap="word",
            state="disabled",
            height=4,
            padx=4,
            pady=2,
        )
        self.log_box.pack(fill="both", expand=True)

        self._apply_log_tags_justify()

        # =========================================================
        # Developer & Socials Footer
        # =========================================================
        footer = ctk.CTkFrame(right_container, fg_color="transparent")
        footer.pack(fill="x", pady=(10, 0))

        dev_outer, dev_inner = create_card(
            footer,
            border_color=theme.BORDER_COLOR,
            bg_color=theme.BG_CARD,
            pad_x=14,
            pad_y=7,
            radius=12,
        )
        dev_outer.pack(fill="x")

        self.dev_lbl = ctk.CTkLabel(
            dev_inner,
            text=i18n.t("dev_label"),
            text_color=theme.TEXT_MUTED,
            font=(theme.FONT_FAMILY, 11, "bold"),
        )
        self.dev_lbl.pack(side="right", padx=(10, 0))

        # Copy clipboard handlers
        def copy_bnet():
            self.root.clipboard_clear()
            self.root.clipboard_append("BESTDQ#2639")
            self.add_log("log_copied_bnet", "info")

        def copy_tiktok():
            self.root.clipboard_clear()
            self.root.clipboard_append("bbooqqww")
            self.add_log("log_copied_tiktok", "info")

        # Battle.net Pill Button
        self.bnet_btn = ctk.CTkButton(
            dev_inner,
            text=i18n.t("dev_bnet_btn"),
            command=copy_bnet,
            fg_color=theme.BG_INPUT,
            hover_color=theme.BG_CARD_HOVER,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            text_color=theme.CYBER_BLUE,
            font=(theme.FONT_FAMILY, 11, "bold"),
            height=28,
            corner_radius=8,
        )
        self.bnet_btn.pack(side="right", padx=(8, 0))

        # TikTok Pill Button
        self.tiktok_btn = ctk.CTkButton(
            dev_inner,
            text=i18n.t("dev_tiktok_btn"),
            command=copy_tiktok,
            fg_color=theme.BG_INPUT,
            hover_color=theme.BG_CARD_HOVER,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            text_color=theme.TIKTOK_PINK,
            font=(theme.FONT_FAMILY, 11, "bold"),
            height=28,
            corner_radius=8,
        )
        self.tiktok_btn.pack(side="right", padx=(8, 0))

        # Hint
        self.dev_hint_lbl = ctk.CTkLabel(
            dev_inner,
            text=i18n.t("dev_copy_hint"),
            text_color=theme.TEXT_DIM,
            font=(theme.FONT_FAMILY, 11),
        )
        self.dev_hint_lbl.pack(side="left")

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
                game_icon=self.sidebar.icon_cache.get(game.game_id),
            )
            self.game_views[game.game_id] = view

        # Display initially selected game view
        if self.current_view_id in self.game_views:
            self.game_views[self.current_view_id].pack(fill="x")

    def _apply_log_tags_justify(self):
        just = "right" if i18n.is_rtl() else "left"
        self.log_box.tag_config("success", foreground="#34d399", justify=just)
        self.log_box.tag_config("error", foreground="#f87171", justify=just)
        self.log_box.tag_config("warn", foreground="#fbbf24", justify=just)
        self.log_box.tag_config("info", foreground="#cbd5e1", justify=just)

    def _format_log_entry(self, entry: Dict[str, Any]) -> str:
        """Format a stored log entry into the currently active language."""
        key = entry["key"]
        kwargs = dict(entry.get("kwargs", {}))
        now = entry["time"]

        # Dynamically localize game name and server name if game_id is stored
        if "game_id" in kwargs:
            g_obj = get_game(kwargs["game_id"])
            if g_obj:
                kwargs["game"] = g_obj.get_display_name()
                if "server_code" in kwargs:
                    srv = g_obj.get_server_by_code(kwargs["server_code"])
                    if srv:
                        kwargs["server"] = srv["title"]
        elif "game" in kwargs and hasattr(self, "all_games"):
            # Fallback for game string if game_id was omitted
            for g_item in self.all_games:
                if kwargs["game"] in (g_item.display_name, g_item.display_name_ar):
                    kwargs["game"] = g_item.get_display_name()
                    break

        text = i18n.t(key, **kwargs)
        if i18n.is_rtl():
            return f"• {text}   \u200F[{now}]\n"
        return f"[{now}]   • {text}\n"

    def _rerender_logs(self):
        """Re-translate and redraw all log entries in the active language."""
        try:
            if not self.root.winfo_exists():
                return
            self._apply_log_tags_justify()
            self.log_box.configure(state="normal")
            self.log_box.delete("1.0", "end")
            for entry in self.log_history:
                line = self._format_log_entry(entry)
                self.log_box.insert("end", line, entry["level"])
            self.log_box.see("end")
            self.log_box.configure(state="disabled")
        except Exception:
            pass

    def change_language(self, new_lang: str):
        """Switch application language dynamically between Arabic ('ar') and English ('en')."""
        i18n.set_lang(new_lang)
        self.settings = config.load_settings()
        self.settings["language"] = i18n.get_lang()
        config.save_settings(self.settings)

        self.root.title(i18n.t("app_window_title"))

        if self.sidebar:
            self.sidebar.refresh_language()

        for view in self.game_views.values():
            view.refresh_language()

        self.log_header_lbl.configure(text=i18n.t("log_header"))
        self.log_header_lbl.pack_forget()
        self.log_header_lbl.pack(side="right" if i18n.is_rtl() else "left")

        self.dev_lbl.configure(text=i18n.t("dev_label"))
        self.dev_hint_lbl.configure(text=i18n.t("dev_copy_hint"))
        self.bnet_btn.configure(text=i18n.t("dev_bnet_btn"))
        self.tiktok_btn.configure(text=i18n.t("dev_tiktok_btn"))

        # Re-render all existing logs in the new language, then log the language switch
        self._rerender_logs()
        self.add_log("log_lang_changed", "info")

    def add_log(self, key_or_text: str, level: str = "info", **kwargs):
        """Append a translatable timestamped entry to the activity log."""
        now = time.strftime("%H:%M:%S")
        entry = {
            "key": key_or_text,
            "kwargs": kwargs,
            "level": level,
            "time": now,
        }
        self.log_history.append(entry)

        try:
            if self.root.winfo_exists():
                self.root.after(0, self._rerender_logs)
        except Exception:
            pass

    def switch_view(self, new_view_id: str):
        """Switch between Game Controls."""
        if new_view_id not in self.game_views:
            return

        # Hide current view
        if self.current_view_id in self.game_views:
            self.game_views[self.current_view_id].pack_forget()

        # Show target view
        self.current_view_id = new_view_id
        target_view = self.game_views[new_view_id]
        target_view.pack(fill="x")
        target_view.refresh_all()
        game_name = target_view.game.display_name
        self.add_log("log_switched_game", "info", game_id=new_view_id, game=game_name)

        # Update sidebar active indicator
        if self.sidebar:
            self.sidebar.set_active_view(new_view_id)

        # Save selected view preference
        self.settings = config.load_settings()
        self.settings["selected_view"] = new_view_id
        config.save_settings(self.settings)

    def _on_game_lock_state_changed(self, game_id: str, is_locked: bool, srv_name: str = ""):
        """Notify sidebar button to update its status badge."""
        if self.sidebar:
            self.sidebar.update_game_lock_status(game_id, is_locked, srv_name)

    def _initial_startup(self):
        """Startup greetings and status announcements."""
        self.add_log("log_startup_ok", "success")
        if not admin.is_admin():
            self.add_log("log_no_admin_warn", "warn")

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
            if not self.root.winfo_exists():
                return
            if self.current_view_id in self.game_views:
                self.game_views[self.current_view_id].check_game_running()
            self.root.after(3000, self._periodic_monitor_loop)
        except Exception:
            pass

    def factory_reset_all(self):
        """Remove all rules for all games, reset settings, and flush DNS."""
        self.add_log("log_reset_start", "warn")
        firewall.clean_all_nexuslock_rules()
        network.flush_dns()

        # Delete settings files (preserve current language)
        current_lang = i18n.get_lang()
        for s_file in [config.get_settings_file_path(), config.DATA_DIR / "settings.json"]:
            if s_file.exists():
                try:
                    s_file.unlink()
                except Exception:
                    pass

        fresh = config.load_settings()
        fresh["language"] = current_lang
        config.save_settings(fresh)

        # Reset views
        for game_id, view in self.game_views.items():
            view.game_path_var.set("")
            view.update_firewall_status()
            if self.sidebar:
                self.sidebar.update_game_lock_status(game_id, False)

        self.add_log("log_reset_done", "success")
        ModernModal.show_info(
            self.root,
            i18n.t("msg_reset_done_title"),
            i18n.t("msg_reset_done_body"),
        )

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
