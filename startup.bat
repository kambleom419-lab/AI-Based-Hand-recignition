@echo off
setlocal
cd /d "%~dp0"

echo ==============================================
echo  AI Hand Gesture Control - startup
echo ==============================================

rem --- 1. Locate Python (prefer the "py" launcher) --------------------------
set "PY="
where py >nul 2>&1 && set "PY=py -3"
if not defined PY (
    where python >nul 2>&1 && set "PY=python"
)
if not defined PY (
    echo ERROR: Python 3.10-3.12 was not found on PATH.
    echo Install it from https://www.python.org/downloads/ and tick
    echo "Add python.exe to PATH" in the installer, then run this again.
    echo.
    pause
    exit /b 1
)
echo ==> Using Python:
%PY% --version

rem --- 2. Virtual environment -----------------------------------------------
if not exist ".venv\Scripts\python.exe" (
    echo ==> Creating virtual environment .venv
    %PY% -m venv .venv
    if errorlevel 1 (
        echo ERROR: failed to create the virtual environment.
        echo.
        pause
        exit /b 1
    )
)
call ".venv\Scripts\activate.bat"

rem --- 3. Dependencies - first run only, may take a few minutes -------------
if not exist ".venv\.deps_installed" (
    echo ==> Installing dependencies - first run, please wait
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: dependency installation failed.
        echo.
        pause
        exit /b 1
    )
    echo done> ".venv\.deps_installed"
) else (
    echo ==> Dependencies already installed
)

rem --- 4. Pretrained hand-landmarker model ----------------------------------
echo ==> Checking the pretrained hand-landmarker model
python -c "from gesture_control.hand_tracker import ensure_model_asset; ensure_model_asset(); print('    model ready')"

rem --- 5. Gesture classifier ------------------------------------------------
if not exist "models\gesture_model.joblib" (
    echo ==> No trained model found - training one on the bundled sample data
    if not exist "data\sample\keypoint.csv" (
        python tools\make_sample_data.py
    )
    python tools\train_model.py --data data\sample
)

rem --- 6. Run --------------------------------------------------------------
echo ==> Starting the application - press q or Esc in the window to quit
python main.py

echo.
echo Application closed.
pause
endlocal
