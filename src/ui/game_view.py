"""
game_view.py - Modern CustomTkinter game control view with sleek CTkOptionMenu, rounded cards, and dark modals
"""
import os
import threading
import tkinter as tk
from tkinter import filedialog
from typing import Callable, Optional, Dict, Any, List
import customtkinter as ctk

from src import config, i18n
from src.core import network
from src.games.base import BaseGame
from src.ui import theme
from src.ui.components import ModernButton, ModernModal, ModernToggleSwitch, create_card


class GameView(ctk.CTkFrame):
    """View panel managing server selection, settings, path, ping and rules for a specific game."""

    def __init__(
        self,
        parent,
        game: BaseGame,
        initial_path: str,
        initial_server_code: str,
        unblock_on_close_var: tk.BooleanVar,
        logger_func: Callable[[str, str], None],
        on_lock_state_changed: Optional[Callable[[str, bool, str], None]] = None,
        on_reset_requested: Optional[Callable[[], None]] = None,
        game_icon: Optional[ctk.CTkImage] = None,
    ):
        super().__init__(parent, fg_color="transparent")
        self.game = game
        self.game_icon = game_icon
        self.logger = logger_func
        self.on_lock_state_changed = on_lock_state_changed
        self.on_reset_requested = on_reset_requested
        self.unblock_on_close_var = unblock_on_close_var

        self.game_path_var = tk.StringVar(value=initial_path)
        self.is_game_running = False
        self.has_running_check = False
        self.last_locked_state: Optional[bool] = None
        self.last_ping_ms: Optional[int] = None
        self.has_ping_result = False

        # Servers list
        self.servers_list: List[Dict[str, Any]] = self.game.get_servers_list()
        self.current_server_code = initial_server_code or self.game.default_server_code
        if not self.game.get_server_by_code(self.current_server_code):
            self.current_server_code = self.servers_list[0]["code"] if self.servers_list else self.game.default_server_code

        # Server picker variable
        curr_srv = self.game.get_server_by_code(self.current_server_code)
        init_title = curr_srv["title"] if curr_srv else self.current_server_code
        self.selected_server_var = ctk.StringVar(value=init_title)

        self._build_ui()
        self.refresh_all()

    def get_current_server(self) -> Dict[str, Any]:
        return self.game.get_server_by_code(self.current_server_code) or {
            "code": self.current_server_code,
            "title": self.current_server_code,
            "ping_ip": "",
        }

    def _get_short_server_name(self) -> str:
        curr_srv = self.get_current_server()
        srv_title = curr_srv.get("title", self.current_server_code)
        return srv_title.split("(")[0].strip()

    def _build_ui(self):
        container = self

        # =========================================================
        # 1. Header (Game Icon + Title + Platform Tagline)
        # =========================================================
        header = ctk.CTkFrame(container, fg_color="transparent")
        header.pack(fill="x", pady=(0, 12))

        if self.game_icon:
            ctk.CTkLabel(
                header,
                text="",
                image=self.game_icon,
                width=38,
                height=38,
            ).pack(side="left", padx=(0, 10))

        title_col = ctk.CTkFrame(header, fg_color="transparent")
        title_col.pack(side="left")

        self.lbl_title = ctk.CTkLabel(
            title_col,
            text=self.game.get_display_name().upper() if not i18n.is_rtl() else self.game.get_display_name(),
            text_color=theme.TEXT_WHITE,
            font=(theme.FONT_FAMILY, 19, "bold"),
            anchor="w",
            height=22,
        )
        self.lbl_title.pack(anchor="w")

        self.lbl_tag = ctk.CTkLabel(
            title_col,
            text=self.game.get_tagline(),
            text_color=theme.TEXT_MUTED,
            font=(theme.FONT_FAMILY, 11),
            anchor="w",
            height=16,
        )
        self.lbl_tag.pack(anchor="w")

        # Live Process Pill Badge on the right of the header
        self.game_state_lbl = ctk.CTkLabel(
            header,
            text=i18n.t("game_state_checking"),
            text_color=theme.TEXT_MUTED,
            fg_color=theme.BG_CARD,
            corner_radius=8,
            font=(theme.FONT_FAMILY, 11, "bold"),
            padx=12,
            pady=5,
        )
        self.game_state_lbl.pack(side="right")

        # =========================================================
        # 2. Hero Firewall Status Banner Card (Locked / Unlocked)
        # =========================================================
        self.status_outer, self.status_inner = create_card(
            container,
            border_color=theme.BORDER_COLOR,
            bg_color=theme.BG_CARD,
            pad_x=18,
            pad_y=14,
            radius=15,
            border_width=1,
        )
        self.status_outer.pack(fill="x", pady=(0, 12))

        self.status_title = ctk.CTkLabel(
            self.status_inner,
            text=i18n.t("status_checking_title"),
            text_color=theme.TEXT_WHITE,
            font=(theme.FONT_FAMILY, 14, "bold"),
            anchor="w",
        )
        self.status_title.pack(fill="x")

        self.status_subtitle = ctk.CTkLabel(
            self.status_inner,
            text=i18n.t("status_checking_sub"),
            text_color=theme.TEXT_MUTED,
            font=(theme.FONT_FAMILY, 12),
            anchor="w",
        )
        self.status_subtitle.pack(fill="x", pady=(3, 0))

        # =========================================================
        # 3. Target Server Selection & Live Ping Card
        # =========================================================
        srv_outer, srv_inner = create_card(container, pad_x=16, pad_y=14, radius=15)
        srv_outer.pack(fill="x", pady=(0, 12))

        srv_top = ctk.CTkFrame(srv_inner, fg_color="transparent")
        srv_top.pack(fill="x")

        # Left: Server Selector Label & Modern CTkOptionMenu
        srv_info = ctk.CTkFrame(srv_top, fg_color="transparent")
        srv_info.pack(side="left", fill="x", expand=True)

        self.select_srv_lbl = ctk.CTkLabel(
            srv_info,
            text=i18n.t("select_server_lbl"),
            text_color=theme.TEXT_WHITE,
            font=(theme.FONT_FAMILY, 13, "bold"),
            anchor="w",
        )
        self.select_srv_lbl.pack(fill="x", pady=(0, 6))

        combo_values = [s["title"] for s in self.servers_list]
        self.server_combo = ctk.CTkOptionMenu(
            srv_info,
            variable=self.selected_server_var,
            values=combo_values,
            command=self._on_server_selected,
            fg_color=theme.BG_INPUT,
            button_color=theme.PRIMARY_BLUE,
            button_hover_color=theme.PRIMARY_BLUE_HOVER,
            dropdown_fg_color=theme.BG_SIDEBAR,
            dropdown_hover_color=theme.BG_CARD_HOVER,
            dropdown_text_color=theme.TEXT_WHITE,
            text_color=theme.TEXT_WHITE,
            font=(theme.FONT_FAMILY, 12, "bold"),
            dropdown_font=(theme.FONT_FAMILY, 12),
            height=38,
            corner_radius=10,
            dynamic_resizing=False,
        )
        self.server_combo.pack(fill="x", pady=(0, 6))

        # Server technical details label
        self.srv_detail_lbl = ctk.CTkLabel(
            srv_info,
            text=i18n.t(
                "server_details_lbl",
                code=self.current_server_code,
                ip=self.get_current_server().get("ping_ip", ""),
            ),
            text_color=theme.TEXT_DIM,
            font=(theme.FONT_FAMILY, 11),
            anchor="w",
        )
        self.srv_detail_lbl.pack(anchor="w")

        # Right: Live Ping Pill Badge & Test Ping Button
        ping_box = ctk.CTkFrame(srv_top, fg_color="transparent")
        ping_box.pack(side="right", padx=(14, 0))

        self.ping_badge = ctk.CTkLabel(
            ping_box,
            text="... ms",
            text_color=theme.TEXT_WHITE,
            fg_color=theme.BG_INPUT,
            corner_radius=9,
            font=(theme.FONT_FAMILY, 12, "bold"),
            width=96,
            height=36,
        )
        self.ping_badge.pack(side="left", padx=(0, 8))

        self.btn_ping = ModernButton(
            ping_box,
            text=i18n.t("btn_test_ping"),
            command=self.measure_ping_async,
            bg_color=theme.BTN_DARK,
            hover_color=theme.BTN_DARK_HOVER,
            font_size=9,
            width=105,
            height=36,
            radius=9,
            border_width=1,
            border_color=theme.BORDER_HOVER,
        )
        self.btn_ping.pack(side="left")

        # =========================================================
        # 4. Game Executable Path Card
        # =========================================================
        game_outer, game_inner = create_card(container, pad_x=16, pad_y=12, radius=15)
        game_outer.pack(fill="x", pady=(0, 12))

        game_head = ctk.CTkFrame(game_inner, fg_color="transparent")
        game_head.pack(fill="x", pady=(0, 6))

        self.game_path_lbl = ctk.CTkLabel(
            game_head,
            text=i18n.t("game_path_lbl", game=self.game.get_display_name(), exes=", ".join(self.game.exe_names)),
            text_color=theme.TEXT_WHITE,
            font=(theme.FONT_FAMILY, 12, "bold"),
        )
        self.game_path_lbl.pack(side="left")

        path_row = ctk.CTkFrame(game_inner, fg_color="transparent")
        path_row.pack(fill="x")

        self.path_entry = ctk.CTkEntry(
            path_row,
            textvariable=self.game_path_var,
            fg_color=theme.BG_INPUT,
            text_color=theme.TEXT_WHITE,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            corner_radius=9,
            height=36,
            font=(theme.FONT_MONO, 11),
        )
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.path_entry.bind("<FocusOut>", self._on_path_changed)
        self.path_entry.bind("<Return>", self._on_path_changed)

        self.btn_browse = ModernButton(
            path_row,
            text=i18n.t("btn_browse"),
            command=self.browse_game_path,
            bg_color=theme.BTN_DARK,
            hover_color=theme.BTN_DARK_HOVER,
            font_size=9,
            width=110,
            height=36,
            radius=9,
            border_width=1,
            border_color=theme.BORDER_HOVER,
        )
        self.btn_browse.pack(side="right")

        # =========================================================
        # 5. Primary Action Buttons / Game Running Warning
        # =========================================================
        self.actions_container = ctk.CTkFrame(container, fg_color="transparent")
        self.actions_container.pack(fill="x", pady=(0, 12))

        self.buttons_frame = ctk.CTkFrame(self.actions_container, fg_color="transparent")
        self.buttons_frame.pack(fill="x")
        self.buttons_frame.grid_columnconfigure(0, weight=1)
        self.buttons_frame.grid_columnconfigure(1, weight=1)

        srv_short = self._get_short_server_name()
        self.btn_activate = ModernButton(
            self.buttons_frame,
            text=i18n.t("btn_activate", server=srv_short),
            command=self.activate_lock,
            bg_color=theme.GREEN,
            hover_color=theme.GREEN_HOVER,
            text_color="#ffffff",
            font_size=10,
            height=50,
            radius=12,
        )
        self.btn_activate.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.btn_deactivate = ModernButton(
            self.buttons_frame,
            text=i18n.t("btn_deactivate"),
            command=self.deactivate_lock,
            bg_color=theme.RED,
            hover_color=theme.RED_HOVER,
            text_color="#ffffff",
            font_size=10,
            height=50,
            radius=12,
        )
        self.btn_deactivate.grid(row=0, column=1, sticky="ew", padx=(6, 0))

        # Warning card shown when game is currently running
        self.game_running_outer, self.game_running_inner = create_card(
            self.actions_container,
            border_color=theme.AMBER,
            bg_color=theme.AMBER_BG,
            pad_x=16,
            pad_y=12,
            radius=14,
        )

        self.warn_title_lbl = ctk.CTkLabel(
            self.game_running_inner,
            text=i18n.t("game_running_warn_title", game=self.game.get_display_name()),
            text_color="#fde68a",
            font=(theme.FONT_FAMILY, 13, "bold"),
            anchor="center",
        )
        self.warn_title_lbl.pack(fill="x")

        self.warn_sub_lbl = ctk.CTkLabel(
            self.game_running_inner,
            text=i18n.t("game_running_warn_sub"),
            text_color="#fef3c7",
            font=(theme.FONT_FAMILY, 11),
            anchor="center",
        )
        self.warn_sub_lbl.pack(fill="x", pady=(2, 0))

        # =========================================================
        # 6. Options & Maintenance Row (Toggle, Flush DNS, Reset)
        # =========================================================
        opt_outer, opt_inner = create_card(container, pad_x=14, pad_y=10, radius=14)
        opt_outer.pack(fill="x", pady=(0, 10))

        opt_row = ctk.CTkFrame(opt_inner, fg_color="transparent")
        opt_row.pack(fill="x")

        self.toggle_switch = ModernToggleSwitch(
            opt_row,
            variable=self.unblock_on_close_var,
            command=self._on_toggle_changed,
        )
        self.toggle_switch.pack(side="left", padx=(0, 8))

        self.opt_toggle_lbl = ctk.CTkLabel(
            opt_row,
            text=i18n.t("opt_unblock_on_close"),
            text_color=theme.TEXT_WHITE,
            font=(theme.FONT_FAMILY, 12),
        )
        self.opt_toggle_lbl.pack(side="left")

        # Factory reset
        self.btn_reset = ModernButton(
            opt_row,
            text=i18n.t("btn_factory_reset"),
            command=self.do_factory_reset,
            bg_color=theme.AMBER_BG,
            hover_color=theme.AMBER_HOVER,
            text_color="#fde68a",
            font_size=8,
            width=110,
            height=32,
            radius=8,
            border_width=1,
            border_color=theme.AMBER_BORDER,
        )
        self.btn_reset.pack(side="right", padx=(8, 0))

        # Flush DNS
        self.btn_dns = ModernButton(
            opt_row,
            text=i18n.t("btn_flush_dns"),
            command=self.do_flush_dns,
            bg_color=theme.BTN_DARK,
            hover_color=theme.BTN_DARK_HOVER,
            text_color=theme.TEXT_WHITE,
            font_size=8,
            width=105,
            height=32,
            radius=8,
            border_width=1,
            border_color=theme.BORDER_HOVER,
        )
        self.btn_dns.pack(side="right")

    # -------------------------------------------------------------
    # Language Update Method
    # -------------------------------------------------------------
    def refresh_language(self):
        """Update all texts, dropdown options, and status banners when language changes."""
        self.servers_list = self.game.get_servers_list()
        combo_values = [s["title"] for s in self.servers_list]
        self.server_combo.configure(values=combo_values)

        curr_srv = self.get_current_server()
        self.selected_server_var.set(curr_srv.get("title", self.current_server_code))

        self.lbl_title.configure(text=self.game.get_display_name().upper() if not i18n.is_rtl() else self.game.get_display_name())
        self.lbl_tag.configure(text=self.game.get_tagline())

        self.select_srv_lbl.configure(text=i18n.t("select_server_lbl"))
        self._update_server_display()
        self.btn_ping.set_text(i18n.t("btn_test_ping"))

        if self.has_ping_result:
            self._apply_ping_result(self.last_ping_ms)
        else:
            self.ping_badge.configure(text=i18n.t("ping_Waiting"))

        self.game_path_lbl.configure(text=i18n.t("game_path_lbl", game=self.game.get_display_name(), exes=", ".join(self.game.exe_names)))
        self.btn_browse.set_text(i18n.t("btn_browse"))
        self.btn_deactivate.set_text(i18n.t("btn_deactivate"))

        self.warn_title_lbl.configure(text=i18n.t("game_running_warn_title", game=self.game.get_display_name()))
        self.warn_sub_lbl.configure(text=i18n.t("game_running_warn_sub"))

        self.opt_toggle_lbl.configure(text=i18n.t("opt_unblock_on_close"))
        self.btn_reset.set_text(i18n.t("btn_factory_reset"))
        self.btn_dns.set_text(i18n.t("btn_flush_dns"))

        if self.last_locked_state is not None:
            self._apply_status_banner(self.last_locked_state)
        else:
            self.status_title.configure(text=i18n.t("status_checking_title"))
            self.status_subtitle.configure(text=i18n.t("status_checking_sub"))

        if self.has_running_check:
            self._apply_running_state(self.is_game_running)
        else:
            self.game_state_lbl.configure(text=i18n.t("game_state_checking"))

    # -------------------------------------------------------------
    # Server Selection Event Handler
    # -------------------------------------------------------------
    def _on_server_selected(self, selected_title: str = ""):
        if not selected_title:
            selected_title = self.selected_server_var.get()
        matched = None
        for srv in self.servers_list:
            if srv["title"] == selected_title:
                matched = srv
                break

        if matched:
            self.current_server_code = matched["code"]
            self._update_server_display()
            self.save_target_server(self.current_server_code)
            self.logger(
                "log_server_selected",
                "info",
                game=self.game.display_name,
                game_id=self.game.game_id,
                server_code=matched["code"],
                server=matched["title"],
            )
            self.measure_ping_async()
            self.update_firewall_status()

    def _update_server_display(self):
        curr_srv = self.get_current_server()
        ping_ip = curr_srv.get("ping_ip", "")
        self.srv_detail_lbl.configure(
            text=i18n.t("server_details_lbl", code=self.current_server_code, ip=ping_ip)
        )
        short_title = self._get_short_server_name()
        self.btn_activate.set_text(i18n.t("btn_activate", server=short_title))

    # -------------------------------------------------------------
    # Logic and UI Update Methods
    # -------------------------------------------------------------
    def refresh_all(self):
        """Perform initial status check, path resolution, and ping test."""
        curr_path = self.game_path_var.get().strip()
        if not curr_path or not os.path.exists(curr_path):
            auto_found = self.game.find_game_automatically()
            if auto_found:
                self.game_path_var.set(auto_found)
                self.save_game_path(auto_found)
                self.logger(
                    "log_path_auto_found",
                    "info",
                    game=self.game.display_name,
                    path=auto_found,
                )
            else:
                self.logger(
                    "log_path_not_found",
                    "warn",
                    game=self.game.display_name,
                )

        self._update_server_display()
        self.update_firewall_status()
        self.check_game_running()
        self.measure_ping_async()

    def _safe_after(self, callback: Callable[[], None]):
        """Schedule a UI update on the main thread safely if widget still exists."""
        try:
            if self.winfo_exists():
                self.after(0, callback)
        except Exception:
            pass

    def update_firewall_status(self):
        """Query firewall rule state and update the status banner."""
        def _check():
            locked = self.game.is_locked()
            self._safe_after(lambda: self._apply_status_banner(locked))

        threading.Thread(target=_check, daemon=True).start()

    def _apply_status_banner(self, active: bool):
        self.last_locked_state = active
        srv_short = self._get_short_server_name()

        if active:
            self.status_outer.configure(fg_color=theme.GREEN_BG, border_color=theme.BORDER_ACTIVE)
            self.status_title.configure(
                text=i18n.t("status_active_title", server=srv_short, game=self.game.get_display_name()),
                text_color=theme.GREEN,
            )
            self.status_subtitle.configure(
                text=i18n.t("status_active_sub"),
                text_color="#a7f3d0",
            )
        else:
            self.status_outer.configure(fg_color=theme.BG_CARD, border_color=theme.BORDER_COLOR)
            self.status_title.configure(
                text=i18n.t("status_inactive_title", game=self.game.get_display_name()),
                text_color=theme.TEXT_WHITE,
            )
            self.status_subtitle.configure(
                text=i18n.t("status_inactive_sub"),
                text_color=theme.TEXT_MUTED,
            )

        if self.on_lock_state_changed:
            self.on_lock_state_changed(self.game.game_id, active, srv_short)

    def check_game_running(self):
        """Check if the game process is running and toggle action buttons vs warning banner."""
        def _task():
            running = self.game.is_running()
            self._safe_after(lambda: self._apply_running_state(running))

        threading.Thread(target=_task, daemon=True).start()

    def _apply_running_state(self, running: bool):
        self.has_running_check = True
        self.is_game_running = running
        if running:
            self.game_state_lbl.configure(
                text=i18n.t("game_state_running", game=self.game.get_display_name()),
                text_color=theme.AMBER,
                fg_color=theme.AMBER_BG,
            )
            self.buttons_frame.pack_forget()
            self.game_running_outer.pack(fill="x")
        else:
            self.game_state_lbl.configure(
                text=i18n.t("game_state_ready"),
                text_color=theme.GREEN,
                fg_color=theme.GREEN_BG,
            )
            self.game_running_outer.pack_forget()
            self.buttons_frame.pack(fill="x")

    def measure_ping_async(self):
        """Measure ping to the selected target server in a background thread."""
        self.has_ping_result = False
        self.ping_badge.configure(text=i18n.t("ping_Waiting"), text_color=theme.TEXT_WHITE, fg_color=theme.BG_INPUT)
        ping_ip = self.get_current_server().get("ping_ip", "")

        def _task():
            ms = network.measure_ping(ping_ip)
            self._safe_after(lambda: self._apply_ping_result(ms))

        threading.Thread(target=_task, daemon=True).start()

    def _apply_ping_result(self, ms: Optional[int]):
        self.has_ping_result = True
        self.last_ping_ms = ms
        if ms is None:
            self.ping_badge.configure(text=i18n.t("ping_failed"), text_color=theme.RED, fg_color=theme.RED_BG)
        elif ms < 60:
            self.ping_badge.configure(text=i18n.t("ping_fast", ms=ms), text_color=theme.GREEN, fg_color=theme.GREEN_BG)
        elif ms < 130:
            self.ping_badge.configure(text=i18n.t("ping_unit", ms=ms), text_color=theme.CYBER_BLUE, fg_color=theme.CYBER_BLUE_BG)
        else:
            self.ping_badge.configure(text=i18n.t("ping_unit", ms=ms), text_color=theme.AMBER, fg_color=theme.AMBER_BG)

    def browse_game_path(self):
        """Open file dialog to locate the game executable."""
        chosen = filedialog.askopenfilename(
            title=i18n.t("browse_dialog_title", game=self.game.get_display_name()),
            filetypes=[
                (f"{self.game.get_display_name()} ({', '.join(self.game.exe_names)})", " ".join(self.game.exe_names)),
                ("Executable Files", "*.exe"),
                ("All Files", "*.*"),
            ],
        )
        if chosen:
            resolved = self.game.resolve_executable_path(chosen)
            final_path = resolved if resolved else chosen
            self.game_path_var.set(final_path)
            self.save_game_path(final_path)
            self.logger(
                "log_path_updated",
                "success",
                game=self.game.display_name,
                path=final_path,
            )
            self.check_game_running()

    def _on_path_changed(self, _event=None):
        val = self.game_path_var.get().strip()
        if val:
            resolved = self.game.resolve_executable_path(val)
            if resolved and resolved != val:
                self.game_path_var.set(resolved)
                val = resolved
            self.save_game_path(val)
            self.check_game_running()

    def save_game_path(self, path: str):
        settings = config.load_settings()
        if "games" not in settings:
            settings["games"] = {}
        if self.game.game_id not in settings["games"]:
            settings["games"][self.game.game_id] = {}
        settings["games"][self.game.game_id]["game_path"] = path
        config.save_settings(settings)

    def save_target_server(self, server_code: str):
        settings = config.load_settings()
        if "games" not in settings:
            settings["games"] = {}
        if self.game.game_id not in settings["games"]:
            settings["games"][self.game.game_id] = {}
        settings["games"][self.game.game_id]["target_server"] = server_code
        config.save_settings(settings)

    def activate_lock(self):
        """Block all other servers in Windows Firewall for this game, preserving chosen target."""
        path = self.game_path_var.get().strip()
        if not path or not os.path.exists(path):
            ModernModal.show_warning(
                self.winfo_toplevel(),
                i18n.t("msg_missing_path_title"),
                i18n.t("msg_missing_path_body", game=self.game.display_name),
            )
            return

        if self.game.is_running():
            ModernModal.show_warning(
                self.winfo_toplevel(),
                i18n.t("msg_game_running_title"),
                i18n.t("msg_game_running_lock", game=self.game.display_name),
            )
            return

        srv_name = self.get_current_server().get("title", self.current_server_code)
        self.btn_activate.set_disabled(True)
        self.btn_deactivate.set_disabled(True)
        self.logger(
            "log_locking",
            "info",
            game=self.game.display_name,
            game_id=self.game.game_id,
            server_code=self.current_server_code,
            server=srv_name,
        )

        def _task():
            try:
                count = self.game.enable_lock(path, target_server_code=self.current_server_code)
                self._safe_after(lambda: self._on_activate_success(count, srv_name))
            except Exception as e:
                self._safe_after(lambda err=str(e): self._on_activate_fail(err))

        threading.Thread(target=_task, daemon=True).start()

    def _on_activate_success(self, count: int, srv_name: str):
        self.btn_activate.set_disabled(False)
        self.btn_deactivate.set_disabled(False)
        self._apply_status_banner(True)
        self.logger(
            "log_lock_success",
            "success",
            game=self.game.display_name,
            game_id=self.game.game_id,
            server_code=self.current_server_code,
            server=srv_name,
            count=count,
        )
        ModernModal.show_info(
            self.winfo_toplevel(),
            i18n.t("msg_lock_ok_title"),
            i18n.t("msg_lock_ok_body", server=self.get_current_server().get("title", srv_name)),
        )

    def _on_activate_fail(self, error_msg: str):
        self.btn_activate.set_disabled(False)
        self.btn_deactivate.set_disabled(False)
        self._apply_status_banner(False)
        self.logger("log_lock_fail", "error", err=error_msg)
        ModernModal.show_error(self.winfo_toplevel(), i18n.t("msg_lock_fail_title"), error_msg)

    def deactivate_lock(self):
        """Remove firewall block rules for this game."""
        if self.game.is_running():
            ModernModal.show_warning(
                self.winfo_toplevel(),
                i18n.t("msg_game_running_title"),
                i18n.t("msg_game_running_unlock", game=self.game.display_name),
            )
            return

        self.btn_activate.set_disabled(True)
        self.btn_deactivate.set_disabled(True)
        self.logger("log_unlocking", "info", game=self.game.display_name)

        def _task():
            try:
                self.game.disable_lock()
                self._safe_after(self._on_deactivate_success)
            except Exception as e:
                self._safe_after(lambda err=str(e): self._on_deactivate_fail(err))

        threading.Thread(target=_task, daemon=True).start()

    def _on_deactivate_success(self):
        self.btn_activate.set_disabled(False)
        self.btn_deactivate.set_disabled(False)
        self._apply_status_banner(False)
        self.logger("log_unlock_success", "success", game=self.game.display_name)
        ModernModal.show_info(
            self.winfo_toplevel(),
            i18n.t("msg_unlock_ok_title"),
            i18n.t("msg_unlock_ok_body", game=self.game.display_name),
        )

    def _on_deactivate_fail(self, err: str):
        self.btn_activate.set_disabled(False)
        self.btn_deactivate.set_disabled(False)
        self.logger("log_unlock_fail", "error", err=err)
        ModernModal.show_error(
            self.winfo_toplevel(),
            i18n.t("msg_unlock_fail_title"),
            i18n.t("msg_unlock_fail_body", err=err),
        )

    def do_flush_dns(self):
        """Flush DNS cache and log result."""
        self.logger("log_flushing_dns", "info")
        ok = network.flush_dns()
        if ok:
            self.logger("log_flush_dns_ok", "success")
            ModernModal.show_info(
                self.winfo_toplevel(),
                i18n.t("msg_dns_title"),
                i18n.t("msg_dns_body"),
            )
        else:
            self.logger("log_flush_dns_fail", "warn")

    def do_factory_reset(self):
        """Confirm and request factory reset via parent handler."""
        if ModernModal.ask_yes_no(
            self.winfo_toplevel(),
            i18n.t("msg_reset_confirm_title"),
            i18n.t("msg_reset_confirm_body"),
        ):
            if self.on_reset_requested:
                self.on_reset_requested()

    def _on_toggle_changed(self):
        settings = config.load_settings()
        settings["unblock_on_close"] = bool(self.unblock_on_close_var.get())
        config.save_settings(settings)
