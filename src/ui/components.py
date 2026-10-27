"""
components.py - Reusable custom modern Tkinter UI components
"""
import tkinter as tk
from typing import Callable, Optional
from src.ui import theme


def draw_rounded_rect(canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int, radius: int, **kwargs):
    """Draw a smooth polygon approximating a rounded rectangle on a Tkinter canvas."""
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
    """Modern button rendered using a Canvas with smooth rounded borders and hover states."""

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
        width: int = 130,
        radius: int = 10,
        parent_bg: str = theme.BG_APP,
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
        self.font_spec = (theme.FONT_FAMILY, font_size, weight)

        self.bind("<Configure>", self._redraw)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<ButtonRelease-1>", self._on_click)

    def _redraw(self, _event=None):
        self.delete("all")
        w = max(self.winfo_width(), 20)
        h = max(self.winfo_height(), 20)
        fill = "#1a2030" if self.is_disabled else self.current_bg
        fg = theme.TEXT_DIM if self.is_disabled else self.text_color
        draw_rounded_rect(self, 1, 1, w - 1, h - 1, self.radius, fill=fill, outline="")
        self.create_text(w / 2, h / 2, text=self.text, fill=fg, font=self.font_spec, justify="center")

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

    def set_text(self, new_text: str):
        self.text = new_text
        self._redraw()

    def set_colors(self, bg_color: str, hover_color: str):
        self.bg_color = bg_color
        self.hover_color = hover_color
        self.current_bg = bg_color
        self._redraw()

    def set_disabled(self, disabled: bool):
        self.is_disabled = disabled
        self.configure(cursor="arrow" if disabled else "hand2")
        self.current_bg = self.bg_color
        self._redraw()


class ModernToggleSwitch(tk.Canvas):
    """Modern iOS/Windows 11 style toggle switch."""

    def __init__(self, parent, variable: tk.BooleanVar, command=None, parent_bg=theme.BG_CARD):
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
        track_color = theme.GREEN if on else "#283246"
        draw_rounded_rect(self, 2, 2, 44, 22, 10, fill=track_color, outline="")
        knob_x = 32 if on else 14
        self.create_oval(knob_x - 7, 5, knob_x + 7, 19, fill="#ffffff", outline="")


def create_card(parent, border_color=theme.BORDER_COLOR, bg_color=theme.BG_CARD, pad_x=16, pad_y=14):
    """Create a modern border-accented container card."""
    outer = tk.Frame(parent, bg=border_color, padx=1, pady=1)
    inner = tk.Frame(outer, bg=bg_color, padx=pad_x, pady=pad_y)
    inner.pack(fill="both", expand=True)
    return outer, inner


