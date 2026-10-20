@echo off
cd /d "%~dp0"
title Dragter (Tangerine Edition)

echo ======================================================================
echo   Dragter - Tangerine Liquid Radial File Converter
echo ======================================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not in your system PATH!
    echo Please install Python 3.10+ from python.org and make sure 'Add Python to PATH' is checked.
    echo.
    pause
    exit /b 1
)

echo [1/3] Stopping any previous Dragter instances...
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name = 'python.exe' or Name = 'pythonw.exe'\" | Where-Object { $_.CommandLine -like '*main.py*' } | Stop-Process -Force" >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
ping 127.0.0.1 -n 2 >nul

echo [2/3] Verifying dependencies...
python -c "import PyQt6, PIL, fitz, docx, pynput, reportlab, win32com" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing missing dependencies...
    python -m pip install -r requirements.txt
)

echo [3/3] Starting Dragter in background...
where pythonw >nul 2>&1
if %errorlevel% equ 0 (
    start "" pythonw main.py
) else (
    start "" python main.py
)

echo.
echo ======================================================================
echo   [SUCCESS] Dragter is active in your background!
echo ======================================================================
echo.
echo HOW TO TRIGGER:
echo   1. Click and drag ANY file in Windows Explorer or Desktop
echo   2. Tap / Click SHIFT while dragging
echo   3. The Tangerine Radial Wheel blooms directly at your cursor!
echo   4. Drop the file onto your desired format to convert instantly
echo.
echo System Tray:
echo   * Look for the Dragter icon in the bottom-right taskbar tray
echo   * Right-click the tray icon to Open Wheel, Tools, or Exit
echo.
echo Closing window...
ping 127.0.0.1 -n 4 >nul
exit
