@echo off
echo ============================================
echo         JARVIS - First Time Setup
echo ============================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed. Download from https://python.org
    pause & exit /b 1
)

:: Create virtual environment
if not exist venv (
    echo [1/3] Creating virtual environment...
    python -m venv venv
)

:: Install dependencies
echo [2/3] Installing dependencies...
venv\Scripts\pip install -q -r requirements.txt

:: Run enrollment
echo [3/3] Starting voice enrollment...
venv\Scripts\python.exe enroll.py

echo.
echo Setup complete! Run jarvis.bat to start.
pause