class SidebarGameButton(tk.Frame):
    """Interactive sidebar game item showing icon, title, subtitle, and active selection state."""

    def __init__(
        self,
        parent,
        game_id: str,
        title: str,
        subtitle: str,
        icon_img: Optional[tk.PhotoImage] = None,
        on_click: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(parent, bg=theme.BG_SIDEBAR, cursor="hand2")
        self.game_id = game_id
        self.title = title
        self.subtitle = subtitle
        self.icon_img = icon_img
        self.on_click = on_click
        self.is_selected = False
        self.is_locked = False

        # Outer highlight card
        self.card_outer = tk.Frame(self, bg=theme.BORDER_COLOR, padx=1, pady=1)
        self.card_outer.pack(fill="x", padx=10, pady=5)

        self.card_inner = tk.Frame(self.card_outer, bg=theme.BG_CARD, padx=10, pady=10)
        self.card_inner.pack(fill="x")

        # Layout: Left side indicator bar + Icon + Right side Texts
        self.indicator = tk.Frame(self.card_inner, bg=theme.BG_CARD, width=4)
        self.indicator.pack(side="left", fill="y", padx=(0, 8))

        # Icon
        self.icon_lbl = tk.Label(self.card_inner, bg=theme.BG_CARD, cursor="hand2")
        if self.icon_img:
            self.icon_lbl.configure(image=self.icon_img)
        self.icon_lbl.pack(side="left", padx=(0, 10))

        # Text container
        self.text_frame = tk.Frame(self.card_inner, bg=theme.BG_CARD, cursor="hand2")
        self.text_frame.pack(side="left", fill="both", expand=True)

        self.title_lbl = tk.Label(
            self.text_frame,
            text=self.title,
            fg=theme.TEXT_WHITE,
            bg=theme.BG_CARD,
            font=(theme.FONT_FAMILY, 11, "bold"),
            anchor="w",
            cursor="hand2",
        )
        self.title_lbl.pack(fill="x")

        self.sub_lbl = tk.Label(
            self.text_frame,
            text=self.subtitle,
            fg=theme.TEXT_MUTED,
            bg=theme.BG_CARD,
            font=(theme.FONT_FAMILY, 9),
            anchor="w",
            cursor="hand2",
        )
        self.sub_lbl.pack(fill="x", pady=(2, 0))

        # Bind clicks and hovers to all child widgets
        for widget in [self, self.card_outer, self.card_inner, self.indicator, self.icon_lbl, self.text_frame, self.title_lbl, self.sub_lbl]:
            widget.bind("<Button-1>", self._handle_click)
            widget.bind("<Enter>", self._handle_enter)
            widget.bind("<Leave>", self._handle_leave)

    def _handle_click(self, _event=None):
        if self.on_click:
            self.on_click(self.game_id)

    def _handle_enter(self, _event=None):
        if not self.is_selected:
            self.card_inner.configure(bg=theme.BG_CARD_HOVER)
            self.icon_lbl.configure(bg=theme.BG_CARD_HOVER)
            self.text_frame.configure(bg=theme.BG_CARD_HOVER)
            self.title_lbl.configure(bg=theme.BG_CARD_HOVER)
            self.sub_lbl.configure(bg=theme.BG_CARD_HOVER)
            self.indicator.configure(bg=theme.BG_CARD_HOVER)

    def _handle_leave(self, _event=None):
        if not self.is_selected:
            self.card_inner.configure(bg=theme.BG_CARD)
            self.icon_lbl.configure(bg=theme.BG_CARD)
            self.text_frame.configure(bg=theme.BG_CARD)
            self.title_lbl.configure(bg=theme.BG_CARD)
            self.sub_lbl.configure(bg=theme.BG_CARD)
            self.indicator.configure(bg=theme.BG_CARD)

    def set_selected(self, selected: bool):
        self.is_selected = selected
        if selected:
            self.card_outer.configure(bg=theme.BORDER_SELECTED)
            bg = "#16233b"
            self.card_inner.configure(bg=bg)
            self.icon_lbl.configure(bg=bg)
            self.text_frame.configure(bg=bg)
            self.title_lbl.configure(bg=bg, fg=theme.CYBER_BLUE)
            self.sub_lbl.configure(bg=bg)
            self.indicator.configure(bg=theme.CYBER_BLUE)
        else:
            self.card_outer.configure(bg=theme.BORDER_COLOR)
            self.card_inner.configure(bg=theme.BG_CARD)
            self.icon_lbl.configure(bg=theme.BG_CARD)
            self.text_frame.configure(bg=theme.BG_CARD)
            self.title_lbl.configure(bg=theme.BG_CARD, fg=theme.TEXT_WHITE)
            self.sub_lbl.configure(bg=theme.BG_CARD)
            self.indicator.configure(bg=theme.BG_CARD)

    def set_lock_status(self, is_locked: bool, srv_name: str = ""):
        self.is_locked = is_locked
        if is_locked:
            label_text = f"🛡️ {srv_name}" if srv_name else "🛡️ السيرفر محمي"
            self.sub_lbl.configure(text=label_text, fg=theme.GREEN)
        else:
            self.sub_lbl.configure(text="🔓 السيرفرات مفتوحة", fg=theme.TEXT_MUTED)
