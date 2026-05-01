#!/usr/bin/env python
"""
setup_models.py
===============
Master setup script — trains both ML models in sequence.

Usage:
    python setup_models.py

Run this once after installing requirements to produce:
    ml_models/sms_model.pkl
    ml_models/sms_vectorizer.pkl
    ml_models/url_model.pkl
"""

import sys
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent


def run(script_name: str):
    script_path = PROJECT_DIR / 'ml_training' / script_name
    print(f"\nRunning: {script_path}\n")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        check=False
    )
    if result.returncode != 0:
        print(f"WARNING: {script_name} exited with code {result.returncode}")


if __name__ == '__main__':
    print("=" * 60)
    print("  CyberGuard — Model Training Setup")
    print("=" * 60)

    run('train_sms_model.py')
    run('train_url_model.py')

    print("\n" + "=" * 60)
    print("  Setup complete!")
    print("  Now run: python manage.py migrate && python manage.py runserver")
    print("=" * 60)
