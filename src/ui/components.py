"""
components.py - Modern CustomTkinter UI components, rounded cards, dual-language switcher, and dark modal dialogs
"""
import tkinter as tk
from typing import Callable, Optional
import customtkinter as ctk
from src import i18n
from src.ui import theme


def draw_rounded_rect(canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int, radius: int, **kwargs):
    """Draw a rounded rectangle on a standard Canvas (used for custom progress animations)."""
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


class ModernModal:
    """
    Modern dark-themed gaming modal dialog replacing legacy Windows XP tkinter.messagebox.
    """

    @staticmethod
    def _show(
        parent,
        title: str,
        message: str,
        icon_text: str = "⚡",
        accent_color: str = theme.CYBER_BLUE,
        is_confirm: bool = False,
    ) -> bool:
        result = {"value": False}

        top = ctk.CTkToplevel(parent)
        top.title(title)
        top.configure(fg_color=theme.BG_APP)
        top.resizable(False, False)
        top.transient(parent)
        top.grab_set()
        theme.apply_dark_titlebar(top, round_corners=True)

        w, h = 430, 235
        try:
            px = parent.winfo_rootx() + (parent.winfo_width() - w) // 2
            py = parent.winfo_rooty() + (parent.winfo_height() - h) // 2
        except Exception:
            px = (top.winfo_screenwidth() - w) // 2
            py = (top.winfo_screenheight() - h) // 2
        top.geometry(f"{w}x{h}+{max(40, px)}+{max(40, py)}")

        card = ctk.CTkFrame(
            top,
            fg_color=theme.BG_CARD,
            border_color=accent_color,
            border_width=1,
            corner_radius=14,
        )
        card.pack(fill="both", expand=True, padx=12, pady=12)

        # Header row with badge + title
        head = ctk.CTkFrame(card, fg_color="transparent")
        head.pack(fill="x", padx=18, pady=(16, 8))

        badge = ctk.CTkLabel(
            head,
            text=icon_text,
            font=(theme.FONT_FAMILY, 18),
            fg_color=theme.BG_INPUT,
            text_color=accent_color,
            corner_radius=8,
            width=36,
            height=36,
        )
        badge.pack(side="right" if i18n.is_rtl() else "left")

        title_lbl = ctk.CTkLabel(
            head,
            text=title,
            font=(theme.FONT_FAMILY, 14, "bold"),
            text_color=theme.TEXT_WHITE,
            anchor="e" if i18n.is_rtl() else "w",
        )
        title_lbl.pack(side="right" if i18n.is_rtl() else "left", padx=10, fill="x", expand=True)

        # Body message
        msg_lbl = ctk.CTkLabel(
            card,
            text=message,
            font=(theme.FONT_FAMILY, 12),
            text_color=theme.TEXT_MUTED,
            wraplength=380,
            justify="right" if i18n.is_rtl() else "left",
        )
        msg_lbl.pack(fill="both", expand=True, padx=20, pady=(2, 10))

        # Action buttons row
        btn_row = ctk.CTkFrame(card, fg_color="transparent")
        btn_row.pack(fill="x", padx=18, pady=(0, 14))

        def on_ok():
            result["value"] = True
            top.destroy()

        def on_cancel():
            result["value"] = False
            top.destroy()

        if is_confirm:
            yes_txt = "نعم، تأكيد" if i18n.is_rtl() else "Yes, Confirm"
            no_txt = "إلغاء" if i18n.is_rtl() else "Cancel"

            ctk.CTkButton(
                btn_row,
                text=yes_txt,
                command=on_ok,
                fg_color=theme.RED,
                hover_color=theme.RED_HOVER,
                text_color="#ffffff",
                font=(theme.FONT_FAMILY, 12, "bold"),
                height=36,
                corner_radius=9,
            ).pack(side="left", fill="x", expand=True, padx=(0, 6))

            ctk.CTkButton(
                btn_row,
                text=no_txt,
                command=on_cancel,
                fg_color=theme.BTN_DARK,
                hover_color=theme.BTN_DARK_HOVER,
                text_color=theme.TEXT_WHITE,
                font=(theme.FONT_FAMILY, 12, "bold"),
                height=36,
                corner_radius=9,
            ).pack(side="right", fill="x", expand=True, padx=(6, 0))
        else:
            ok_txt = "حسناً" if i18n.is_rtl() else "OK"
            ctk.CTkButton(
                btn_row,
                text=ok_txt,
                command=on_ok,
                fg_color=accent_color,
                hover_color=theme.PRIMARY_BLUE_HOVER if accent_color == theme.CYBER_BLUE else accent_color,
                text_color="#05080f" if accent_color in (theme.CYBER_BLUE, theme.AMBER) else "#ffffff",
                font=(theme.FONT_FAMILY, 12, "bold"),
                height=36,
                corner_radius=9,
            ).pack(fill="x", expand=True)

        top.bind("<Return>", lambda _e: on_ok())
        top.bind("<Escape>", lambda _e: on_cancel())
        parent.wait_window(top)
        return result["value"]

    @classmethod
    def show_info(cls, parent, title: str, message: str):
        cls._show(parent, title, message, icon_text="✅", accent_color=theme.GREEN, is_confirm=False)

    @classmethod
    def show_warning(cls, parent, title: str, message: str):
        cls._show(parent, title, message, icon_text="⚠️", accent_color=theme.AMBER, is_confirm=False)

    @classmethod
    def show_error(cls, parent, title: str, message: str):
        cls._show(parent, title, message, icon_text="❌", accent_color=theme.RED, is_confirm=False)

    @classmethod
    def ask_yes_no(cls, parent, title: str, message: str) -> bool:
        return cls._show(parent, title, message, icon_text="⚙️", accent_color=theme.AMBER, is_confirm=True)


