@echo off
title InternalWhisper Setup
cd /d "%~dp0"
echo ===================================================
echo   Installing InternalWhisper Dependencies...
echo ===================================================
python -m pip install -r requirements.txt
echo.
echo Launching InternalWhisper in background tray...
start "" python main.py
