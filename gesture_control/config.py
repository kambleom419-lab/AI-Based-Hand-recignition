"""Central configuration: camera/model settings, gesture thresholds, ML paths.

Every tunable value used by the system lives here so the gesture logic stays
transparent and easy to explain in the project report.
"""

import os

# Project root = parent directory of this package.
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Camera (Input module) ---------------------------------------------------
CAM_INDEX = 0
CAM_WIDTH = 640
CAM_HEIGHT = 480
FLIP_HORIZONTAL = True  # mirror the frame for natural, selfie-style interaction

# --- MediaPipe HandLandmarker (Landmark module, Tasks API) ------------------
# MediaPipe 1.x removed the legacy solutions API; we use the Tasks API with a
# pretrained .task model asset (auto-downloaded to models/ on first run).
MAX_NUM_HANDS = 1  # single-hand scope for this version
MIN_DETECTION_CONFIDENCE = 0.7
MIN_HAND_PRESENCE_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5
MODEL_ASSET_PATH = os.path.join(PROJECT_ROOT, "models", "hand_landmarker.task")
MODEL_ASSET_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/1/hand_landmarker.task"
)

# --- Cursor control (Control module) ----------------------------------------
FRAME_MARGIN = 100  # px: lets the user reach screen edges without hitting the border
SMOOTHING = 5  # larger = steadier but slower cursor (position += (target - position) / k)
MOVE_DURATION = 0  # pyautogui move duration (0 = instant)
FAILSAFE = True  # slam the mouse into a screen corner to abort instantly

# --- Gestures (Gesture module) ----------------------------------------------
PINCH_THRESHOLD = 0.35  # pinch distance normalised by palm size (dist 0-9)
CLICK_COOLDOWN = 0.4  # seconds: minimum gap between two clicks on the same button
SCROLL_STEP = 40  # wheel units per scroll event
SCROLL_DEBOUNCE = 0.15  # seconds between scroll events

# --- Machine learning ---------------------------------------------------------
# Which recogniser drives the actions: "ml" (classifier + rule fallback) or "rules".
GESTURE_ENGINE = "ml"
MODEL_PATH = os.path.join(PROJECT_ROOT, "models", "gesture_model.joblib")
METRICS_PATH = os.path.join(PROJECT_ROOT, "models", "metrics.json")

# Kaggle dataset used to train the classifier (override with --dataset).
DEFAULT_KAGGLE_DATASET = "omarainajmi/hand-gesture-recognition-mediapipe"
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")

# Dataset label -> Gesture enum name. Keys are matched case-insensitively and
# with spaces/dashes normalised to underscores. Extend this when you train on a
# dataset with different label names.
POSE_TO_GESTURE = {
    "open": "IDLE",
    "open_hand": "IDLE",
    "palm": "IDLE",
    "close": "PAUSE",
    "closed": "PAUSE",
    "fist": "PAUSE",
    "closed_fist": "PAUSE",
    "pointer": "MOVE",
    "pointing": "MOVE",
    "point": "MOVE",
    "index": "MOVE",
    "one": "MOVE",
    "ok": "LEFT_CLICK",
    "pinch": "LEFT_CLICK",
    "peace": "SCROLL",
    "two": "SCROLL",
    "victory": "SCROLL",
    "scroll": "SCROLL",
    "right_click": "RIGHT_CLICK",
    "right": "RIGHT_CLICK",
    "middle_pinch": "RIGHT_CLICK",
}

# --- Interaction -------------------------------------------------------------
WINDOW_NAME = "AI Hand Gesture Control"
EXIT_KEY = ord("q")
ESC_KEY = 27
