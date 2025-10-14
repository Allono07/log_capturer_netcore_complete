@echo off
echo.
echo ========================================
echo   Android Log Capturer - Windows
echo ========================================
echo.
echo Starting Android Log Capturer...
echo Web interface will be available at:
echo   http://localhost:5001
echo.
echo Press Ctrl+C to stop the server
echo.

REM Check if ADB is available
adb version >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: ADB not found in PATH
    echo Please install Android SDK Platform Tools
    echo and add to system PATH
    echo.
    pause
)

REM Navigate to the directory where this script is located
cd /d "%~dp0"

REM Check if executable exists
if not exist "dist\AndroidLogCapturerSimple.exe" (
    echo ERROR: AndroidLogCapturerSimple.exe not found
    echo Please build the executable first using:
    echo   pyinstaller --onefile --add-data "templates;templates" --add-data "static;static" --name "AndroidLogCapturerSimple" web_app_simple.py
    echo.
    pause
    exit /b 1
)

REM Run the executable
echo Running AndroidLogCapturerSimple.exe...
echo.
dist\AndroidLogCapturerSimple.exe

echo.
echo Application has stopped.
pause