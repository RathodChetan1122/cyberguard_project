#!/bin/bash
echo "============================================================"
echo "  CyberGuard - Quick Start (macOS / Linux)"
echo "============================================================"
echo ""

# Create venv if not exists
if [ ! -d "venv" ]; then
    echo "[1/5] Creating virtual environment..."
    python3 -m venv venv
fi

# Activate
echo "[2/5] Activating virtual environment..."
source venv/bin/activate

# Install
echo "[3/5] Installing requirements..."
pip install -r requirements.txt -q

# Train models
echo "[4/5] Training ML models..."
python setup_models.py

# Migrate
echo "[5/5] Running database migrations..."
python manage.py migrate --run-syncdb

echo ""
echo "============================================================"
echo "  Launching server at http://127.0.0.1:8000"
echo "  Press Ctrl+C to stop"
echo "============================================================"
echo ""
python manage.py runserver
