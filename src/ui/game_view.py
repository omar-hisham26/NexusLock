"""
game_view.py - Content view presenting settings, server picker, and controls for a selected game
"""
import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable, Optional, Dict, Any, List

from src import config
from src.core import network
from src.games.base import BaseGame
from src.ui import theme
from src.ui.components import ModernButton, ModernToggleSwitch, create_card


class GameView(tk.Frame):
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
    ):
        super().__init__(parent, bg=theme.BG_APP)
        self.game = game
        self.logger = logger_func
        self.on_lock_state_changed = on_lock_state_changed
        self.on_reset_requested = on_reset_requested
        self.unblock_on_close_var = unblock_on_close_var

        self.game_path_var = tk.StringVar(value=initial_path)
        self.is_game_running = False

        # Servers list
        self.servers_list: List[Dict[str, Any]] = self.game.get_servers_list()
        self.current_server_code = initial_server_code or self.game.default_server_code
        if not self.game.get_server_by_code(self.current_server_code):
            self.current_server_code = self.servers_list[0]["code"] if self.servers_list else self.game.default_server_code

        # Server picker combobox variable
        curr_srv = self.game.get_server_by_code(self.current_server_code)
        init_title = curr_srv["title"] if curr_srv else self.current_server_code
        self.selected_server_var = tk.StringVar(value=init_title)

        self._init_combobox_style()
        self._build_ui()
        self.refresh_all()

    def _init_combobox_style(self):
        """Configure Dark.TCombobox styling."""
        try:
            style = ttk.Style()
            if "clam" in style.theme_names():
                style.theme_use("clam")
            style.configure(
                "Dark.TCombobox",
                fieldbackground=theme.BG_INPUT,
                background=theme.BTN_DARK,
                foreground=theme.TEXT_WHITE,
                selectbackground=theme.BTN_DARK,
                selectforeground=theme.TEXT_WHITE,
                bordercolor=theme.BORDER_COLOR,
                lightcolor=theme.BORDER_COLOR,
                darkcolor=theme.BORDER_COLOR,
                arrowcolor=theme.CYBER_BLUE,
                padding=5,
            )
            style.map(
                "Dark.TCombobox",
                fieldbackground=[("readonly", theme.BG_INPUT)],
                selectbackground=[("readonly", theme.BG_INPUT)],
                selectforeground=[("readonly", theme.TEXT_WHITE)],
            )
            self.option_add("*TCombobox*Listbox.background", theme.BG_CARD)
            self.option_add("*TCombobox*Listbox.foreground", theme.TEXT_WHITE)
            self.option_add("*TCombobox*Listbox.selectBackground", theme.BTN_DARK_HOVER)
            self.option_add("*TCombobox*Listbox.selectForeground", theme.CYBER_BLUE)
            self.option_add("*TCombobox*Listbox.font", (theme.FONT_FAMILY, 9))
        except Exception:
            pass

    def get_current_server(self) -> Dict[str, Any]:
        return self.game.get_server_by_code(self.current_server_code) or {
            "code": self.current_server_code,
            "title": self.current_server_code,
            "ping_ip": "",
        }

    def _build_ui(self):
        container = self
        # =========================================================
        # 1. Header (Game title + platform badge)
        # =========================================================
        header = tk.Frame(container, bg=theme.BG_APP)
        header.pack(fill="x", pady=(0, 10))

        title_frame = tk.Frame(header, bg=theme.BG_APP)
        title_frame.pack(side="left")

        self.lbl_title = tk.Label(
            title_frame,
            text=self.game.display_name.upper(),
            fg=theme.TEXT_WHITE,
            bg=theme.BG_APP,
            font=(theme.FONT_FAMILY, 15, "bold"),
        )
        self.lbl_title.pack(side="left")

        self.lbl_tag = tk.Label(
            title_frame,
            text=self.game.tagline,
            fg=theme.TEXT_MUTED,
            bg=theme.BG_APP,
            font=(theme.FONT_FAMILY, 9),
            padx=10,
        )
        self.lbl_tag.pack(side="left", pady=(3, 0))

        # =========================================================
        # 2. Main status banner (Locked / Unlocked)
        # =========================================================
        self.status_outer, self.status_inner = create_card(
            container, border_color=theme.BORDER_COLOR, bg_color=theme.BG_CARD, pad_x=16, pad_y=12
        )
        self.status_outer.pack(fill="x", pady=(0, 10))

        self.status_title = tk.Label(
            self.status_inner,
            text="● بفحص جدار الحماية...",
            fg=theme.TEXT_WHITE,
            bg=theme.BG_CARD,
            font=(theme.FONT_FAMILY, 11, "bold"),
            anchor="w",
        )
        self.status_title.pack(fill="x")

        self.status_subtitle = tk.Label(
            self.status_inner,
            text="تحقق من قواعد جدار حماية ويندوز",
            fg=theme.TEXT_MUTED,
            bg=theme.BG_CARD,
            font=(theme.FONT_FAMILY, 9),
            anchor="w",
        )
        self.status_subtitle.pack(fill="x", pady=(2, 0))

        # =========================================================
        # 3. Target Server Selection & live ping card
        # =========================================================
        srv_outer, srv_inner = create_card(container, pad_x=14, pad_y=12)
        srv_outer.pack(fill="x", pady=(0, 10))

        srv_top = tk.Frame(srv_inner, bg=theme.BG_CARD)
        srv_top.pack(fill="x")

        # Left: Server Selector Label & Dropdown
        srv_info = tk.Frame(srv_top, bg=theme.BG_CARD)
        srv_info.pack(side="left", fill="x", expand=True)

        sel_header = tk.Frame(srv_info, bg=theme.BG_CARD)
        sel_header.pack(fill="x", pady=(0, 4))

        tk.Label(
            sel_header,
            text="🎯 اختر السيرفر المطلوب تثبيته:",
            fg=theme.TEXT_WHITE,
            bg=theme.BG_CARD,
            font=(theme.FONT_FAMILY, 10, "bold"),
            anchor="w",
        ).pack(side="left")

        # Dropdown combobox
        dropdown_frame = tk.Frame(srv_info, bg=theme.BORDER_COLOR, padx=1, pady=1)
        dropdown_frame.pack(fill="x", pady=(0, 4))

        combo_values = [s["title"] for s in self.servers_list]
        self.server_combo = ttk.Combobox(
            dropdown_frame,
            textvariable=self.selected_server_var,
            values=combo_values,
            state="readonly",
            style="Dark.TCombobox",
            font=(theme.FONT_FAMILY, 9),
        )
        self.server_combo.pack(fill="x")
        self.server_combo.bind("<<ComboboxSelected>>", self._on_server_selected)

        # Server technical details label
        self.srv_detail_lbl = tk.Label(
            srv_info,
            text=f"رمز السيرفر: {self.current_server_code}   •   IP الفحص: {self.get_current_server().get('ping_ip', '')}",
            fg=theme.TEXT_MUTED,
            bg=theme.BG_CARD,
            font=(theme.FONT_FAMILY, 8),
            anchor="w",
        )
        self.srv_detail_lbl.pack(anchor="w")

        # Right: Ping badge and refresh button
        ping_box = tk.Frame(srv_top, bg=theme.BG_CARD)
        ping_box.pack(side="right", padx=(12, 0))

        self.ping_badge = tk.Label(
            ping_box,
            text="... ms",
            fg=theme.TEXT_WHITE,
            bg=theme.BG_INPUT,
            font=(theme.FONT_FAMILY, 9, "bold"),
            padx=10,
            pady=4,
        )
        self.ping_badge.pack(side="left", padx=(0, 8))

        self.btn_ping = ModernButton(
            ping_box,
            text="🔄 فحص البنق",
            command=self.measure_ping_async,
            bg_color=theme.BTN_DARK,
            hover_color=theme.BTN_DARK_HOVER,
            font_size=8,
            width=95,
            height=30,
            radius=6,
            parent_bg=theme.BG_CARD,
        )
        self.btn_ping.pack(side="left")

        # =========================================================
        # 4. Game path & live process monitor card
        # =========================================================
        game_outer, game_inner = create_card(container, pad_x=14, pad_y=10)
        game_outer.pack(fill="x", pady=(0, 10))

        game_head = tk.Frame(game_inner, bg=theme.BG_CARD)
        game_head.pack(fill="x", pady=(0, 6))

        tk.Label(
            game_head,
            text=f"مسار اللعبة ({', '.join(self.game.exe_names)})",
            fg=theme.TEXT_WHITE,
            bg=theme.BG_CARD,
            font=(theme.FONT_FAMILY, 9, "bold"),
        ).pack(side="left")

        self.game_state_lbl = tk.Label(
            game_head,
            text="○ بفحص حالة اللعبة...",
            fg=theme.TEXT_MUTED,
            bg=theme.BG_CARD,
            font=(theme.FONT_FAMILY, 8, "bold"),
        )
        self.game_state_lbl.pack(side="right")

        path_row = tk.Frame(game_inner, bg=theme.BG_CARD)
        path_row.pack(fill="x")

        entry_border = tk.Frame(path_row, bg=theme.BORDER_COLOR, padx=1, pady=1)
        entry_border.pack(side="left", fill="x", expand=True, padx=(0, 8))

        self.path_entry = tk.Entry(
            entry_border,
            textvariable=self.game_path_var,
            bg=theme.BG_INPUT,
            fg=theme.TEXT_WHITE,
            insertbackground=theme.TEXT_WHITE,
            relief="flat",
            bd=5,
            font=(theme.FONT_MONO, 8),
        )
        self.path_entry.pack(fill="x")
        self.path_entry.bind("<FocusOut>", self._on_path_changed)
        self.path_entry.bind("<Return>", self._on_path_changed)

        self.btn_browse = ModernButton(
            path_row,
            text="📂 تحديد الملف",
            command=self.browse_game_path,
            bg_color=theme.BTN_DARK,
            hover_color=theme.BTN_DARK_HOVER,
            font_size=8,
            width=95,
            height=30,
            radius=6,
            parent_bg=theme.BG_CARD,
        )
        self.btn_browse.pack(side="right")

        # =========================================================
        # 5. Action Buttons / Game Running Warning
        # =========================================================
        self.actions_container = tk.Frame(container, bg=theme.BG_APP)
        self.actions_container.pack(fill="x", pady=(0, 10))

        self.buttons_frame = tk.Frame(self.actions_container, bg=theme.BG_APP)
        self.buttons_frame.pack(fill="x")

        srv_short = self.get_current_server().get("title", self.current_server_code).split("(")[0].strip()
        self.btn_activate = ModernButton(
            self.buttons_frame,
            text=f"🛡️ تثبيت سيرفر {srv_short}\n(وحظر باقي السيرفرات الأخرى)",
            command=self.activate_lock,
            bg_color=theme.GREEN,
            hover_color=theme.GREEN_HOVER,
            text_color="#ffffff",
            font_size=9,
            height=46,
            radius=8,
            parent_bg=theme.BG_APP,
        )
        self.btn_activate.pack(side="left", fill="x", expand=True, padx=(0, 6))

        self.btn_deactivate = ModernButton(
            self.buttons_frame,
            text="🔓 فك البلوك\n(فتح جميع السيرفرات عالمياً)",
            command=self.deactivate_lock,
            bg_color=theme.RED,
            hover_color=theme.RED_HOVER,
            text_color="#ffffff",
            font_size=9,
            height=46,
            radius=8,
            parent_bg=theme.BG_APP,
        )
        self.btn_deactivate.pack(side="right", fill="x", expand=True, padx=(6, 0))

        # Warning card shown when game is currently running
        self.game_running_outer, self.game_running_inner = create_card(
            self.actions_container,
            border_color=theme.AMBER,
            bg_color=theme.AMBER_BG,
            pad_x=14,
            pad_y=10,
        )

        tk.Label(
            self.game_running_inner,
            text=f"⚠️ {self.game.display_name} شغال حالياً على جهازك!",
            fg="#fde68a",
            bg=theme.AMBER_BG,
            font=(theme.FONT_FAMILY, 9, "bold"),
            anchor="center",
        ).pack(fill="x")

        tk.Label(
            self.game_running_inner,
            text="يجب إغلاق اللعبة أولاً قبل تفعيل الحظر أو فكه لتطبيق قواعد جدار الحماية.",
            fg="#fef3c7",
            bg=theme.AMBER_BG,
            font=(theme.FONT_FAMILY, 8),
            anchor="center",
        ).pack(fill="x", pady=(2, 0))

        # =========================================================
        # 6. Options & Maintenance row (Toggle, Flush DNS, Reset)
        # =========================================================
        opt_outer, opt_inner = create_card(container, pad_x=12, pad_y=8)
        opt_outer.pack(fill="x", pady=(0, 10))

        opt_row = tk.Frame(opt_inner, bg=theme.BG_CARD)
        opt_row.pack(fill="x")

        self.toggle_switch = ModernToggleSwitch(
            opt_row,
            variable=self.unblock_on_close_var,
            command=self._on_toggle_changed,
            parent_bg=theme.BG_CARD,
        )
        self.toggle_switch.pack(side="left", padx=(0, 8))

        tk.Label(
            opt_row,
            text="فك التبليك تلقائياً عند إغلاق البرنامج",
            fg=theme.TEXT_WHITE,
            bg=theme.BG_CARD,
            font=(theme.FONT_FAMILY, 8),
        ).pack(side="left")

        # Factory reset
        self.btn_reset = ModernButton(
            opt_row,
            text="⚙️ ضبط المصنع",
            command=self.do_factory_reset,
            bg_color=theme.AMBER_BG,
            hover_color=theme.AMBER_HOVER,
            text_color="#fde68a",
            font_size=8,
            width=95,
            height=28,
            radius=6,
            parent_bg=theme.BG_CARD,
        )
        self.btn_reset.pack(side="right", padx=(6, 0))

        # Flush DNS
        self.btn_dns = ModernButton(
            opt_row,
            text="🌐 تنظيف DNS",
            command=self.do_flush_dns,
            bg_color=theme.BTN_DARK,
            hover_color=theme.BTN_DARK_HOVER,
            text_color=theme.TEXT_WHITE,
            font_size=8,
            width=90,
            height=28,
            radius=6,
            parent_bg=theme.BG_CARD,
        )
        self.btn_dns.pack(side="right")

    # -------------------------------------------------------------
    # Server Selection Event Handler
    # -------------------------------------------------------------
    def _on_server_selected(self, _event=None):
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
            self.logger(f"تم اختيار سيرفر الوجهة لـ {self.game.display_name}: {matched['title']}", "info")
            self.measure_ping_async()
            self.update_firewall_status()

    def _update_server_display(self):
        curr_srv = self.get_current_server()
        ping_ip = curr_srv.get("ping_ip", "")
        self.srv_detail_lbl.configure(
            text=f"رمز السيرفر: {self.current_server_code}   •   IP الفحص: {ping_ip}"
        )
        short_title = curr_srv.get("title", self.current_server_code).split("(")[0].strip()
        self.btn_activate.set_text(f"🛡️ تثبيت سيرفر {short_title}\n(وحظر باقي السيرفرات الأخرى)")

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
                self.logger(f"تم اكتشاف مسار {self.game.display_name} تلقائياً:\n  {auto_found}", "info")
            else:
                self.logger(f"لم يتم العثور على مسار {self.game.display_name}، يرجى تحديده يدوياً.", "warn")

        self._update_server_display()
        self.update_firewall_status()
        self.check_game_running()
        self.measure_ping_async()

    def update_firewall_status(self):
        """Query firewall rule state and update the status banner."""
        def _check():
            locked = self.game.is_locked()
            self.after(0, lambda: self._apply_status_banner(locked))

        threading.Thread(target=_check, daemon=True).start()

    def _apply_status_banner(self, active: bool):
        curr_srv = self.get_current_server()
        srv_name = curr_srv.get("title", self.current_server_code)
        srv_short = srv_name.split("(")[0].strip()

        if active:
            self.status_outer.configure(bg=theme.BORDER_ACTIVE)
            self.status_inner.configure(bg=theme.GREEN_BG)
            self.status_title.configure(
                text=f"● شغال: متصل بسيرفر {srv_short} فقط ({self.game.display_name})",
                fg=theme.GREEN,
                bg=theme.GREEN_BG,
            )
            self.status_subtitle.configure(
                text="جميع السيرفرات الأخرى تم حظرها بنجاح في جدار الحماية",
                fg="#a7f3d0",
                bg=theme.GREEN_BG,
            )
        else:
            self.status_outer.configure(bg=theme.BORDER_COLOR)
            self.status_inner.configure(bg=theme.BG_CARD)
            self.status_title.configure(
                text=f"● مطفأ: جميع سيرفرات {self.game.display_name} مفتوحة",
                fg=theme.TEXT_WHITE,
                bg=theme.BG_CARD,
            )
            self.status_subtitle.configure(
                text="لا توجد قواعد حظر نشطة، البحث سيتصل بأي سيرفر عالمي",
                fg=theme.TEXT_MUTED,
                bg=theme.BG_CARD,
            )

        if self.on_lock_state_changed:
            self.on_lock_state_changed(self.game.game_id, active, srv_short)

    def check_game_running(self):
        """Check if the game process is running and toggle action buttons vs warning banner."""
        def _task():
            running = self.game.is_running()
            self.after(0, lambda: self._apply_running_state(running))

        threading.Thread(target=_task, daemon=True).start()

    def _apply_running_state(self, running: bool):
        self.is_game_running = running
        if running:
            self.game_state_lbl.configure(text=f"● {self.game.display_name} شغالة حالياً", fg=theme.AMBER)
            self.buttons_frame.pack_forget()
            self.game_running_outer.pack(fill="x")
        else:
            self.game_state_lbl.configure(text="○ اللعبة طافية (جاهز)", fg=theme.GREEN)
            self.game_running_outer.pack_forget()
            self.buttons_frame.pack(fill="x")

    def measure_ping_async(self):
        """Measure ping to the selected target server in a background thread."""
        self.ping_badge.configure(text="... ms", fg=theme.TEXT_WHITE, bg=theme.BG_INPUT)
        ping_ip = self.get_current_server().get("ping_ip", "")

        def _task():
            ms = network.measure_ping(ping_ip)
            self.after(0, lambda: self._apply_ping_result(ms))

        threading.Thread(target=_task, daemon=True).start()

    def _apply_ping_result(self, ms: Optional[int]):
        if ms is None:
            self.ping_badge.configure(text="-- ms (تعذر)", fg=theme.RED, bg=theme.RED_BG)
        elif ms < 60:
            self.ping_badge.configure(text=f"⚡ {ms} ms", fg=theme.GREEN, bg=theme.GREEN_BG)
        elif ms < 130:
            self.ping_badge.configure(text=f"{ms} ms", fg=theme.CYBER_BLUE, bg="#0c2336")
        else:
            self.ping_badge.configure(text=f"{ms} ms", fg=theme.AMBER, bg=theme.AMBER_BG)

    def browse_game_path(self):
        """Open file dialog to locate the game executable."""
        candidates = ";".join(f"*{os.path.splitext(e)[1]}" for e in self.game.exe_names)
        chosen = filedialog.askopenfilename(
            title=f"حدد ملف تشغيل {self.game.display_name}",
            filetypes=[
                (f"{self.game.display_name} ({', '.join(self.game.exe_names)})", " ".join(self.game.exe_names)),
                ("Executable Files", "*.exe"),
                ("All Files", "*.*"),
            ],
        )
        if chosen:
            resolved = self.game.resolve_executable_path(chosen)
            final_path = resolved if resolved else chosen
            self.game_path_var.set(final_path)
            self.save_game_path(final_path)
            self.logger(f"تم تحديث مسار {self.game.display_name}:\n  {final_path}", "success")
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
            messagebox.showwarning("مسار غير محدد", f"يرجى تحديد مسار {self.game.display_name} أولاً عبر زر اختيار الملف.")
            return

        if self.game.is_running():
            messagebox.showwarning("اللعبة قيد التشغيل", f"يرجى إغلاق {self.game.display_name} أولاً لتطبيق التبليك.")
            return

        srv_name = self.get_current_server().get("title", self.current_server_code)
        self.btn_activate.set_disabled(True)
        self.btn_deactivate.set_disabled(True)
        self.logger(f"جاري تبليك السيرفرات لـ {self.game.display_name} وتثبيت سيرفر: {srv_name}...", "info")

        def _task():
            try:
                count = self.game.enable_lock(path, target_server_code=self.current_server_code)
                self.after(
                    0,
                    lambda: self._on_activate_success(count, srv_name),
                )
            except Exception as e:
                self.after(
                    0,
                    lambda err=str(e): self._on_activate_fail(err),
                )

        threading.Thread(target=_task, daemon=True).start()

    def _on_activate_success(self, count: int, srv_name: str):
        self.btn_activate.set_disabled(False)
        self.btn_deactivate.set_disabled(False)
        self._apply_status_banner(True)
        self.logger(f"✅ تم تفعيل الحظر لـ {self.game.display_name} بنجاح! تم تثبيت: {srv_name} ({count} عنوان/نطاق محظور)", "success")
        messagebox.showinfo("تم التبليك بنجاح", f"تم حظر جميع السيرفرات الأخرى بنجاح!\nأنت الآن متصل بسيرفر:\n{srv_name}")

    def _on_activate_fail(self, error_msg: str):
        self.btn_activate.set_disabled(False)
        self.btn_deactivate.set_disabled(False)
        self._apply_status_banner(False)
        self.logger(f"❌ خطأ أثناء تطبيق الحظر: {error_msg}", "error")
        messagebox.showerror("فشل التبليك", error_msg)

    def deactivate_lock(self):
        """Remove firewall block rules for this game."""
        if self.game.is_running():
            messagebox.showwarning("اللعبة قيد التشغيل", f"يرجى إغلاق {self.game.display_name} أولاً قبل فك البلوك.")
            return

        self.btn_activate.set_disabled(True)
        self.btn_deactivate.set_disabled(True)
        self.logger(f"جاري فك البلوك عن سيرفرات {self.game.display_name}...", "info")

        def _task():
            try:
                self.game.disable_lock()
                self.after(0, self._on_deactivate_success)
            except Exception as e:
                self.after(0, lambda err=str(e): self._on_deactivate_fail(err))

        threading.Thread(target=_task, daemon=True).start()

    def _on_deactivate_success(self):
        self.btn_activate.set_disabled(False)
        self.btn_deactivate.set_disabled(False)
        self._apply_status_banner(False)
        self.logger(f"🔓 تم فك البلوك عن سيرفرات {self.game.display_name} بنجاح.", "success")
        messagebox.showinfo("تم فك البلوك", f"تم فتح جميع السيرفرات بنجاح لـ {self.game.display_name}.\nيمكنك الآن اللعب في أي سيرفر.")

    def _on_deactivate_fail(self, err: str):
        self.btn_activate.set_disabled(False)
        self.btn_deactivate.set_disabled(False)
        self.logger(f"❌ فشل فك البلوك: {err}", "error")
        messagebox.showerror("خطأ", f"حدث خطأ أثناء فك البلوك:\n{err}")

    def do_flush_dns(self):
        """Flush DNS cache and log result."""
        self.logger("جاري تنظيف كاش الـ DNS (Flush DNS)...", "info")
        ok = network.flush_dns()
        if ok:
            self.logger("✅ تم تنظيف كاش الـ DNS بنجاح.", "success")
            messagebox.showinfo("تنظيف DNS", "تم تنظيف كاش الـ DNS بنجاح!")
        else:
            self.logger("⚠️ تعذر تنظيف DNS.", "warn")

    def do_factory_reset(self):
        """Confirm and request factory reset via parent handler."""
        if messagebox.askyesno("تأكيد ضبط المصنع", "هل أنت متأكد من رغبتك في حذف جميع القواعد واستعادة الإعدادات الأصلية؟"):
            if self.on_reset_requested:
                self.on_reset_requested()

    def _on_toggle_changed(self):
        settings = config.load_settings()
        settings["unblock_on_close"] = bool(self.unblock_on_close_var.get())
        config.save_settings(settings)