class ModernButton(ctk.CTkButton):
    """Modern anti-aliased rounded button built on CustomTkinter."""

    def __init__(
        self,
        parent,
        text: str,
        command: Optional[Callable] = None,
        bg_color: str = theme.BTN_DARK,
        hover_color: str = theme.BTN_DARK_HOVER,
        text_color: str = theme.TEXT_WHITE,
        font_size: int = 10,
        bold: bool = True,
        height: int = 40,
        width: int = 125,
        radius: int = 10,
        parent_bg: str = "transparent",
        border_color: Optional[str] = None,
        border_width: int = 0,
    ):
        # Convert legacy small tk point sizes to crisp CTk pixel sizes
        px_size = max(12, int(font_size * 1.35))
        weight = "bold" if bold else "normal"
        super().__init__(
            parent,
            text=text,
            command=command,
            fg_color=bg_color,
            hover_color=hover_color,
            text_color=text_color,
            text_color_disabled=theme.TEXT_DIM,
            font=(theme.FONT_FAMILY, px_size, weight),
            width=width,
            height=height,
            corner_radius=radius,
            border_width=border_width,
            border_color=border_color or theme.BORDER_COLOR,
        )
        self._default_bg = bg_color
        self._default_hover = hover_color

    def set_text(self, new_text: str):
        self.configure(text=new_text)

    def set_colors(self, bg_color: str, hover_color: str):
        self._default_bg = bg_color
        self._default_hover = hover_color
        self.configure(fg_color=bg_color, hover_color=hover_color)

    def set_disabled(self, disabled: bool):
        if disabled:
            self.configure(state="disabled", fg_color="#141a29")
        else:
            self.configure(state="normal", fg_color=self._default_bg, hover_color=self._default_hover)


class ModernToggleSwitch(ctk.CTkSwitch):
    """Modern smooth pill toggle switch."""

    def __init__(self, parent, variable: tk.BooleanVar, command=None, parent_bg="transparent"):
        super().__init__(
            parent,
            text="",
            variable=variable,
            command=command,
            onvalue=True,
            offvalue=False,
            width=46,
            height=24,
            switch_width=44,
            switch_height=22,
            fg_color="#232f46",
            progress_color=theme.GREEN,
            button_color="#ffffff",
            button_hover_color="#e2e8f0",
        )


