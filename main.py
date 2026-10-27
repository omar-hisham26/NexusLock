"""
main.py - Entry point for the NetherWatch application
"""
import os
import sys
import traceback
from pathlib import Path

# Make sure the current directory and src directory are in Python's import path
CURRENT_DIR = Path(__file__).resolve().parent
SRC_DIR = CURRENT_DIR / "src"
for p in (CURRENT_DIR, SRC_DIR):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from src import firewall
from src.gui import NetherWatchGUI


def main():
    # NetherWatch only works on Windows because it configures Windows Firewall
    if os.name != "nt":
        print("هذا التطبيق مخصص لنظام ويندوز فقط للتحكم في جدار الحماية (Windows Firewall).")
        sys.exit(1)

    # Request administrator rights if not already elevated
    firewall.request_admin()

    # Start the GUI
    app = NetherWatchGUI()
    app.run()


if __name__ == "__main__":
    try:
        main()
    except Exception as err:
        # If an unexpected error happens, log it and keep the window open so it doesn't close silently
        error_text = traceback.format_exc()
        print("\n" + "=" * 50)
        print("حدث خطأ أثناء تشغيل التطبيق:")
        print(error_text)
        print("=" * 50)
        try:
            with open(CURRENT_DIR / "error.log", "w", encoding="utf-8") as f:
                f.write(error_text)
        except Exception:
            pass
        try:
            import tkinter.messagebox as mb
            mb.showerror("خطأ في تشغيل NetherWatch", f"حدث خطأ:\n{err}\n\nتم حفظ التفاصيل في error.log")
        except Exception:
            pass
        input("\nاضغط Enter للخروج...")
