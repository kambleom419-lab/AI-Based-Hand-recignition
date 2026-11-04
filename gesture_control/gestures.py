"""Gesture module: rule-based classification and dataset-label mapping.

Two recognisers share this module:

* a transparent, rule-based classifier built from finger states and normalised
  pinch distances (used directly, and as a fallback when no ML model is loaded);
* a mapping from a trained ML model's label text to a :class:`Gesture`.
"""

from enum import Enum
from math import hypot

from . import config


class Gesture(Enum):
    NONE = "None"
    MOVE = "Move cursor"
    LEFT_CLICK = "Left click"
    RIGHT_CLICK = "Right click"
    SCROLL = "Scroll"
    PAUSE = "Pause"
    IDLE = "Idle"


# Landmark indices (MediaPipe Hands).
WRIST = 0
THUMB_MCP, THUMB_IP, THUMB_TIP = 2, 3, 4
INDEX_PIP, INDEX_TIP = 6, 8
MIDDLE_MCP, MIDDLE_PIP, MIDDLE_TIP = 9, 10, 12
RING_PIP, RING_TIP = 14, 16
PINKY_PIP, PINKY_TIP = 18, 20


def _distance(a, b):
    return hypot(a[0] - b[0], a[1] - b[1])


def finger_states(landmarks, handedness="Right"):
    """Return which of the five fingers are extended (up)."""
    # Non-thumb fingers: extended when the tip sits above the PIP joint
    # (image y grows downward, so "above" means a smaller y).
    states = {
        "index": landmarks[INDEX_TIP][1] < landmarks[INDEX_PIP][1],
        "middle": landmarks[MIDDLE_TIP][1] < landmarks[MIDDLE_PIP][1],
        "ring": landmarks[RING_TIP][1] < landmarks[RING_PIP][1],
        "pinky": landmarks[PINKY_TIP][1] < landmarks[PINKY_PIP][1],
    }
    # Thumb: horizontal comparison against the IP joint; direction depends on
    # the hand. The frame is mirrored before detection, so the label may need
    # flipping after the first run - verify on the live preview.
    if handedness == "Right":
        states["thumb"] = landmarks[THUMB_TIP][0] < landmarks[THUMB_IP][0]
    else:
        states["thumb"] = landmarks[THUMB_TIP][0] > landmarks[THUMB_IP][0]
    return states


def pinch_distances(landmarks):
    """Index/middle pinch distances normalised by palm size (wrist -> middle MCP)."""
    palm = max(_distance(landmarks[WRIST], landmarks[MIDDLE_MCP]), 1e-6)
    return {
        "index": _distance(landmarks[THUMB_TIP], landmarks[INDEX_TIP]) / palm,
        "middle": _distance(landmarks[THUMB_TIP], landmarks[MIDDLE_TIP]) / palm,
    }


def classify(landmarks, handedness="Right"):
    """Rule-based gesture classification with the project's priority order:
    pause -> pinch -> scroll -> move.
    """
    states = finger_states(landmarks, handedness)
    pinches = pinch_distances(landmarks)
    four = [states["index"], states["middle"], states["ring"], states["pinky"]]

    # 1. Fist (nothing extended) -> pause everything.
    if not any(four) and not states["thumb"]:
        return Gesture.PAUSE

    # 2 & 3. Pinches -> clicks (thumb tip distance to a fingertip).
    if pinches["index"] < config.PINCH_THRESHOLD:
        return Gesture.LEFT_CLICK
    if pinches["middle"] < config.PINCH_THRESHOLD:
        return Gesture.RIGHT_CLICK

    # 4. Index + middle extended, ring & pinky folded -> scroll.
    if states["index"] and states["middle"] and not states["ring"] and not states["pinky"]:
        return Gesture.SCROLL

    # 5. Only the index extended -> move the cursor.
    if states["index"] and not states["middle"] and not states["ring"] and not states["pinky"]:
        return Gesture.MOVE

    # Open palm and anything unrecognised -> idle.
    return Gesture.IDLE


def gesture_from_label(label):
    """Map a trained model's label text to a Gesture, or ``None`` if unmapped."""
    if label is None:
        return None
    key = str(label).strip().lower().replace(" ", "_").replace("-", "_")
    name = config.POSE_TO_GESTURE.get(key)
    if name is None:
        return None
    return Gesture[name]