class LanguageSwitcher(ctk.CTkFrame):
    """
    Sleek dual-language pill switcher displaying both '🌐 English' and 'العربية 🌐'.
    Highlights the active language with a glowing cyber pill and allows instant switching.
    """

    def __init__(
        self,
        parent,
        current_lang: str = "ar",
        on_change: Optional[Callable[[str], None]] = None,
        height: int = 36,
        parent_bg: str = theme.BG_SIDEBAR,
    ):
        super().__init__(
            parent,
            fg_color=theme.BG_INPUT,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            corner_radius=10,
            height=height,
        )
        self.current_lang = "en" if current_lang == "en" else "ar"
        self.on_change = on_change

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.btn_en = ctk.CTkButton(
            self,
            text="🌐 English",
            command=lambda: self._handle_click("en"),
            font=(theme.FONT_FAMILY, 12, "bold"),
            height=height - 8,
            corner_radius=7,
        )
        self.btn_en.grid(row=0, column=0, padx=(4, 2), pady=4, sticky="ew")

        self.btn_ar = ctk.CTkButton(
            self,
            text="العربية 🌐",
            command=lambda: self._handle_click("ar"),
            font=(theme.FONT_FAMILY, 12, "bold"),
            height=height - 8,
            corner_radius=7,
        )
        self.btn_ar.grid(row=0, column=1, padx=(2, 4), pady=4, sticky="ew")

        self._apply_styles()

    def _handle_click(self, clicked_lang: str):
        # If user clicks the already-active button, toggle to the other language for 1-click convenience
        target_lang = ("en" if self.current_lang == "ar" else "ar") if clicked_lang == self.current_lang else clicked_lang
        self.current_lang = target_lang
        self._apply_styles()
        if self.on_change:
            self.on_change(target_lang)

    def set_lang(self, lang: str):
        self.current_lang = "en" if lang == "en" else "ar"
        self._apply_styles()

    def _apply_styles(self):
        if self.current_lang == "en":
            self.btn_en.configure(
                fg_color=theme.PRIMARY_BLUE,
                hover_color=theme.PRIMARY_BLUE_HOVER,
                text_color="#ffffff",
            )
            self.btn_ar.configure(
                fg_color="transparent",
                hover_color=theme.BG_CARD_HOVER,
                text_color=theme.TEXT_MUTED,
            )
        else:
            self.btn_ar.configure(
                fg_color=theme.PRIMARY_BLUE,
                hover_color=theme.PRIMARY_BLUE_HOVER,
                text_color="#ffffff",
            )
            self.btn_en.configure(
                fg_color="transparent",
                hover_color=theme.BG_CARD_HOVER,
                text_color=theme.TEXT_MUTED,
            )


def create_card(
    parent,
    border_color: str = theme.BORDER_COLOR,
    bg_color: str = theme.BG_CARD,
    pad_x: int = 16,
    pad_y: int = 12,
    radius: int = 14,
    border_width: int = 1,
):
    """Create a smooth anti-aliased rounded card with an inner padded container."""
    outer = ctk.CTkFrame(
        parent,
        fg_color=bg_color,
        border_color=border_color,
        border_width=border_width,
        corner_radius=radius,
    )
    inner = ctk.CTkFrame(outer, fg_color="transparent", corner_radius=0)
    inner.pack(fill="both", expand=True, padx=pad_x, pady=pad_y)
    return outer, inner


