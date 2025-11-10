@echo off
REM Auto-start script for JARVIS AI Assistant (Windows)
REM Place this in Windows Startup folder or use Task Scheduler

cd /d "%~dp0"

REM Check if running from packaged executable
if exist "JARVIS.exe" (
    start "" "JARVIS.exe"
    exit
)

REM Check if running from source
if exist "Main.py" (
    REM Check for virtual environment
    if exist "venv\Scripts\activate.bat" (
        call venv\Scripts\activate.bat
        python Main.py
    ) else (
        echo ERROR: Virtual environment not found!
        echo Please run: python -m venv venv
        echo Then install dependencies: pip install -r Requirements.txt
        pause
    )
) else (
    echo ERROR: Main.py not found!
    echo Please run this script from the JARVIS project directory.
    pause
)

