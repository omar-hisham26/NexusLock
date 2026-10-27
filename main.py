"""
main.py - Entry point for the NexusLock application with Discord-style splash updater
"""
import os
import sys
import traceback
from pathlib import Path

# Ensure root and src directories are in Python sys.path
CURRENT_DIR = Path(__file__).resolve().parent
SRC_DIR = CURRENT_DIR / "src"
for p in (CURRENT_DIR, SRC_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from src.core import admin
from src.ui.app import NexusLockGUI
from src.ui.splash import DiscordSplash


def start_main_application():
    """Start the main NexusLock GUI window after splash/update check."""
    app = NexusLockGUI()
    app.run()


def main():
    if os.name != "nt":
        print("هذا التطبيق مخصص لنظام ويندوز فقط للتحكم في جدار الحماية (Windows Firewall).")
        sys.exit(1)

    # Request Administrator privileges via UAC prompt if not elevated
    admin.request_admin()

    # Show Discord-style Frameless Splash Updater first
    splash = DiscordSplash(on_ready_callback=start_main_application)
    splash.mainloop()


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        error_text = traceback.format_exc()
        print("\n" + "=" * 50)
        print("حدث خطأ غير متوقع أثناء تشغيل NexusLock:")
        print(error_text)
        print("=" * 50)
        try:
            with open(CURRENT_DIR / "error.log", "w", encoding="utf-8") as f:
                f.write(error_text)
        except Exception:
            pass
        try:
            import tkinter.messagebox as mb
            mb.showerror("خطأ في تشغيل NexusLock", f"حدث خطأ:\n{err}\n\nتم حفظ التفاصيل في error.log")
        except Exception:
            pass
        input("\nاضغط Enter للخروج...")
