@echo off
echo ============================================================
echo   CyberGuard - Quick Start (Windows)
echo ============================================================
echo.

:: Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found. Install Python 3.10+ from python.org
    pause
    exit /b 1
)

:: Create venv if not exists
if not exist "venv\" (
    echo [1/5] Creating virtual environment...
    python -m venv venv
)

:: Activate
echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

:: Install
echo [3/5] Installing requirements...
pip install -r requirements.txt -q

:: Train models
echo [4/5] Training ML models...
python setup_models.py

:: Migrate
echo [5/5] Running database migrations...
python manage.py migrate --run-syncdb

echo.
echo ============================================================
echo   Launching server at http://127.0.0.1:8000
echo   Press Ctrl+C to stop
echo ============================================================
echo.
python manage.py runserver

pause
