"""
catalog_view.py - Dedicated overview dashboard displaying supported and upcoming games
"""
import tkinter as tk
from typing import Callable, Dict, List
from src.games.base import BaseGame
from src.ui import theme
from src.ui.components import ModernButton, create_card


class SupportedGamesView(tk.Frame):
    """Catalog view presenting active games, upcoming integrations, and security guarantees."""

    def __init__(
        self,
        parent,
        games: List[BaseGame],
        icon_cache: Dict[str, tk.PhotoImage],
        on_select_game: Callable[[str], None],
    ):
        super().__init__(parent, bg=theme.BG_APP)
        self.games = games
        self.icon_cache = icon_cache
        self.on_select_game = on_select_game

        self._build_ui()

    def _build_ui(self):
        container = self

        # 1. Header Banner
        head_outer, head_inner = create_card(
            container,
            border_color="#1e293b",
            bg_color="#0f172a",
            pad_x=16,
            pad_y=12,
        )
        head_outer.pack(fill="x", pady=(0, 12))

        tk.Label(
            head_inner,
            text="🎮 الألعاب المدعومة في NexusLock",
            fg=theme.TEXT_WHITE,
            bg="#0f172a",
            font=(theme.FONT_FAMILY, 14, "bold"),
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            head_inner,
            text="تحكم كامل في مسار وخوادم ألعابك المفضلة بدون VPN وبدون برامج وسيطة ترفع البنق.",
            fg=theme.TEXT_MUTED,
            bg="#0f172a",
            font=(theme.FONT_FAMILY, 9),
            anchor="w",
        ).pack(fill="x", pady=(3, 0))

        # 2. Currently Active Games Section
        tk.Label(
            container,
            text="الألعاب المتاحة حالياً (جاهزة للاستخدام):",
            fg=theme.GREEN,
            bg=theme.BG_APP,
            font=(theme.FONT_FAMILY, 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        games_row = tk.Frame(container, bg=theme.BG_APP)
        games_row.pack(fill="x", pady=(0, 14))

        for game in self.games:
            card_outer, card_inner = create_card(
                games_row,
                border_color=theme.BORDER_COLOR,
                bg_color=theme.BG_CARD,
                pad_x=12,
                pad_y=12,
            )
            card_outer.pack(side="left", fill="both", expand=True, padx=4)

            # Top: Icon + Name
            top_box = tk.Frame(card_inner, bg=theme.BG_CARD)
            top_box.pack(fill="x", pady=(0, 8))

            icon_img = self.icon_cache.get(game.game_id)
            if icon_img:
                tk.Label(top_box, image=icon_img, bg=theme.BG_CARD).pack(side="left", padx=(0, 8))

            name_box = tk.Frame(top_box, bg=theme.BG_CARD)
            name_box.pack(side="left", fill="x", expand=True)

            tk.Label(
                name_box,
                text=game.display_name,
                fg=theme.TEXT_WHITE,
                bg=theme.BG_CARD,
                font=(theme.FONT_FAMILY, 11, "bold"),
                anchor="w",
            ).pack(fill="x")

            tk.Label(
                name_box,
                text="🟢 مدعوم بالكامل 100%",
                fg=theme.GREEN,
                bg=theme.BG_CARD,
                font=(theme.FONT_FAMILY, 8, "bold"),
                anchor="w",
            ).pack(fill="x")

            # Game details
            srv_count = len(game.get_servers_list())
            details_text = (
                f"• المنصة: {game.tagline.split('(')[0].strip()}\n"
                f"• الخوادم المتاحة: {srv_count} منطقة وسيرفر قابل للاختيار\n"
                f"• حظر السيرفرات الأخرى عبر جدار حماية ويندوز"
            )
            tk.Label(
                card_inner,
                text=details_text,
                fg=theme.TEXT_MUTED,
                bg=theme.BG_CARD,
                font=(theme.FONT_FAMILY, 8),
                justify="right",
                anchor="w",
            ).pack(fill="x", pady=(0, 10))

            # Action button
            ModernButton(
                card_inner,
                text=f"⚙️ فتح إعدادات {game.display_name}",
                command=lambda g_id=game.game_id: self.on_select_game(g_id),
                bg_color=theme.BTN_DARK,
                hover_color=theme.BTN_DARK_HOVER,
                font_size=8,
                height=32,
                radius=6,
                parent_bg=theme.BG_CARD,
            ).pack(fill="x")

        # 3. Upcoming Games Section
        tk.Label(
            container,
            text="ألعاب قادمة في التحديثات القادمة (قيد التطوير):",
            fg=theme.CYBER_BLUE,
            bg=theme.BG_APP,
            font=(theme.FONT_FAMILY, 10, "bold"),
            anchor="w",
        ).pack(fill="x", pady=(0, 6))

        upcoming_outer, upcoming_inner = create_card(container, pad_x=12, pad_y=10)
        upcoming_outer.pack(fill="x", pady=(0, 12))

        upcoming_list = [
            ("Counter-Strike 2 (CS2)", "Valve SDR Network", "🟡 قيد التجهيز"),
            ("Marvel Rivals", "NetEase Datacenters", "🔵 قريباً"),
            ("Apex Legends", "EA / Respawn Servers", "🔵 قريباً"),
        ]

        for title, net, st in upcoming_list:
            row = tk.Frame(upcoming_inner, bg=theme.BG_CARD)
            row.pack(fill="x", pady=2)

            tk.Label(
                row,
                text=f"🎮 {title}",
                fg=theme.TEXT_WHITE,
                bg=theme.BG_CARD,
                font=(theme.FONT_FAMILY, 9, "bold"),
            ).pack(side="left")

            tk.Label(
                row,
                text=f"({net})",
                fg=theme.TEXT_DIM,
                bg=theme.BG_CARD,
                font=(theme.FONT_FAMILY, 8),
            ).pack(side="left", padx=8)

            tk.Label(
                row,
                text=st,
                fg=theme.AMBER if "تجهيز" in st else theme.CYBER_BLUE,
                bg=theme.BG_CARD,
                font=(theme.FONT_FAMILY, 8, "bold"),
            ).pack(side="right")

        # 4. Security & Safety Guarantee
        sec_outer, sec_inner = create_card(
            container,
            border_color="#14532d",
            bg_color="#052e16",
            pad_x=12,
            pad_y=8,
        )
        sec_outer.pack(fill="x")

        tk.Label(
            sec_inner,
            text="🛡️ ضمان الأمان (Zero-Ban Guarantee):",
            fg="#4ade80",
            bg="#052e16",
            font=(theme.FONT_FAMILY, 9, "bold"),
            anchor="w",
        ).pack(fill="x")

        tk.Label(
            sec_inner,
            text="NexusLock لا يعدل ملفات الألعاب ولا يتدخل في ذاكرة اللعبة (No Memory Hooking).\n"
            "التحكم يتم 100% عبر قواعد جدار الحماية الخارجي لنظام ويندوز الرسمي (Windows Firewall).",
            fg="#bbf7d0",
            bg="#052e16",
            font=(theme.FONT_FAMILY, 8),
            anchor="w",
            justify="right",
        ).pack(fill="x", pady=(2, 0))
