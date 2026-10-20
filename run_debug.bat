@echo off
cd /d "%~dp0"
title Dragter (Live Console)

echo ======================================================================
echo   Dragter - Live Console Mode (Tangerine Edition)
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

echo Stopping any previous Dragter instances...
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name = 'python.exe' or Name = 'pythonw.exe'\" | Where-Object { $_.CommandLine -like '*main.py*' } | Stop-Process -Force" >nul 2>&1
taskkill /F /IM pythonw.exe >nul 2>&1
ping 127.0.0.1 -n 2 >nul

echo Verifying dependencies...
python -c "import PyQt6, PIL, fitz, docx, pynput, reportlab, win32com" >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing missing dependencies...
    python -m pip install -r requirements.txt
)

echo.
echo Starting Dragter with live console logs...
echo.
echo HOW TO TRIGGER:
echo   1. Click and drag ANY file in Windows Explorer or Desktop
echo   2. Tap / Click SHIFT while dragging
echo   3. The Tangerine Radial Wheel blooms directly at your cursor!
echo.
echo Live logs will appear below:
echo.

python -u main.py
pause
