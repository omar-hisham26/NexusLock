"""
i18n.py - Internationalization (Pure Arabic & Pure English) support for NexusLock
Ensures zero English-Arabic BiDi text mixing when Arabic is active.
"""
from typing import Dict

_current_lang: str = "ar"

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "ar": {
        # Window & Branding
        "app_window_title": "نيكسوس لوك — حظر وتحديد سيرفرات الألعاب",
        "app_brand_title": "نيكسوس لوك",
        "version_badge": "الإصدار {ver}",
        "sidebar_subtitle": "أداة حظر وتحديد سيرفرات الألعاب",
        "lang_label": "اللغة:",

        # Splash Screen
        "splash_checking": "جاري البحث عن تحديثات...",
        "splash_found": "تم العثور على تحديث جديد {ver}! جاري التنزيل...",
        "splash_downloading": "جاري تنزيل التحديث ({p}%)...",
        "splash_ready": "البرنامج محدث! جاري التشغيل...",

        # Sidebar
        "nav_games_section": "الألعاب المتاحة للتحكم:",
        "nav_checking": "جاري الفحص...",
        "nav_locked_default": "🛡️ السيرفر محمي",
        "nav_unlocked": "🔓 السيرفرات مفتوحة",
        "admin_active": "🛡️ صلاحية المسؤول مفعلة",
        "admin_inactive": "⚠️ بدون صلاحية مسؤول",
        "sidebar_footer_note": "قواعد جدار حماية ويندوز المباشرة",

        # Game View
        "status_checking_title": "● جاري فحص جدار الحماية...",
        "status_checking_sub": "يتم التحقق من قواعد جدار حماية ويندوز",
        "status_active_title": "● مفعل: متصل بسيرفر {server} فقط — {game}",
        "status_active_sub": "جميع السيرفرات الأخرى محظورة حالياً في جدار الحماية",
        "status_inactive_title": "● غير مفعل: جميع سيرفرات {game} مفتوحة",
        "status_inactive_sub": "لا توجد قواعد حظر نشطة، البحث سيتصل بأي سيرفر عالمي",

        "select_server_lbl": "🎯 اختر السيرفر المطلوب تثبيته:",
        "server_details_lbl": "عنوان فحص السيرفر: {ip}",
        "btn_test_ping": "🔄 فحص البنق",
        "ping_Waiting": "جاري القياس...",
        "ping_unit": "{ms} م.ث",
        "ping_fast": "⚡ {ms} م.ث",
        "ping_failed": "-- تعذر الاتصال",

        "game_path_lbl": "مسار ملف تشغيل {game}:",
        "game_state_checking": "○ جاري فحص حالة اللعبة...",
        "game_state_running": "● {game} قيد التشغيل حالياً",
        "game_state_ready": "○ اللعبة مغلقة — جاهز",
        "btn_browse": "📂 تحديد الملف",
        "browse_dialog_title": "حدد ملف تشغيل {game}",

        "btn_activate": "🛡️ تثبيت سيرفر {server}\nوحظر باقي السيرفرات الأخرى",
        "btn_deactivate": "🔓 فك الحظر\nوفتح جميع السيرفرات عالمياً",

        "game_running_warn_title": "⚠️ لعبة {game} تعمل حالياً على جهازك!",
        "game_running_warn_sub": "يرجى إغلاق اللعبة أولاً قبل تفعيل الحظر أو فكه لتطبيق قواعد جدار الحماية.",

        "opt_unblock_on_close": "فك الحظر تلقائياً عند إغلاق البرنامج",
        "btn_flush_dns": "🌐 تنظيف الشبكة",
        "btn_factory_reset": "⚙️ ضبط المصنع",

        # Logs & Footer
        "log_header": "سجل العمليات المباشر",
        "dev_label": "المطور:",
        "dev_bnet_btn": "🎮 باتل نت: BESTDQ#2639",
        "dev_tiktok_btn": "🎵 تيك توك: @bbooqqww",
        "dev_copy_hint": "اضغط على أي حساب لنسخه 📋",
        "log_copied_bnet": "تم نسخ حساب باتل نت الخاص بالمطور إلى الحافظة بنجاح!",
        "log_copied_tiktok": "تم نسخ حساب تيك توك الخاص بالمطور إلى الحافظة بنجاح!",
        "log_lang_changed": "🌐 تم تغيير لغة التطبيق إلى العربية.",
        "log_switched_game": "تم الانتقال إلى إعدادات لعبة {game}",
        "log_startup_ok": "⚡ تم تشغيل نيكسوس لوك بنجاح وجاهز لاختيار السيرفرات.",
        "log_no_admin_warn": "⚠️ تنبيه: التطبيق يعمل بدون صلاحيات المسؤول، يرجى تشغيله كمسؤول لتطبيق قواعد جدار الحماية.",
        "log_server_selected": "تم اختيار سيرفر الوجهة للعبة {game}: {server}",
        "log_path_auto_found": "تم اكتشاف مسار لعبة {game} تلقائياً بنجاح.",
        "log_path_not_found": "لم يتم العثور على مسار لعبة {game} تلقائياً، يرجى تحديده يدوياً.",
        "log_path_updated": "تم تحديث مسار ملف تشغيل لعبة {game} بنجاح.",
        "log_locking": "جاري حظر السيرفرات الأخرى للعبة {game} وتثبيت سيرفر {server}...",
        "log_lock_success": "✅ تم تفعيل الحظر للعبة {game} بنجاح وتثبيت سيرفر {server} — تم حظر {count} نطاق.",
        "log_lock_fail": "❌ حدث خطأ أثناء تطبيق الحظر: {err}",
        "log_unlocking": "جاري فك الحظر عن جميع سيرفرات لعبة {game}...",
        "log_unlock_success": "🔓 تم فك الحظر وفتح جميع سيرفرات لعبة {game} بنجاح.",
        "log_unlock_fail": "❌ تعذر فك الحظر: {err}",
        "log_flushing_dns": "جاري تنظيف ذاكرة الشبكة المؤقتة...",
        "log_flush_dns_ok": "✅ تم تنظيف ذاكرة الشبكة المؤقتة بنجاح.",
        "log_flush_dns_fail": "⚠️ تعذر تنظيف ذاكرة الشبكة.",
        "log_reset_start": "جاري إجراء ضبط المصنع وحذف جميع قواعد الحظر...",
        "log_reset_done": "✅ اكتمل ضبط المصنع وتم تنظيف جدار الحماية بالكامل.",

        # MessageBoxes & Errors
        "msg_missing_path_title": "مسار غير محدد",
        "msg_missing_path_body": "يرجى تحديد مسار ملف تشغيل {game} أولاً عبر زر تحديد الملف.",
        "msg_game_running_title": "اللعبة قيد التشغيل",
        "msg_game_running_lock": "يرجى إغلاق لعبة {game} أولاً لتطبيق الحظر.",
        "msg_game_running_unlock": "يرجى إغلاق لعبة {game} أولاً قبل فك الحظر.",
        "msg_lock_ok_title": "تم تثبيت السيرفر بنجاح",
        "msg_lock_ok_body": "تم حظر جميع السيرفرات الأخرى بنجاح!\nأنت الآن متصل بسيرفر:\n{server}",
        "msg_lock_fail_title": "فشل تثبيت السيرفر",
        "msg_unlock_ok_title": "تم فك الحظر",
        "msg_unlock_ok_body": "تم فتح جميع السيرفرات بنجاح للعبة {game}.\nيمكنك الآن اللعب في أي سيرفر.",
        "msg_unlock_fail_title": "خطأ",
        "msg_unlock_fail_body": "حدث خطأ أثناء فك الحظر:\n{err}",
        "msg_dns_title": "تنظيف الشبكة",
        "msg_dns_body": "تم تنظيف ذاكرة الشبكة المؤقتة بنجاح!",
        "msg_reset_confirm_title": "تأكيد ضبط المصنع",
        "msg_reset_confirm_body": "هل أنت متأكد من رغبتك في حذف جميع القواعد واستعادة الإعدادات الأصلية؟",
        "msg_reset_done_title": "ضبط المصنع",
        "msg_reset_done_body": "تمت استعادة الإعدادات الأصلية وتنظيف قواعد جدار الحماية بنجاح!",

        "err_empty_path": "مسار اللعبة فارغ! يرجى تحديد مسار ملف تشغيل اللعبة أولاً.",
        "err_file_not_found": "لم يتم العثور على ملف تشغيل اللعبة في المسار المحدد.",
        "err_empty_ips": "قائمة العناوين المراد حظرها فارغة!",
        "err_admin_required": (
            "ويندوز يرفض تعديل جدار الحماية بدون صلاحيات المسؤول!\n"
            "يرجى تشغيل البرنامج كمسؤول."
        ),
        "err_firewall_failed": "فشل إنشاء قاعدة جدار الحماية:\n{msg}",
    },
    "en": {
        # Window & Branding
        "app_window_title": "NexusLock — Game Server Blocker & Region Picker",
        "app_brand_title": "NEXUSLOCK",
        "version_badge": "v{ver}",
        "sidebar_subtitle": "Game Server Blocker & Region Picker",
        "lang_label": "Language:",

        # Splash Screen
        "splash_checking": "Checking for updates...",
        "splash_found": "Update {ver} found! Downloading...",
        "splash_downloading": "Downloading update ({p}%)...",
        "splash_ready": "Up to date! Launching...",

        # Sidebar
        "nav_games_section": "AVAILABLE GAMES:",
        "nav_checking": "Checking...",
        "nav_locked_default": "🛡️ Server Locked",
        "nav_unlocked": "🔓 All Servers Open",
        "admin_active": "🛡️ Administrator Active",
        "admin_inactive": "⚠️ No Admin Privileges",
        "sidebar_footer_note": "Direct Windows Firewall Rules",

        # Game View
        "status_checking_title": "● Checking Windows Firewall...",
        "status_checking_sub": "Verifying Windows Firewall rules",
        "status_active_title": "● ACTIVE: Locked to {server} only ({game})",
        "status_active_sub": "All other servers are actively blocked in Windows Firewall",
        "status_inactive_title": "● INACTIVE: All {game} servers are open",
        "status_inactive_sub": "No active block rules; matchmaking will connect to any global server",

        "select_server_lbl": "🎯 Select Target Server to Lock:",
        "server_details_lbl": "Server Code: {code}   •   Ping IP: {ip}",
        "btn_test_ping": "🔄 Test Ping",
        "ping_Waiting": "... ms",
        "ping_unit": "{ms} ms",
        "ping_fast": "⚡ {ms} ms",
        "ping_failed": "-- ms (Failed)",

        "game_path_lbl": "Game Executable Path ({exes})",
        "game_state_checking": "○ Checking game status...",
        "game_state_running": "● {game} is Running",
        "game_state_ready": "○ Game Closed (Ready)",
        "btn_browse": "📂 Browse",
        "browse_dialog_title": "Select {game} Executable",

        "btn_activate": "🛡️ Lock {server} Server\n(Block All Other Servers)",
        "btn_deactivate": "🔓 Unlock Servers\n(Open All Global Servers)",

        "game_running_warn_title": "⚠️ {game} is currently running!",
        "game_running_warn_sub": "Please close the game first before locking or unlocking servers to apply firewall rules.",

        "opt_unblock_on_close": "Automatically unlock servers when closing app",
        "btn_flush_dns": "🌐 Flush DNS",
        "btn_factory_reset": "⚙️ Factory Reset",

        # Logs & Footer
        "log_header": "Live Activity Log",
        "dev_label": "Developer:",
        "dev_bnet_btn": "🎮 Battle.net: BESTDQ#2639",
        "dev_tiktok_btn": "🎵 TikTok: @bbooqqww",
        "dev_copy_hint": "Click any account to copy 📋",
        "log_copied_bnet": "Copied developer Battle.net tag (BESTDQ#2639) to clipboard!",
        "log_copied_tiktok": "Copied developer TikTok username (bbooqqww) to clipboard!",
        "log_lang_changed": "🌐 Application language switched to English.",
        "log_switched_game": "Switched to settings: {game}",
        "log_startup_ok": "⚡ NexusLock started successfully (Multi-Game Server Selector).",
        "log_no_admin_warn": "⚠️ Warning: Running without Administrator privileges. Please run as Admin to apply firewall rules.",
        "log_server_selected": "Selected target server for {game}: {server}",
        "log_path_auto_found": "Automatically detected {game} path:\n  {path}",
        "log_path_not_found": "Could not auto-detect {game} path. Please browse manually.",
        "log_path_updated": "Updated {game} executable path:\n  {path}",
        "log_locking": "Blocking other servers for {game} and locking to: {server}...",
        "log_lock_success": "✅ Server lock enabled for {game}! Locked to: {server} ({count} IP ranges blocked)",
        "log_lock_fail": "❌ Error applying firewall lock: {err}",
        "log_unlocking": "Unlocking servers for {game}...",
        "log_unlock_success": "🔓 Successfully unlocked all servers for {game}.",
        "log_unlock_fail": "❌ Failed to unlock servers: {err}",
        "log_flushing_dns": "Flushing Windows DNS resolver cache...",
        "log_flush_dns_ok": "✅ DNS cache flushed successfully.",
        "log_flush_dns_fail": "⚠️ Failed to flush DNS cache.",
        "log_reset_start": "Performing factory reset and removing all NexusLock firewall rules...",
        "log_reset_done": "✅ Factory reset complete and Windows Firewall cleaned.",

        # MessageBoxes & Errors
        "msg_missing_path_title": "Missing Game Path",
        "msg_missing_path_body": "Please select the {game} executable file first using the Browse button.",
        "msg_game_running_title": "Game is Running",
        "msg_game_running_lock": "Please close {game} first before applying the server lock.",
        "msg_game_running_unlock": "Please close {game} first before unlocking servers.",
        "msg_lock_ok_title": "Server Lock Active",
        "msg_lock_ok_body": "All other servers have been blocked!\nYou are now locked to:\n{server}",
        "msg_lock_fail_title": "Lock Failed",
        "msg_unlock_ok_title": "Servers Unlocked",
        "msg_unlock_ok_body": "All servers are now open for {game}.\nYou can matchmake in any global region.",
        "msg_unlock_fail_title": "Error",
        "msg_unlock_fail_body": "An error occurred while unlocking servers:\n{err}",
        "msg_dns_title": "Flush DNS",
        "msg_dns_body": "Windows DNS cache has been flushed successfully!",
        "msg_reset_confirm_title": "Confirm Factory Reset",
        "msg_reset_confirm_body": "Are you sure you want to remove all firewall rules and restore default settings?",
        "msg_reset_done_title": "Factory Reset",
        "msg_reset_done_body": "Default settings restored and all firewall rules cleaned successfully!",

        "err_empty_path": "Game path is empty! Please select the {game} executable first.",
        "err_file_not_found": "Game executable was not found at:\n{path}",
        "err_empty_ips": "The list of IP addresses to block is empty!",
        "err_admin_required": (
            "Windows denied firewall modification without Administrator privileges!\n"
            "Please run the application as Administrator."
        ),
        "err_firewall_failed": "Failed to create Windows Firewall rule:\n{msg}",
    },
}


def get_lang() -> str:
    """Return current active language code ('ar' or 'en')."""
    return _current_lang


def set_lang(lang: str) -> None:
    """Set active language code ('ar' or 'en')."""
    global _current_lang
    _current_lang = "en" if str(lang).lower().strip() == "en" else "ar"


def is_rtl() -> bool:
    """Return True if current language is Arabic (RTL)."""
    return _current_lang == "ar"


def t(key: str, **kwargs) -> str:
    """Translate a key into the currently active language with optional formatting."""
    lang_dict = TRANSLATIONS.get(_current_lang, TRANSLATIONS["ar"])
    template = lang_dict.get(key) or TRANSLATIONS["ar"].get(key, key)
    if kwargs:
        try:
            return template.format(**kwargs)
        except Exception:
            return template
    return template
