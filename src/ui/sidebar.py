"""
sidebar.py - Modern left navigation sidebar with high-DPI LANCZOS icons, language switcher, and status badges
"""
from typing import Callable, Dict, Optional
import customtkinter as ctk
from src import config, i18n
from src.core import admin
from src.ui import theme
from src.ui.components import LanguageSwitcher, SidebarGameButton


class Sidebar(ctk.CTkFrame):
    """Left navigation sidebar containing app brand, language switcher, and game selectors."""

    def __init__(
        self,
        parent,
        games: list,
        selected_view_id: str,
        on_view_change: Callable[[str], None],
        on_lang_change: Optional[Callable[[str], None]] = None,
    ):
        super().__init__(
            parent,
            fg_color=theme.BG_SIDEBAR,
            width=260,
            corner_radius=0,
        )
        self.pack_propagate(False)
        self.games = games
        self.selected_view_id = selected_view_id
        self.on_view_change = on_view_change
        self.on_lang_change = on_lang_change
        self.game_buttons: Dict[str, SidebarGameButton] = {}
        self.icon_cache: Dict[str, Optional[ctk.CTkImage]] = {}
        self.app_logo_img: Optional[ctk.CTkImage] = None

        self._load_icons()
        self._build_ui()

    def _load_icons(self):
        """Load high-DPI anti-aliased LANCZOS icons for the app brand and each game."""
        app_icon_path = config.ASSETS_DIR / "app_icon.png"
        self.app_logo_img = theme.load_ctk_image(app_icon_path, (34, 34))

        for game in self.games:
            icon_path = config.ASSETS_DIR / game.icon_filename
            self.icon_cache[game.game_id] = theme.load_ctk_image(icon_path, (36, 36))

    def _build_ui(self):
        # 1. Branding Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=16, pady=(18, 12))

        title_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_row.pack(fill="x")

        if self.app_logo_img:
            ctk.CTkLabel(
                title_row,
                text="",
                image=self.app_logo_img,
                width=34,
                height=34,
            ).pack(side="left", padx=(0, 8))

        self.brand_lbl = ctk.CTkLabel(
            title_row,
            text=i18n.t("app_brand_title"),
            text_color=theme.TEXT_WHITE,
            font=(theme.FONT_FAMILY, 18, "bold"),
        )
        self.brand_lbl.pack(side="left")

        self.version_lbl = ctk.CTkLabel(
            title_row,
            text=i18n.t("version_badge", ver=config.VERSION),
            text_color=theme.GREEN,
            fg_color=theme.GREEN_BG,
            corner_radius=6,
            font=(theme.FONT_FAMILY, 10, "bold"),
            padx=7,
            pady=2,
        )
        self.version_lbl.pack(side="right")

        self.subtitle_lbl = ctk.CTkLabel(
            header_frame,
            text=i18n.t("sidebar_subtitle"),
            text_color=theme.TEXT_MUTED,
            font=(theme.FONT_FAMILY, 11),
            anchor="w",
        )
        self.subtitle_lbl.pack(fill="x", pady=(6, 12))

        # Dual Language Switcher Button (🌐 English | العربية 🌐)
        self.lang_switcher = LanguageSwitcher(
            header_frame,
            current_lang=i18n.get_lang(),
            on_change=self._handle_lang_change,
            height=36,
            parent_bg=theme.BG_SIDEBAR,
        )
        self.lang_switcher.pack(fill="x")

        # Subtle Divider
        ctk.CTkFrame(self, fg_color=theme.BORDER_COLOR, height=1).pack(fill="x", padx=14, pady=(6, 12))

        # 2. Section Title
        self.section_lbl = ctk.CTkLabel(
            self,
            text=i18n.t("nav_games_section"),
            text_color=theme.TEXT_DIM,
            font=(theme.FONT_FAMILY, 11, "bold"),
            anchor="w",
        )
        self.section_lbl.pack(fill="x", padx=16, pady=(0, 4))

        # 3. Game Buttons List
        for game in self.games:
            btn = SidebarGameButton(
                parent=self,
                game_id=game.game_id,
                title=game.get_display_name(),
                subtitle=i18n.t("nav_checking"),
                icon_img=self.icon_cache.get(game.game_id),
                on_click=self._handle_item_click,
            )
            btn.pack(fill="x")
            self.game_buttons[game.game_id] = btn

        # Highlight initially selected view
        if self.selected_view_id in self.game_buttons:
            self.game_buttons[self.selected_view_id].set_selected(True)

        # 4. Bottom Footer (Admin Status Card + System Info)
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.pack(side="bottom", fill="x", padx=14, pady=16)

        self.admin_ok = admin.is_admin()
        admin_text = i18n.t("admin_active") if self.admin_ok else i18n.t("admin_inactive")
        admin_fg = theme.GREEN if self.admin_ok else theme.AMBER
        admin_bg = theme.GREEN_BG if self.admin_ok else theme.AMBER_BG
        admin_border = theme.GREEN_BORDER if self.admin_ok else theme.AMBER_BORDER

        admin_card = ctk.CTkFrame(
            footer_frame,
            fg_color=admin_bg,
            border_color=admin_border,
            border_width=1,
            corner_radius=10,
        )
        admin_card.pack(fill="x")

        self.admin_badge = ctk.CTkLabel(
            admin_card,
            text=admin_text,
            text_color=admin_fg,
            font=(theme.FONT_FAMILY, 11, "bold"),
            height=32,
        )
        self.admin_badge.pack(fill="x", padx=8, pady=2)

        self.footer_note_lbl = ctk.CTkLabel(
            footer_frame,
            text=i18n.t("sidebar_footer_note"),
            text_color=theme.TEXT_DIM,
            font=(theme.FONT_FAMILY, 10),
        )
        self.footer_note_lbl.pack(fill="x", pady=(6, 0))

    def _handle_lang_change(self, new_lang: str):
        if self.on_lang_change:
            self.on_lang_change(new_lang)

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

    def refresh_language(self):
        """Update all sidebar labels and buttons when the application language changes."""
        self.lang_switcher.set_lang(i18n.get_lang())
        self.brand_lbl.configure(text=i18n.t("app_brand_title"))
        self.version_lbl.configure(text=i18n.t("version_badge", ver=config.VERSION))
        self.subtitle_lbl.configure(text=i18n.t("sidebar_subtitle"))
        self.section_lbl.configure(text=i18n.t("nav_games_section"))
        self.admin_badge.configure(
            text=i18n.t("admin_active") if self.admin_ok else i18n.t("admin_inactive")
        )
        self.footer_note_lbl.configure(text=i18n.t("sidebar_footer_note"))

        for game in self.games:
            btn = self.game_buttons.get(game.game_id)
            if btn:
                loc_title = game.get_display_name()
                if btn.has_lock_state:
                    btn.set_title_and_subtitle(loc_title)
                    btn.set_lock_status(btn.is_locked, btn.last_srv_name)
                else:
                    btn.set_title_and_subtitle(loc_title, i18n.t("nav_checking"))
