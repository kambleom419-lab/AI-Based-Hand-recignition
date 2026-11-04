# AI-Based Hand Gesture Recognition and Touchless Computer Control System

A software-only system that lets you control a computer with hand gestures seen
through an ordinary webcam. It uses **MediaPipe HandLandmarker** (Tasks API) for
real-time hand-landmark detection, a **machine-learning classifier** (scikit-learn:
SVM / KNN / MLP) trained on hand-landmark data to recognise gestures, and
**PyAutoGUI** to turn those gestures into cursor movement, clicks and scrolling.

> Mini Project (MDM-331-ETC) — PCCOER, AY 2026–27, Term I.
> The hand-landmark model is pretrained (MediaPipe); the project trains **a gesture
> classifier** on landmark features, it does not train a detector from scratch.

---

## Quick start (clone and run)

```bash
git clone <your-repo-url>
cd "AI Based Hand recignition"
```

- **Windows:** double-click **`startup.bat`**.
- **Linux / macOS:** `bash startup.sh`.

Either script creates the virtual environment, installs the dependencies, downloads
the hand model, trains a sample classifier if none exists, and launches the app.
You need Python 3.10–3.12, a webcam, and internet for the first run.

The trained model (`models/gesture_model.joblib`) and the pretrained hand model
(`models/hand_landmarker.task`) ship with the repo, so a fresh clone runs without
extra downloads.

---

## Problem statement

Operating a computer through physical input devices (mouse, keyboard, touchpad) is
not always convenient or hygienic and is difficult for some users. A software system
is required that detects the user's hand through an ordinary webcam, recognises a set
of hand gestures in real time and translates them into cursor and click operations.

## Solution

Capture webcam frames → detect 21 hand landmarks (MediaPipe) → classify the gesture
with a trained ML model (rule-based logic as a fallback) → map the gesture to a
cursor/click/scroll action (PyAutoGUI) → preview window with landmarks, the gesture
label, the engine used and FPS.

---

## Architecture

```
Webcam ─▶ Input module ─▶ Landmark module ─▶ Gesture module ─▶ Control module ─▶ OS
 (capture+mirror)   (MediaPipe, 21 pts)  (ML classifier      (map, smooth,     (cursor/
                                          + rule fallback)     click, scroll)    click/scroll)
                              │                  │
                              └─────┐   ┌────────┘
                                    ▼   ▼
                              Interface module (landmarks, label, FPS)
```

| Module | File | Responsibility |
|---|---|---|
| Input | `gesture_control/camera.py` | Capture and mirror webcam frames |
| Landmark | `gesture_control/hand_tracker.py` | MediaPipe HandLandmarker (Tasks API) → 21 landmarks + handedness |
| Features | `gesture_control/features.py` | Landmark → 42-value ML feature vector |
| Gesture | `gesture_control/gestures.py` | Rule-based classification + label mapping |
| Classifier | `gesture_control/classifier.py` | Load the trained model and predict |
| Control | `gesture_control/mouse_control.py` | Screen mapping, smoothing, clicks, scroll |
| Interface | `gesture_control/ui.py` | Landmarks, gesture label, engine, FPS |
| Orchestrator | `gesture_control/app.py` | The per-frame loop |
| Config | `gesture_control/config.py` | All thresholds and paths |

## Gestures

| Gesture | Rule | Action |
|---|---|---|
| Closed fist | all fingers folded | **Pause** |
| Index–thumb pinch | `dist(4,8)/palm < 0.35` | **Left click** |
| Middle–thumb pinch | `dist(4,12)/palm < 0.35` | **Right click** |
| Index + middle up | two fingers extended | **Scroll** up / down |
| Index up | only index extended | **Move cursor** |
| Open palm | all five extended | Idle |

Priority when several match: **pause → pinch → scroll → move**.

---

## Project layout

```
main.py                     run the app
requirements.txt
gesture_control/            application package (see table above)
tools/
  download_data.py          pull the Kaggle dataset (Kaggle CLI)
  make_sample_data.py       generate a synthetic keypoint dataset (no webcam needed)
  train_model.py            train & compare SVM / KNN / MLP, save the best
  evaluate.py               record live gesture trials and report metrics
data/                       datasets (raw + generated)
models/                     trained model + metrics + confusion matrices
```

