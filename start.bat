@echo off
title Permian Basin News Tracker
cd /d "%~dp0"

echo.
echo   ======================================
echo     Permian Basin News Tracker
echo   ======================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo   ERROR: Python not found. Install from https://python.org
    pause
    exit /b 1
)

echo   Installing dependencies...
pip install -r requirements.txt -q 2>nul

echo   Starting app...
echo.
python app.py
