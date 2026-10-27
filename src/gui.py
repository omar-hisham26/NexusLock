import ctypes
import os
import threading
import time
import tkinter as tk
from tkinter import filedialog, messagebox

try:
    from src import firewall
except ImportError:
    import firewall

# -------------------------------------------------------------
# Color palette (Modern Cyber Dark)
# -------------------------------------------------------------
BG_MAIN = "#0b0e14"         # Main window background
BG_CARD = "#131824"         # Card background
BG_INPUT = "#0d111a"        # Input fields and log background
BORDER_COLOR = "#21293d"    # Card border color
BORDER_ACTIVE = "#10b981"   # Card border when locked to Netherlands

TEXT_WHITE = "#f8fafc"      # Main text
TEXT_MUTED = "#8b98b1"      # Subtitle / secondary text
TEXT_DIM = "#56637a"        # Disabled / dim text

GREEN = "#10b981"           # Emerald green
GREEN_HOVER = "#059669"
GREEN_BG = "#07261d"

RED = "#ef4444"             # Red for inactive / unlock
RED_HOVER = "#dc2626"
RED_BG = "#280a0e"          # Red banner background when unlocked

AMBER = "#f59e0b"           # Warning / amber
AMBER_BG = "#2b1d08"
AMBER_HOVER = "#d97706"

BTN_DARK = "#1e2638"        # Dark secondary button
BTN_DARK_HOVER = "#2a354d"

CYBER_BLUE = "#38bdf8"      # Battle.net accent
TIKTOK_PINK = "#f43f5e"     # TikTok accent

FONT_FAMILY = "Segoe UI"


# -------------------------------------------------------------
# High-DPI support and dark titlebar for Windows 10/11
# -------------------------------------------------------------
def enable_high_dpi():
    """Make fonts and UI sharp on high-resolution screens"""
    if os.name == "nt":
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass


def apply_dark_titlebar(window):
    """Enable dark titlebar on Windows 10 and 11"""
    if os.name != "nt":
        return
    try:
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        value = ctypes.c_int(2)
        # 20 = DWMWA_USE_IMMERSIVE_DARK_MODE on modern Windows
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(value), ctypes.sizeof(value))
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(value), ctypes.sizeof(value))
    except Exception:
        pass


# -------------------------------------------------------------
# Custom UI elements (rounded corners and hover effects)
# -------------------------------------------------------------
def draw_rounded_rect(canvas, x1, y1, x2, y2, radius, **kwargs):
    """Draw a smooth rounded rectangle inside a Canvas"""
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, **kwargs)