class SidebarGameButton(ctk.CTkFrame):
    """Modern rounded navigation card in the sidebar with crisp CTkImage icon and active glow."""

    def __init__(
        self,
        parent,
        game_id: str,
        title: str,
        subtitle: str,
        icon_img: Optional[ctk.CTkImage] = None,
        on_click: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(parent, fg_color="transparent")
        self.game_id = game_id
        self.title = title
        self.subtitle = subtitle
        self.icon_img = icon_img
        self.on_click = on_click
        self.is_selected = False
        self.is_locked = False
        self.has_lock_state = False
        self.last_srv_name = ""

        # Rounded card container
        self.card = ctk.CTkFrame(
            self,
            fg_color=theme.BG_CARD,
            border_color=theme.BORDER_COLOR,
            border_width=1,
            corner_radius=12,
            cursor="hand2",
        )
        self.card.pack(fill="x", padx=12, pady=4)

        self.inner = ctk.CTkFrame(self.card, fg_color="transparent", cursor="hand2")
        self.inner.pack(fill="x", padx=10, pady=9)

        # Left active glow bar
        self.indicator = ctk.CTkFrame(
            self.inner,
            width=4,
            height=34,
            corner_radius=2,
            fg_color="transparent",
        )
        self.indicator.pack(side="left", padx=(0, 8))

        # Game Icon or Catalog Badge
        if self.icon_img:
            self.icon_lbl = ctk.CTkLabel(
                self.inner,
                text="",
                image=self.icon_img,
                width=36,
                height=36,
            )
            self.icon_lbl.pack(side="left", padx=(0, 10))
        else:
            self.icon_lbl = ctk.CTkLabel(
                self.inner,
                text="🎮",
                font=(theme.FONT_FAMILY, 17),
                fg_color=theme.BG_INPUT,
                corner_radius=8,
                width=36,
                height=36,
            )
            self.icon_lbl.pack(side="left", padx=(0, 10))

        # Texts column
        self.text_frame = ctk.CTkFrame(self.inner, fg_color="transparent", cursor="hand2")
        self.text_frame.pack(side="left", fill="both", expand=True)

        clean_title = self.title.replace("🎮 ", "") if not self.icon_img else self.title
        self.title_lbl = ctk.CTkLabel(
            self.text_frame,
            text=clean_title,
            text_color=theme.TEXT_WHITE,
            font=(theme.FONT_FAMILY, 13, "bold"),
            anchor="w",
            height=18,
        )
        self.title_lbl.pack(fill="x")

        self.sub_lbl = ctk.CTkLabel(
            self.text_frame,
            text=self.subtitle,
            text_color=theme.TEXT_MUTED,
            font=(theme.FONT_FAMILY, 11),
            anchor="w",
            height=16,
        )
        self.sub_lbl.pack(fill="x", pady=(2, 0))

        # Bind click & hover events across all child widgets
        for widget in [self.card, self.inner, self.indicator, self.icon_lbl, self.text_frame, self.title_lbl, self.sub_lbl]:
            widget.bind("<Button-1>", self._handle_click)
            widget.bind("<Enter>", self._handle_enter)
            widget.bind("<Leave>", self._handle_leave)

    def _handle_click(self, _event=None):
        if self.on_click:
            self.on_click(self.game_id)

    def _handle_enter(self, _event=None):
        if not self.is_selected:
            self.card.configure(fg_color=theme.BG_CARD_HOVER, border_color=theme.BORDER_HOVER)

    def _handle_leave(self, _event=None):
        if not self.is_selected:
            self.card.configure(fg_color=theme.BG_CARD, border_color=theme.BORDER_COLOR)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        if selected:
            self.card.configure(fg_color="#132238", border_color=theme.BORDER_SELECTED)
            self.title_lbl.configure(text_color=theme.CYBER_BLUE)
            self.indicator.configure(fg_color=theme.CYBER_BLUE)
        else:
            self.card.configure(fg_color=theme.BG_CARD, border_color=theme.BORDER_COLOR)
            self.title_lbl.configure(text_color=theme.TEXT_WHITE)
            self.indicator.configure(fg_color="transparent")

    def set_title_and_subtitle(self, title: str, subtitle: Optional[str] = None):
        self.title = title
        clean_title = title.replace("🎮 ", "") if not self.icon_img else title
        self.title_lbl.configure(text=clean_title)
        if subtitle is not None:
            self.subtitle = subtitle
            self.sub_lbl.configure(text=subtitle)

    def set_lock_status(self, is_locked: bool, srv_name: str = ""):
        self.has_lock_state = True
        self.is_locked = is_locked
        self.last_srv_name = srv_name
        if is_locked:
            label_text = f"🛡️ {srv_name}" if srv_name else i18n.t("nav_locked_default")
            self.sub_lbl.configure(text=label_text, text_color=theme.GREEN)
        else:
            self.sub_lbl.configure(text=i18n.t("nav_unlocked"), text_color=theme.TEXT_MUTED)
