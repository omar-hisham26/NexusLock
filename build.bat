@echo off
chcp 65001 >nul
echo ========================================================
echo   NexusLock - Build and Packaging Wizard
echo ========================================================
echo.

echo [1/3] Compiling Python source code with PyInstaller...
python -m PyInstaller --noconsole --onefile --clean --uac-admin --version-file="version_info.txt" --name "NexusLock" --icon="assets/icon.ico" --collect-all customtkinter --add-data "data;data" --add-data "assets;assets" main.py

if exist "dist\NexusLock.exe" (
    echo [2/3] Moving NexusLock.exe to main directory...
    move /y "dist\NexusLock.exe" "NexusLock.exe" >nul
) else (
    echo [Warning] dist\NexusLock.exe not found!
)

echo [3/3] Generating NexusLock-Setup.exe installer...
set "ISCC_EXE="
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC_EXE=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files\Inno Setup 6\ISCC.exe"
if not defined ISCC_EXE if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set "ISCC_EXE=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"

if defined ISCC_EXE (
    "%ISCC_EXE%" "installer.iss"
    echo.
    echo ========================================================
    echo   SUCCESS: NexusLock-Setup.exe generated successfully!
    echo ========================================================
) else (
    echo [Note] Inno Setup compiler not found. Standalone NexusLock.exe is ready!
)

:: Clean up temporary build artifacts
if exist "build" rd /s /q "build"
if exist "dist" rd /s /q "dist"
if exist "NexusLock.spec" del /f /q "NexusLock.spec"

echo.
echo Build complete!
