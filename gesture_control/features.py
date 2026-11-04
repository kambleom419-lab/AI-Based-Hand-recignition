"""Feature extraction: turn 21 hand landmarks into a fixed-length vector.

Uses the same preprocessing as the MediaPipe hand-gesture datasets (kinivi /
Kazuhito00): coordinates are made relative to the wrist and rescaled so the
largest absolute value is 1. This makes the features translation- and
scale-invariant, so the trained classifier works whether the hand is close to
or far from the camera. Output: 42 features (21 landmarks x, y).
"""

import numpy as np

FEATURE_DIM = 42


def pre_process_landmark(normalized_landmarks):
    """Return a 42-value feature vector from 21 normalised (x, y) landmarks."""
    points = np.asarray(normalized_landmarks, dtype=np.float64).reshape(-1, 2)
    points = points - points[0]  # relative to the wrist (landmark 0)
    flat = points.flatten()
    max_value = float(np.max(np.abs(flat)))
    if max_value == 0.0:
        max_value = 1.0
    return flat / max_value