class ModernButton(tk.Canvas):
    """Modern button with rounded corners and hover effects"""

    def __init__(
        self,
        parent,
        text,
        command=None,
        bg_color=BTN_DARK,
        hover_color=BTN_DARK_HOVER,
        text_color=TEXT_WHITE,
        font_size=10,
        bold=True,
        height=40,
        width=130,
        radius=10,
        parent_bg=BG_MAIN,
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            bg=parent_bg,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.text = text
        self.command = command
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.radius = radius
        self.is_disabled = False
        self.current_bg = bg_color
        weight = "bold" if bold else "normal"
        self.font_spec = (FONT_FAMILY, font_size, weight)

        self.bind("<Configure>", self._redraw)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonRelease-1>", self._on_click)

    def _redraw(self, _event=None):
        self.delete("all")
        w = max(self.winfo_width(), 20)
        h = max(self.winfo_height(), 20)
        fill = "#1a2030" if self.is_disabled else self.current_bg
        fg = TEXT_DIM if self.is_disabled else self.text_color
        draw_rounded_rect(self, 1, 1, w - 1, h - 1, self.radius, fill=fill, outline="")
        self.create_text(w / 2, h / 2, text=self.text, fill=fg, font=self.font_spec)

    def _on_enter(self, _event=None):
        if not self.is_disabled:
            self.current_bg = self.hover_color
            self._redraw()

    def _on_leave(self, _event=None):
        if not self.is_disabled:
            self.current_bg = self.bg_color
            self._redraw()

    def _on_click(self, _event=None):
        if not self.is_disabled and self.command:
            self.command()

    def set_disabled(self, disabled: bool):
        self.is_disabled = disabled
        self.configure(cursor="arrow" if disabled else "hand2")
        self.current_bg = self.bg_color
        self._redraw()


class ModernToggleSwitch(tk.Canvas):
    """Modern toggle switch instead of standard checkbox"""

    def __init__(self, parent, variable: tk.BooleanVar, command=None, parent_bg=BG_CARD):
        super().__init__(
            parent,
            width=46,
            height=24,
            bg=parent_bg,
            highlightthickness=0,
            bd=0,
            cursor="hand2",
        )
        self.variable = variable
        self.command = command
        self.bind("<ButtonRelease-1>", self.toggle)
        self.variable.trace_add("write", lambda *_: self.redraw())
        self.redraw()

    def toggle(self, _event=None):
        self.variable.set(not self.variable.get())
        if self.command:
            self.command()

    def redraw(self):
        self.delete("all")
        on = self.variable.get()
        track_color = GREEN if on else "#283246"
        draw_rounded_rect(self, 2, 2, 44, 22, 10, fill=track_color, outline="")
        knob_x = 32 if on else 14
        self.create_oval(knob_x - 7, 5, knob_x + 7, 19, fill="#ffffff", outline="")


def create_card(parent, border_color=BORDER_COLOR, bg_color=BG_CARD, pad_x=16, pad_y=14):
    """Create a modern card container with a 1px border"""
    outer = tk.Frame(parent, bg=border_color, padx=1, pady=1)
    inner = tk.Frame(outer, bg=bg_color, padx=pad_x, pady=pad_y)
    inner.pack(fill="both", expand=True)
    return outer, inner


# -------------------------------------------------------------
# Main application window (NetherWatch GUI)
# -------------------------------------------------------------
class NetherWatchGUI:
    def __init__(self):
        enable_high_dpi()

        self.root = tk.Tk()
        self.root.title("NetherWatch — تبليك السيرفرات ")
        self.root.geometry("680x760")
        self.root.minsize(620, 710)
        self.root.configure(bg=BG_MAIN)
        apply_dark_titlebar(self.root)

        # Set window icon if available
        icon_path = firewall.BUNDLE_DIR / "assets" / "icon.ico"
        if not icon_path.exists():
            icon_path = firewall.CURRENT_DIR / "assets" / "icon.ico"
        if icon_path.exists():
            try:
                self.root.iconbitmap(str(icon_path))
            except Exception:
                pass

        # Load saved settings
        self.settings = firewall.load_saved_settings()

        # State variables
        self.game_path_var = tk.StringVar(value=self.settings.get("game_path", ""))
        self.unblock_on_close_var = tk.BooleanVar(value=self.settings.get("unblock_on_close", False))
        self._is_game_running = False

        # Build UI layout
        self._build_ui()

        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close_window)

        # Run initial checks
        self.root.after(150, self.initial_setup)

    def _build_ui(self):
        container = tk.Frame(self.root, bg=BG_MAIN, padx=22, pady=18)
        container.pack(fill="both", expand=True)

        # =========================================================
        # 1. Header (Brand title + Admin rights badge)
        # =========================================================
        header = tk.Frame(container, bg=BG_MAIN)
        header.pack(fill="x", pady=(0, 14))

        brand_frame = tk.Frame(header, bg=BG_MAIN)
        brand_frame.pack(side="left")

        tk.Label(
            brand_frame,
            text="⚡ NETHERWATCH",
            fg=TEXT_WHITE,
            bg=BG_MAIN,
            font=(FONT_FAMILY, 16, "bold"),
        ).pack(side="left")

        tk.Label(
            brand_frame,
            text="OVERWATCH SERVER LOCK",
            fg=GREEN,
            bg=BG_MAIN,
            font=(FONT_FAMILY, 8, "bold"),
            padx=10,
        ).pack(side="left", pady=(4, 0))

        # Admin status badge
        admin_ok = firewall.is_admin()
        admin_text = "🛡️ صلاحية مسؤول مفعلة" if admin_ok else "⚠️ يعمل بدون صلاحية مسؤول"
        admin_fg = GREEN if admin_ok else AMBER
        admin_bg = GREEN_BG if admin_ok else AMBER_BG

        tk.Label(
            header,
            text=admin_text,
            fg=admin_fg,
            bg=admin_bg,
            font=(FONT_FAMILY, 8, "bold"),
            padx=10,
            pady=4,
        ).pack(side="right")

        # =========================================================
        # 2. Main status banner (Locked / Unlocked indicator)
        # =========================================================
        self.status_outer, self.status_inner = create_card(
            container, border_color=BORDER_COLOR, bg_color=BG_CARD, pad_x=18, pad_y=14
        )
        self.status_outer.pack(fill="x", pady=(0, 12))

        self.status_title = tk.Label(
            self.status_inner,
            text="●  بفحص لك جدار الحماية...",
            fg=TEXT_WHITE,
            bg=BG_CARD,
            font=(FONT_FAMILY, 12, "bold"),
            anchor="w",
        )
        self.status_title.pack(fill="x")

        self.status_subtitle = tk.Label(
            self.status_inner,
            text="  بتحقق من قواعد الاتصال في نظام ويندوز",
            fg=TEXT_MUTED,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9),
            anchor="w",
        )
        self.status_subtitle.pack(fill="x", pady=(3, 0))

        # =========================================================
        # 3. Netherlands server & live ping card
        # =========================================================
        srv_outer, srv_inner = create_card(container)
        srv_outer.pack(fill="x", pady=(0, 12))

        srv_top = tk.Frame(srv_inner, bg=BG_CARD)
        srv_top.pack(fill="x")

        # Server info on the left
        srv_info = tk.Frame(srv_top, bg=BG_CARD)
        srv_info.pack(side="left")

        tk.Label(
            srv_info,
            text="🇳🇱  سيرفر هولندا — أمستردام",
            fg=TEXT_WHITE,
            bg=BG_CARD,
            font=(FONT_FAMILY, 11, "bold"),
            anchor="w",
        ).pack(anchor="w")

        tk.Label(
            srv_info,
            text=f"Server: ams1   •   IP: {firewall.NETHERLANDS_SERVER_IP}",
            fg=TEXT_MUTED,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9),
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        # Ping badge and refresh button on the right
        ping_box = tk.Frame(srv_top, bg=BG_CARD)
        ping_box.pack(side="right")

        self.ping_badge = tk.Label(
            ping_box,
            text="... ms",
            fg=TEXT_WHITE,
            bg=BG_INPUT,
            font=(FONT_FAMILY, 10, "bold"),
            padx=12,
            pady=6,
        )
        self.ping_badge.pack(side="left", padx=(0, 8))

        self.btn_ping = ModernButton(
            ping_box,
            text="🔄 فحص البنق",
            command=self.measure_ping,
            bg_color=BTN_DARK,
            hover_color=BTN_DARK_HOVER,
            font_size=9,
            width=105,
            height=34,
            radius=8,
            parent_bg=BG_CARD,
        )
        self.btn_ping.pack(side="left")

        # =========================================================
        # 4. Game path & process status card
        # =========================================================
        game_outer, game_inner = create_card(container)
        game_outer.pack(fill="x", pady=(0, 14))

        game_head = tk.Frame(game_inner, bg=BG_CARD)
        game_head.pack(fill="x", pady=(0, 8))

        tk.Label(
            game_head,
            text="مسار ملف اللعبة: Overwatch.exe",
            fg=TEXT_WHITE,
            bg=BG_CARD,
            font=(FONT_FAMILY, 10, "bold"),
        ).pack(side="left")

        self.game_state_lbl = tk.Label(
            game_head,
            text="○ بفحص حالة اللعبة...",
            fg=TEXT_MUTED,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold"),
        )
        self.game_state_lbl.pack(side="right")

        path_row = tk.Frame(game_inner, bg=BG_CARD)
        path_row.pack(fill="x")

        # Input field with styled border
        entry_border = tk.Frame(path_row, bg=BORDER_COLOR, padx=1, pady=1)
        entry_border.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.path_entry = tk.Entry(
            entry_border,
            textvariable=self.game_path_var,
            bg=BG_INPUT,
            fg=TEXT_WHITE,
            insertbackground=TEXT_WHITE,
            relief="flat",
            bd=6,
            font=("Consolas", 9),
        )
        self.path_entry.pack(fill="x")

        self.btn_browse = ModernButton(
            path_row,
            text="📂 اختار الملف",
            command=self.browse_game_path,
            bg_color=BTN_DARK,
            hover_color=BTN_DARK_HOVER,
            font_size=9,
            width=110,
            height=34,
            radius=8,
            parent_bg=BG_CARD,
        )
        self.btn_browse.pack(side="right")

        # =========================================================
        # 5. Primary action buttons & Game-running notice
        # =========================================================
        self.actions_container = tk.Frame(container, bg=BG_MAIN)
        self.actions_container.pack(fill="x", pady=(0, 14))

        # Buttons row (visible when Overwatch is not running)
        self.buttons_frame = tk.Frame(self.actions_container, bg=BG_MAIN)
        self.buttons_frame.pack(fill="x")

        self.btn_activate = ModernButton(
            self.buttons_frame,
            text="🛡️ تبليك السيرفرات\n(سيرفر هولندا بيكون شغال)",
            command=self.activate_lock,
            bg_color=GREEN,
            hover_color=GREEN_HOVER,
            text_color="#ffffff",
            font_size=10,
            height=52,
            radius=10,
            parent_bg=BG_MAIN,
        )
        self.btn_activate.pack(side="left", fill="x", expand=True, padx=(0, 7))

        self.btn_deactivate = ModernButton(
            self.buttons_frame,
            text="🔓 فك البلوك\n(فتح جميع السيرفرات)",
            command=self.deactivate_lock,
            bg_color=RED,
            hover_color=RED_HOVER,
            text_color="#ffffff",
            font_size=10,
            height=52,
            radius=10,
            parent_bg=BG_MAIN,
        )
        self.btn_deactivate.pack(side="right", fill="x", expand=True, padx=(7, 0))

        # Warning card (shown instead of buttons when Overwatch is running)
        self.game_running_outer, self.game_running_inner = create_card(
            self.actions_container,
            border_color=AMBER,
            bg_color=AMBER_BG,
            pad_x=16,
            pad_y=12,
        )

        tk.Label(
            self.game_running_inner,
            text="⚠️  اللعبه شغاله حالياً في جهازك!",
            fg="#fde68a",
            bg=AMBER_BG,
            font=(FONT_FAMILY, 10, "bold"),
            anchor="center",
        ).pack(fill="x")

        tk.Label(
            self.game_running_inner,
            text="لازم تطفي اللعبه أولاً، بعدين تقدر تبلك السيرفرات أو تفك البلوك .",
            fg="#fef3c7",
            bg=AMBER_BG,
            font=(FONT_FAMILY, 9),
            anchor="center",
        ).pack(fill="x", pady=(3, 0))

        # =========================================================
        # 6. Settings & maintenance card (Toggle switch, DNS flush, reset)
        # =========================================================
        opt_outer, opt_inner = create_card(container, pad_x=14, pad_y=10)
        opt_outer.pack(fill="x", pady=(0, 14))

        opt_row = tk.Frame(opt_inner, bg=BG_CARD)
        opt_row.pack(fill="x")

        # Toggle switch for auto-unblock on exit
        self.toggle_switch = ModernToggleSwitch(
            opt_row,
            variable=self.unblock_on_close_var,
            command=self.on_toggle_changed,
            parent_bg=BG_CARD,
        )
        self.toggle_switch.pack(side="left", padx=(0, 10))

        tk.Label(
            opt_row,
            text="فك التبليك تلقائياً اذا قفلت البرنامج",
            fg=TEXT_WHITE,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9),
        ).pack(side="left")

        # Factory reset button
        self.btn_reset = ModernButton(
            opt_row,
            text="⚙️ ضبط المصنع",
            command=self.reset_to_default,
            bg_color=AMBER_BG,
            hover_color=AMBER_HOVER,
            text_color="#fde68a",
            font_size=9,
            width=110,
            height=32,
            radius=8,
            parent_bg=BG_CARD,
        )
        self.btn_reset.pack(side="right", padx=(8, 0))

        # Flush DNS button
        self.btn_dns = ModernButton(
            opt_row,
            text="🌐 تنظيف DNS",
            command=self.do_flush_dns,
            bg_color=BTN_DARK,
            hover_color=BTN_DARK_HOVER,
            text_color=TEXT_WHITE,
            font_size=9,
            width=100,
            height=32,
            radius=8,
            parent_bg=BG_CARD,
        )
        self.btn_dns.pack(side="right")

        # =========================================================
        # 7. Terminal activity log
        # =========================================================
        log_header = tk.Frame(container, bg=BG_MAIN)
        log_header.pack(fill="x", pady=(0, 4))

        tk.Label(
            log_header,
            text="سجل العمليات المباشر",
            fg=TEXT_MUTED,
            bg=BG_MAIN,
            font=(FONT_FAMILY, 9, "bold"),
        ).pack(side="right")

        log_outer, log_inner = create_card(container, bg_color=BG_INPUT, pad_x=12, pad_y=10)
        log_outer.pack(fill="both", expand=True)

        self.log_box = tk.Text(
            log_inner,
            bg=BG_INPUT,
            fg="#cbd5e1",
            bd=0,
            highlightthickness=0,
            font=(FONT_FAMILY, 9),
            wrap="word",
            state="disabled",
            height=5,
        )
        self.log_box.pack(fill="both", expand=True)

        # Style log tags and keep text aligned cleanly
        self.log_box.tag_config("success", foreground="#34d399", justify="right")
        self.log_box.tag_config("error", foreground="#f87171", justify="right")
        self.log_box.tag_config("warn", foreground="#fbbf24", justify="right")
        self.log_box.tag_config("info", foreground="#cbd5e1", justify="right")

        # =========================================================
        # 8. Developer / Socials footer
        # =========================================================
        footer = tk.Frame(container, bg=BG_MAIN)
        footer.pack(fill="x", pady=(10, 0))

        dev_outer, dev_inner = create_card(footer, border_color=BORDER_COLOR, bg_color=BG_CARD, pad_x=14, pad_y=8)
        dev_outer.pack(fill="x")

        # Developer label on the right
        tk.Label(
            dev_inner,
            text="المطور",
            fg=TEXT_MUTED,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold"),
        ).pack(side="right", padx=(10, 0))

        # Battle.net account (platform on left, username on right)
        bnet_frame = tk.Frame(dev_inner, bg=BG_CARD, cursor="hand2")
        bnet_frame.pack(side="right", padx=(16, 0))

        tk.Label(
            bnet_frame,
            text="🎮 Battle.net:",
            fg=CYBER_BLUE,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold"),
            cursor="hand2",
        ).pack(side="left")

        bnet_lbl = tk.Label(
            bnet_frame,
            text="BESTDQ#2639",
            fg=TEXT_WHITE,
            bg=BG_CARD,
            font=("Consolas", 9, "bold"),
            cursor="hand2",
        )
        bnet_lbl.pack(side="left", padx=(5, 0))

        # TikTok account (platform on left, username on right)
        tiktok_frame = tk.Frame(dev_inner, bg=BG_CARD, cursor="hand2")
        tiktok_frame.pack(side="right", padx=(16, 0))

        tk.Label(
            tiktok_frame,
            text="🎵 TikTok:",
            fg=TIKTOK_PINK,
            bg=BG_CARD,
            font=(FONT_FAMILY, 9, "bold"),
            cursor="hand2",
        ).pack(side="left")

        tiktok_lbl = tk.Label(
            tiktok_frame,
            text="@bbooqqww",
            fg=TEXT_WHITE,
            bg=BG_CARD,
            font=("Consolas", 9, "bold"),
            cursor="hand2",
        )
        tiktok_lbl.pack(side="left", padx=(5, 0))

        # Click-to-copy hint
        tk.Label(
            dev_inner,
            text="اضغط على أي حساب للنسخ 📋",
            fg=TEXT_MUTED,
            bg=BG_CARD,
            font=(FONT_FAMILY, 8),
        ).pack(side="left")

        # Copy to clipboard handlers
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

    # -------------------------------------------------------------
    # Add timestamped message to the log box
    # -------------------------------------------------------------
    def add_log(self, text, level="info"):
        now = time.strftime("%H:%M:%S")

        def _insert():
            self.log_box.configure(state="normal")
            # \u200F ensures brackets and timestamp stay formatted correctly with RTL text
            line = f"• {text}   \u200F[{now}]\n"
            self.log_box.insert("end", line, level)
            self.log_box.see("end")
            self.log_box.configure(state="disabled")

        self.root.after(0, _insert)

    # -------------------------------------------------------------
    # Startup initialization
    # -------------------------------------------------------------
    def initial_setup(self):
        self.add_log("تم تشغيل التطبيق بنجاح.", "success")

        if not firewall.is_admin():
            self.add_log("تنبيه: البرنامج يعمل بدون صلاحية مسؤول، قد يفشل تعديل جدار الحماية.", "warn")

        # Try auto-detecting game executable if not configured
        current_path = self.game_path_var.get().strip()
        if not current_path or not os.path.exists(current_path):
            found = firewall.find_game_automatically()
            if found:
                self.game_path_var.set(found)
                self.save_user_options()
                self.add_log(f"اكتشفت مسار اللعبة تلقائياً:\n  {found}", "info")
            else:
                self.add_log("لم يتم العثور على ملف اللعبة تلقائياً، يرجى تحديده عبر 'اختيار الملف'.", "warn")

        self.check_firewall_status()
        self.measure_ping()
        self.monitor_game_loop()

    # -------------------------------------------------------------
    # Update status banner (green when locked, red when unlocked)
    # -------------------------------------------------------------
    def _set_status_banner(self, active: bool):
        if active:
            self.status_outer.configure(bg=BORDER_ACTIVE)
            self.status_inner.configure(bg=GREEN_BG)
            self.status_title.configure(
                text="● شغال: متصل بسيرفر هولندا فقط (باقي السيرفرات مبلكه)",
                fg=GREEN,
                bg=GREEN_BG,
            )
            self.status_subtitle.configure(
                text="جميع السيرفرات الثانيه مبلكه في جدار الحماية — جاهز للعب!",
                fg="#a7f3d0",
                bg=GREEN_BG,
            )
        else:
            self.status_outer.configure(bg=RED)
            self.status_inner.configure(bg=RED_BG)
            self.status_title.configure(
                text="● مو مبلك : أنت مو مبلك السيرفرات حالياً (جميع السيرفرات مفتوحة)",
                fg="#f87171",
                bg=RED_BG,
            )
            self.status_subtitle.configure(
                text="تنبيه: السيرفرات الثانيه ماهي مبلكه — اضغط 'تبليك السيرفرات' تحت للتبليك",
                fg="#fca5a5",
                bg=RED_BG,
            )

    def check_firewall_status(self):
        """Check firewall status in background thread"""
        def _task():
            active = firewall.is_lock_active()
            self.root.after(0, lambda: self._set_status_banner(active))

        threading.Thread(target=_task, daemon=True).start()

    # -------------------------------------------------------------
    # Monitor game process in loop
    # -------------------------------------------------------------
    def monitor_game_loop(self):
        def _task():
            running = firewall.is_overwatch_running()

            def _update():
                if running:
                    self.game_state_lbl.configure(text="● اللعبة شغاله", fg=AMBER)
                else:
                    self.game_state_lbl.configure(text="● اللعبة مقفله (جاهز)", fg=GREEN)

                # Toggle buttons vs game-running warning card
                if self._is_game_running != running:
                    self._is_game_running = running
                    if running:
                        self.buttons_frame.pack_forget()
                        self.game_running_outer.pack(fill="x")
                    else:
                        self.game_running_outer.pack_forget()
                        self.buttons_frame.pack(fill="x")

            self.root.after(0, _update)

        threading.Thread(target=_task, daemon=True).start()
        self.root.after(2000, self.monitor_game_loop)

    # -------------------------------------------------------------
    # Ping Netherlands server
    # -------------------------------------------------------------
    def measure_ping(self):
        self.ping_badge.configure(text="ثواني افحص لك ...", fg=TEXT_MUTED)

        def _task():
            ms = firewall.check_netherlands_ping()

            def _update():
                if ms is not None:
                    color = GREEN if ms < 85 else (AMBER if ms < 140 else RED)
                    self.ping_badge.configure(text=f"⚡ {ms} ms", fg=color)
                    self.add_log(f"بنق سيرفر هولندا (ams1): {ms} ms", "info")
                else:
                    self.ping_badge.configure(text="Timeout", fg=RED)
                    self.add_log("تعذر قياس البنق لسيرفر هولندا (انتهت المهلة).", "warn")

            self.root.after(0, _update)

        threading.Thread(target=_task, daemon=True).start()

    # -------------------------------------------------------------
    # Manually browse and select Overwatch.exe
    # -------------------------------------------------------------
    def browse_game_path(self):
        chosen = filedialog.askopenfilename(
            title="اختر ملف Overwatch.exe",
            filetypes=[("Overwatch Executable", "Overwatch.exe"), ("All Executables", "*.exe")],
        )
        if chosen:
            if os.path.basename(chosen).lower() != "overwatch.exe":
                messagebox.showwarning("تنبيه", " اختار ملف Overwatch.exe الصحيح.")
                return
            self.game_path_var.set(chosen)
            self.save_user_options()
            self.add_log(f"تم حفظ مسار اللعبة: {chosen}", "success")

    # -------------------------------------------------------------
    # Enable lock (block all other servers)
    # -------------------------------------------------------------
    def activate_lock(self):
        if firewall.is_overwatch_running():
            messagebox.showwarning("اللعبه شغاله", "اللعبه شغاله حالياً! لازم تطفيها أولاً بعدين تقدر تسوي اللي تبيه.")
            return

        path = self.game_path_var.get().strip()
        if not path or not os.path.exists(path):
            messagebox.showerror("مسار اللعبة مفقود", "يرجى اختيار ملف Overwatch.exe أولاً عبر زر 'اختيار الملف'.")
            return

        self.btn_activate.set_disabled(True)
        self.add_log(" بطبق لك قواعد الحظر في جدار حماية ويندوز...", "info")

        def _task():
            try:
                count = firewall.enable_netherlands_lock(path)
                self.add_log(
                    f"تم التبليك بنجاح! تم حظر {count} نطاق IP، وسيرفر هولندا (ams1) فقط مفتوح الآن.",
                    "success",
                )
            except Exception as err:
                self.add_log(f"خطأ في التبليك: {err}", "error")
                self.root.after(0, lambda e=err: messagebox.showerror("فشل التبليك", str(e)))

            active = firewall.is_lock_active()
            self.root.after(0, lambda: self._set_status_banner(active))
            self.root.after(0, lambda: self.btn_activate.set_disabled(False))

        threading.Thread(target=_task, daemon=True).start()

    # -------------------------------------------------------------
    # Disable lock (unblock all servers)
    # -------------------------------------------------------------
    def deactivate_lock(self):
        if firewall.is_overwatch_running():
            messagebox.showwarning("اللعبه شغاله", "اللعبه شغاله حالياً! لازم تطفيها أولاً بعدين تقدر تسوي اللي تبيه.")
            return

        self.btn_deactivate.set_disabled(True)
        self.add_log("بشيل لك قواعد الحظر وافتح لك جميع السيرفرات...", "info")

        def _task():
            try:
                firewall.disable_netherlands_lock()
                self.add_log("الغيت الحظر . كل السيرفرات باللعبة مفتوحة الآن.", "warn")
            except Exception as err:
                self.add_log(f"جاني خطأ أثناء الإلغاء: {err}", "error")
                self.root.after(0, lambda e=err: messagebox.showerror("ما ضبط إلغاء الحظر", str(e)))

            active = firewall.is_lock_active()
            self.root.after(0, lambda: self._set_status_banner(active))
            self.root.after(0, lambda: self.btn_deactivate.set_disabled(False))

        threading.Thread(target=_task, daemon=True).start()

    # -------------------------------------------------------------
    # Flush DNS cache
    # -------------------------------------------------------------
    def do_flush_dns(self):
        def _task():
            ok = firewall.flush_dns()
            if ok:
                self.add_log("تم تنظيف ذاكرة الـ DNS بنجاح (Flush DNS).", "success")
            else:
                self.add_log("المسوحه ما قدرت انظف الـ DNS.", "error")

        threading.Thread(target=_task, daemon=True).start()

    # -------------------------------------------------------------
    # Factory reset: clean rules and restore defaults
    # -------------------------------------------------------------
    def reset_to_default(self):
        confirm = messagebox.askyesno(
            "استعادة ضبط المصنع",
            "تبي ارجع ضبط المصنع بالكامل و اخلي الويندوز زي ما كان؟\n\n"
            "•  بحذف جميع قواعد الحظر من جدار الحماية نهائياً.\n"
            "•  بفرغ كاش الـ DNS.\n"
            "•  بمسح الإعدادات المحفوظة.",
            icon="warning",
        )
        if not confirm:
            return

        self.add_log("ثواني و ارجع لك نظامك نفس ما كان...", "warn")

        def _task():
            firewall.reset_everything_to_default()

            def _done():
                self.unblock_on_close_var.set(False)
                found = firewall.find_game_automatically()
                self.game_path_var.set(found or "")
                self.save_user_options()
                self.check_firewall_status()
                self.add_log("تمت استعادة ضبط المصنع بنجاح وعاد نظام ويندوز لوضعه الأصلي.", "success")
                messagebox.showinfo("تم بنجاح", "تم تنظيف جدار الحماية واستعادة الإعدادات الافتراضية بالكامل!")

            self.root.after(0, _done)

        threading.Thread(target=_task, daemon=True).start()

    # -------------------------------------------------------------
    # Save user preferences
    # -------------------------------------------------------------
    def on_toggle_changed(self):
        self.save_user_options()
        if self.unblock_on_close_var.get():
            self.add_log("تم تفعيل خيار: إلغاء الحظر تلقائياً عند إغلاق البرنامج.", "info")
        else:
            self.add_log("تم تفعيل خيار: بقاء الحظر مستمراً حتى بعد إغلاق البرنامج.", "info")

    def save_user_options(self):
        data = {
            "game_path": self.game_path_var.get().strip(),
            "unblock_on_close": self.unblock_on_close_var.get(),
        }
        firewall.save_settings(data)

    # -------------------------------------------------------------
    # Handle window close event
    # -------------------------------------------------------------
    def on_close_window(self):
        if self.unblock_on_close_var.get():
            try:
                firewall.disable_netherlands_lock()
            except Exception:
                pass
        self.save_user_options()
        self.root.destroy()

    def run(self):
        """Start the Tkinter event loop"""
        self.root.mainloop()
