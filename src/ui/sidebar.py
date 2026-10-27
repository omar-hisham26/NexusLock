"""
sidebar.py - Left-hand navigation sidebar displaying app brand, games catalog, and game selectors
"""
import tkinter as tk
from typing import Callable, Dict, Optional
from src import config
from src.core import admin
from src.games.base import BaseGame
from src.ui import theme
from src.ui.components import SidebarGameButton


class Sidebar(tk.Frame):
    """Left navigation sidebar containing app brand, supported games link, and game selectors."""

    def __init__(
        self,
        parent,
        games: list,
        selected_view_id: str,
        on_view_change: Callable[[str], None],
    ):
        super().__init__(parent, bg=theme.BG_SIDEBAR, width=240)
        self.pack_propagate(False)
        self.games = games
        self.selected_view_id = selected_view_id
        self.on_view_change = on_view_change
        self.game_buttons: Dict[str, SidebarGameButton] = {}
        self.icon_cache: Dict[str, tk.PhotoImage] = {}

        self._load_icons()
        self._build_ui()

    def _load_icons(self):
        """Load and cache 36x36 downsampled PNG icons for each game."""
        for game in self.games:
            icon_path = config.ASSETS_DIR / game.icon_filename
            if icon_path.exists():
                try:
                    full_img = tk.PhotoImage(file=str(icon_path))
                    factor = max(1, full_img.width() // 36)
                    scaled = full_img.subsample(factor, factor)
                    self.icon_cache[game.game_id] = scaled
                except Exception as e:
                    print(f"Failed to load icon {icon_path}: {e}")
                    self.icon_cache[game.game_id] = None
            else:
                self.icon_cache[game.game_id] = None

    def _build_ui(self):
        # 1. Branding Header
        header_frame = tk.Frame(self, bg=theme.BG_SIDEBAR, padx=14, pady=16)
        header_frame.pack(fill="x")

        title_row = tk.Frame(header_frame, bg=theme.BG_SIDEBAR)
        title_row.pack(fill="x")

        tk.Label(
            title_row,
            text="⚡ NEXUSLOCK",
            fg=theme.TEXT_WHITE,
            bg=theme.BG_SIDEBAR,
            font=(theme.FONT_FAMILY, 14, "bold"),
        ).pack(side="left")

        tk.Label(
            title_row,
            text=f"v{config.VERSION}",
            fg=theme.GREEN,
            bg=theme.BG_SIDEBAR,
            font=(theme.FONT_FAMILY, 8, "bold"),
            padx=6,
        ).pack(side="left", pady=(3, 0))

        tk.Label(
            header_frame,
            text="أداة حظر ومطابقة سيرفرات الألعاب",
            fg=theme.TEXT_MUTED,
            bg=theme.BG_SIDEBAR,
            font=(theme.FONT_FAMILY, 9),
            anchor="w",
        ).pack(fill="x", pady=(2, 0))

        # Divider
        tk.Frame(self, bg=theme.BORDER_COLOR, height=1).pack(fill="x", padx=10, pady=(4, 10))

        # 2. "الألعاب المدعومة" (Supported Games Catalog Button)
        self.btn_catalog = SidebarGameButton(
            parent=self,
            game_id="catalog",
            title="🎮 الألعاب المدعومة",
            subtitle="نظرة عامة على الألعاب والخوادم",
            icon_img=None,
            on_click=self._handle_item_click,
        )
        self.btn_catalog.pack(fill="x")
        self.game_buttons["catalog"] = self.btn_catalog

        # Divider
        tk.Frame(self, bg=theme.BORDER_COLOR, height=1).pack(fill="x", padx=10, pady=(8, 8))

        # 3. Section Title
        tk.Label(
            self,
            text="الألعاب المتاحة للتحكم:",
            fg=theme.TEXT_MUTED,
            bg=theme.BG_SIDEBAR,
            font=(theme.FONT_FAMILY, 9, "bold"),
            padx=14,
            anchor="w",
        ).pack(fill="x", pady=(0, 4))

        # 4. Game Buttons List
        for game in self.games:
            btn = SidebarGameButton(
                parent=self,
                game_id=game.game_id,
                title=game.display_name,
                subtitle="جاري الفحص...",
                icon_img=self.icon_cache.get(game.game_id),
                on_click=self._handle_item_click,
            )
            btn.pack(fill="x")
            self.game_buttons[game.game_id] = btn

        # Highlight initially selected view
        if self.selected_view_id in self.game_buttons:
            self.game_buttons[self.selected_view_id].set_selected(True)

        # 5. Bottom Footer (Admin Status Badge + System Info)
        footer_frame = tk.Frame(self, bg=theme.BG_SIDEBAR, padx=12, pady=14)
        footer_frame.pack(side="bottom", fill="x")

        admin_ok = admin.is_admin()
        admin_text = "🛡️ صلاحية مسؤول مفعلة" if admin_ok else "⚠️ بدون صلاحية مسؤول"
        admin_fg = theme.GREEN if admin_ok else theme.AMBER
        admin_bg = theme.GREEN_BG if admin_ok else theme.AMBER_BG

        admin_badge = tk.Label(
            footer_frame,
            text=admin_text,
            fg=admin_fg,
            bg=admin_bg,
            font=(theme.FONT_FAMILY, 8, "bold"),
            padx=8,
            pady=4,
        )
        admin_badge.pack(fill="x")

        tk.Label(
            footer_frame,
            text="قواعد جدار حماية ويندوز المباشرة",
            fg=theme.TEXT_DIM,
            bg=theme.BG_SIDEBAR,
            font=(theme.FONT_FAMILY, 8),
            pady=4,
        ).pack(fill="x")

    def _handle_item_click(self, view_id: str):
        if view_id == self.selected_view_id:
            return
        self.set_active_view(view_id)
        self.on_view_change(view_id)

    def set_active_view(self, view_id: str):
        if self.selected_view_id in self.game_buttons:
            self.game_buttons[self.selected_view_id].set_selected(False)
        self.selected_view_id = view_id
        if self.selected_view_id in self.game_buttons:
            self.game_buttons[self.selected_view_id].set_selected(True)

    def update_game_lock_status(self, game_id: str, is_locked: bool, srv_name: str = ""):
        """Update the subtitle badge under the game name in sidebar."""
        if game_id in self.game_buttons:
            self.game_buttons[game_id].set_lock_status(is_locked, srv_name)
