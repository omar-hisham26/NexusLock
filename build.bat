@echo off
chcp 65001 >nul
echo ========================================================
echo   ⚡ بناء NetherWatch وتوليد السيت اب الاحترافي
echo ========================================================
echo.

echo [1/3] تجميع الكود المصدري عبر PyInstaller...
pyinstaller --noconsole --onefile --name "NetherWatch" --icon="assets/icon.ico" --add-data "data;data" --add-data "assets;assets" main.py

if exist "dist\NetherWatch.exe" (
    echo [2/3] نقل NetherWatch.exe الجديد إلى المجلد الرئيسي...
    move /y "dist\NetherWatch.exe" "NetherWatch.exe" >nul
) else (
    echo [تنبيه] لم يتم العثور على dist\NetherWatch.exe، سيتم استخدام الملف الحالي.
)

echo [3/3] توليد ملف السيت اب NetherWatch-Setup.exe عبر Inno Setup...
set "ISCC_PATH=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not exist "%ISCC_PATH%" set "ISCC_PATH=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist "%ISCC_PATH%" set "ISCC_PATH=C:\Program Files\Inno Setup 6\ISCC.exe"

if exist "%ISCC_PATH%" (
    "%ISCC_PATH%" "installer.iss"
    echo.
    echo ========================================================
    echo   ✅ تم الانتهاء بنجاح! تم إنشاء NetherWatch-Setup.exe الفخم
    echo ========================================================
) else (
    echo [خطأ] لم يتم العثور على Inno Setup! تأكد من تثبيته أولاً.
)

echo.
pause
