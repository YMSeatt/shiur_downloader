@echo off
REM ============================================================================
REM PyInstaller Build Script for BehaviorLogger
REM ============================================================================
echo Starting build for ShasDownloader...

REM --- Configuration ---
REM For better portability, it's recommended to copy your icon into your 
REM project directory and use a relative path.
set "ICON_PATH=assets\LightningChocolate.png"
set "SPLASH_PATH=assets\YMAPPS.png"

REM It's also best to use a relative path to your main script.
REM For example, if this script is in your project root and your main file is
REM in a 'Split' subfolder, you could use "Split\__main__.py".
set "SCRIPT_PATH=DownloaderShasDriveGUI_new.py"
set "SERVICE_PATH=C:\Users\Yaakov M\Coding\shiur_downloader\service_account.json"

set "APP_NAME=Shas Downloader (Google Drive Edition)"
REM --splash "%SPLASH_PATH%" ^
REM --- PyInstaller Command ---
echo Running PyInstaller...
pyinstaller --onefile ^
    --windowed ^
    --clean ^
    -n "%APP_NAME%" ^
    -i "%ICON_PATH%" ^
    --splash "%SPLASH_PATH%" ^
    --collect-all sv_ttk ^
    --collect-all darkdetect ^
    --add-data assets;assets ^
    --exclude-module PyQt5 ^
    --exclude-module PySide6 ^
    --exclude-module tkcap ^
    --exclude-module matplotlib ^
    --exclude-module pandas ^
    --exclude-module selenium ^
    --exclude-module pikepdf ^
    "%SCRIPT_PATH%"

echo.
echo Build finished. Check the 'dist' folder for your executable.
pause