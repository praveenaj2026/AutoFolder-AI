@echo off
REM AutoFolder AI Launcher
REM Quick launch script for AutoFolder AI

echo ========================================
echo    AutoFolder AI - File Organizer
echo ========================================
echo.

cd /d "%~dp0"

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.8 or higher
    pause
    exit /b 1
)

REM Launch the application
echo Starting AutoFolder AI...
echo.
python src\main.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo ERROR: Application failed to start
    pause
)
