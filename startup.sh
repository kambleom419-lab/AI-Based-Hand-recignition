#!/usr/bin/env bash
#
# startup.sh - one-command setup and launch for the
# AI-Based Hand Gesture Recognition & Touchless Computer Control System.
#
# Usage (Linux / macOS / Git Bash / WSL):
#     bash startup.sh
#
# It will:
#   1. check for Python 3.10-3.12
#   2. create a virtual environment in .venv (first run only)
#   3. install the dependencies (first run only)
#   4. download the MediaPipe hand-landmarker model
#   5. train a gesture classifier on the sample data if none exists yet
#   6. launch the application

set -e
cd "$(dirname "$0")"

echo "=============================================="
echo " AI Hand Gesture Control - startup"
echo "=============================================="

# --- 1. Locate Python ---------------------------------------------------------
PYTHON=""
for candidate in python3 python; do
    if command -v "$candidate" >/dev/null 2>&1; then
        PYTHON="$candidate"
        break
    fi
done
if [ -z "$PYTHON" ]; then
    echo "ERROR: Python 3.10-3.12 was not found on PATH."
    echo "Install it from https://www.python.org/downloads/ and run this again."
    exit 1
fi
echo "==> Python: $($PYTHON --version) ($PYTHON)"

# --- 2. Virtual environment ---------------------------------------------------
if [ ! -d ".venv" ]; then
    echo "==> Creating virtual environment (.venv)"
    "$PYTHON" -m venv .venv
fi
if [ -f ".venv/bin/activate" ]; then
    . ".venv/bin/activate"          # Linux / macOS
elif [ -f ".venv/Scripts/activate" ]; then
    . ".venv/Scripts/activate"      # Windows (Git Bash / WSL)
fi

# --- 3. Dependencies ----------------------------------------------------------
if [ ! -f ".venv/.deps_installed" ]; then
    echo "==> Installing dependencies (this happens once, may take a few minutes)"
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    touch ".venv/.deps_installed"
else
    echo "==> Dependencies already installed"
fi

# --- 4. Pretrained hand-landmarker model -------------------------------------
echo "==> Checking the pretrained hand-landmarker model"
python - <<'PY'
from gesture_control.hand_tracker import ensure_model_asset
ensure_model_asset()
print("    model ready")
PY

# --- 5. Gesture classifier ----------------------------------------------------
if [ ! -f "models/gesture_model.joblib" ]; then
    echo "==> No trained model found - training one on the bundled sample data"
    if [ ! -f "data/sample/keypoint.csv" ]; then
        python tools/make_sample_data.py
    fi
    python tools/train_model.py --data data/sample
    echo "    (For real accuracy, train on the Kaggle dataset:"
    echo "     python tools/download_data.py && python tools/train_model.py --data data/raw)"
fi

# --- 6. Run -------------------------------------------------------------------
echo "==> Starting the application - press 'q' or Esc in the window to quit"
python main.py