---

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate            # Windows  (source .venv/bin/activate on Linux/macOS)
pip install -r requirements.txt
```

Python 3.10–3.12 is supported (3.11 recommended). Requires **NumPy 2.x** (MediaPipe
1.x / OpenCV 5). On first run the pretrained `hand_landmarker.task` model (~8 MB) is
downloaded automatically to `models/` (MediaPipe 1.x uses the Tasks API — the legacy
`mp.solutions` API no longer exists).

## Training the gesture classifier

### 1. Get the data (Kaggle)

Option A — real dataset (recommended):

```bash
pip install kaggle
# Put your API token at ~/.kaggle/kaggle.json  (Kaggle → Settings → API → Create New Token)
python tools/download_data.py
```

The default dataset is `omarainajmi/hand-gesture-recognition-mediapipe`
(MediaPipe keypoints). Any dataset in the same format works — override with
`--dataset owner/dataset-name`. The loader auto-detects `*keypoint*.csv` (feature
data) and `*label*.csv` (labels), and drops `z` automatically for 63-column files.

Option B — synthetic sample (no download, for a quick smoke test):

```bash
python tools/make_sample_data.py         # writes data/sample/
```

### 2. Train and compare models

```bash
python tools/train_model.py --data data/raw       # or data/sample
```

This trains an **SVM**, a **KNN** and an **MLP (neural network)**, prints an
accuracy / precision / recall / F1 comparison, writes a confusion-matrix PNG per
model, and saves the best one to `models/gesture_model.joblib` plus
`models/metrics.json`. The app loads that model automatically.

## Running the app

```bash
python main.py
```

The preview shows the 21 landmarks, the recognised gesture, whether the **ML** or
**rules** engine produced it, and the FPS. Exit with `q` or `Esc`.

* The ML model drives a gesture when its label maps to a known action; the
  deterministic rules cover gestures outside the model's vocabulary (e.g. right-click
  and scroll). Set `GESTURE_ENGINE = "rules"` in `config.py` to disable ML.
* Safety: the fist gesture pauses everything, and PyAutoGUI's fail-safe aborts if you
  slam the mouse into a screen corner.

## Evaluating (fills the report's tables)

```bash
python tools/evaluate.py
```

Make each gesture and press the matching key (`1`..`6`) to record a trial. On exit it
prints accuracy, per-class precision/recall/F1, a confusion matrix and FPS statistics,
and saves the raw trials to `data/evaluation_results.csv`.

---

## Tuning

All thresholds live in `gesture_control/config.py`: `PINCH_THRESHOLD`, `FRAME_MARGIN`,
`SMOOTHING`, `CLICK_COOLDOWN`, `SCROLL_STEP`, camera resolution, MediaPipe confidences
and the label→gesture map (`POSE_TO_GESTURE`). Record the values you settle on below.

| Setting | Value used | Notes |
|---|---|---|
| Pinch threshold | | |
| Frame margin | | |
| Smoothing k | | |
| Click cooldown | | |

## Limitations

Recognition depends on lighting, background, camera quality and hand distance; one
hand only; rule thresholds may need per-user tuning; frame rate depends on hardware.
Not intended for safety-critical use. Frames are processed locally and not stored.

## References

1. F. Zhang et al., *MediaPipe Hands: On-device Real-time Hand Tracking*, arXiv:2006.10214, 2020.
2. C. Lugaresi et al., *MediaPipe: A Framework for Building Perception Pipelines*, arXiv:1906.08172, 2019.
3. S. S. Rautaray and A. Agrawal, *Vision based hand gesture recognition for HCI: a survey*, AI Review, 2015.
4. MediaPipe Hand Landmarker docs — https://ai.google.dev/edge/mediapipe/solutions/vision/hand_landmarker
5. OpenCV — https://docs.opencv.org/  ·  PyAutoGUI — https://pyautogui.readthedocs.io/  ·  NumPy — https://numpy.org/doc/
