"""Unit tests for the rule-based gesture classifier (no camera required)."""

from gesture_control import gestures
from gesture_control.gestures import Gesture

FINGERS = {"index": (8, 6), "middle": (12, 10), "ring": (16, 14), "pinky": (20, 18)}
XS = {"index": 160, "middle": 200, "ring": 240, "pinky": 280}


def make_landmarks(up=(), thumb_tip=(90, 410)):
    """Build 21 pixel landmarks; ``up`` lists extended fingers."""
    lm = [(200, 400)] * 21
    lm[0] = (200, 500)   # wrist
    lm[9] = (200, 400)   # middle MCP -> palm size 100
    lm[2] = (150, 450)   # thumb MCP
    lm[3] = (120, 430)   # thumb IP
    lm[4] = thumb_tip    # thumb tip
    for name, (tip, pip) in FINGERS.items():
        x = XS[name]
        lm[pip] = (x, 350)
        lm[tip] = (x, 300) if name in up else (x, 420)
    return lm


def test_fist_is_pause():
    lm = make_landmarks(up=(), thumb_tip=(150, 420))
    assert gestures.classify(lm, "Right") is Gesture.PAUSE


def test_index_only_is_move():
    lm = make_landmarks(up=("index",))
    assert gestures.classify(lm, "Right") is Gesture.MOVE


def test_two_fingers_is_scroll():
    lm = make_landmarks(up=("index", "middle"))
    assert gestures.classify(lm, "Right") is Gesture.SCROLL


def test_open_palm_is_idle():
    lm = make_landmarks(up=("index", "middle", "ring", "pinky"))
    assert gestures.classify(lm, "Right") is Gesture.IDLE


def test_index_thumb_pinch_is_left_click():
    lm = make_landmarks(up=("index",), thumb_tip=(160, 300))
    assert gestures.classify(lm, "Right") is Gesture.LEFT_CLICK


def test_middle_thumb_pinch_is_right_click():
    lm = make_landmarks(up=("index", "middle", "ring", "pinky"), thumb_tip=(200, 300))
    assert gestures.classify(lm, "Right") is Gesture.RIGHT_CLICK


def test_pinch_normalised_by_distance_tolerance():
    # A small hand far from the camera still registers the pinch.
    near = make_landmarks(up=("index",), thumb_tip=(160, 300))
    far = [(x * 0.5 + 100, y * 0.5 + 100) for x, y in near]
    assert gestures.classify(far, "Right") is Gesture.LEFT_CLICK


def test_label_mapping():
    assert gestures.gesture_from_label("Open") is Gesture.IDLE
    assert gestures.gesture_from_label("Pointing") is Gesture.MOVE
    assert gestures.gesture_from_label("fist") is Gesture.PAUSE
    assert gestures.gesture_from_label("OK") is Gesture.LEFT_CLICK
    assert gestures.gesture_from_label("unknown-label") is None
    assert gestures.gesture_from_label(None) is None
