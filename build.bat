@echo off
REM Build script for JARVIS AI Assistant (Windows)
REM This script packages JARVIS into a standalone executable

echo ========================================
echo JARVIS AI Assistant - Build Script
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/upgrade build dependencies
echo Installing build dependencies...
pip install --upgrade pip
pip install pyinstaller

REM Install project dependencies
echo Installing project dependencies...
pip install -r Requirements.txt

REM Clean previous builds
echo Cleaning previous builds...
if exist "build\" rmdir /s /q build
if exist "dist\" rmdir /s /q dist
if exist "JARVIS.spec" (
    echo Using existing spec file...
) else (
    echo ERROR: jarvis.spec not found!
    pause
    exit /b 1
)

REM Build the executable
echo.
echo ========================================
echo Building JARVIS executable...
echo ========================================
echo.

pyinstaller jarvis.spec

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Build completed successfully!
    echo ========================================
    echo.
    echo Executable location: dist\JARVIS.exe
    echo.
    echo To test the build:
    echo   1. Navigate to dist folder
    echo   2. Copy your .env file to dist folder
    echo   3. Run JARVIS.exe
    echo.
) else (
    echo.
    echo ========================================
    echo Build failed! Check errors above.
    echo ========================================
    echo.
)

pause

