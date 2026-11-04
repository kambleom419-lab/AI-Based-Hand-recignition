"""Landmark module: wrap the pretrained MediaPipe HandLandmarker (Tasks API).

MediaPipe 1.x removed the legacy ``mp.solutions`` API, so this uses the Tasks API
(``mediapipe.tasks.python.vision.HandLandmarker``) with the pretrained
``hand_landmarker.task`` model asset. The model is used as provided; this project
does not train a hand detector from scratch.

Returns normalised landmarks (for the ML feature extractor) and pixel landmarks
(for drawing and cursor mapping), plus the handedness label.
"""

import os
import time
import urllib.request
from dataclasses import dataclass

import mediapipe as mp
from mediapipe.tasks.python import vision

from . import config


@dataclass
class HandResult:
    """Detection result for one hand."""

    norm: list  # list[tuple[float, float]] of length 21, values in [0, 1]
    landmarks: list  # list[tuple[int, int]] of length 21, pixel coordinates
    handedness: str  # "Left" or "Right"
    raw: list  # list of NormalizedLandmark (for drawing)


def ensure_model_asset():
    """Download the pretrained .task model the first time it is needed."""
    if os.path.exists(config.MODEL_ASSET_PATH):
        return
    os.makedirs(os.path.dirname(config.MODEL_ASSET_PATH), exist_ok=True)
    print("Downloading hand-landmarker model to {} ...".format(config.MODEL_ASSET_PATH))
    urllib.request.urlretrieve(config.MODEL_ASSET_URL, config.MODEL_ASSET_PATH)


class HandTracker:
    """Detects one hand and returns its 21 landmarks."""

    def __init__(self):
        ensure_model_asset()
        options = vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=config.MODEL_ASSET_PATH),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=config.MAX_NUM_HANDS,
            min_hand_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
            min_hand_presence_confidence=config.MIN_HAND_PRESENCE_CONFIDENCE,
            min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE,
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)
        self._last_timestamp = -1

    def process(self, rgb_frame):
        """Return a :class:`HandResult`, or ``None`` if no hand is found."""
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        timestamp = int(time.time() * 1000)
        if timestamp <= self._last_timestamp:  # VIDEO mode needs increasing stamps
            timestamp = self._last_timestamp + 1
        self._last_timestamp = timestamp

        result = self.landmarker.detect_for_video(image, timestamp)
        if not result.hand_landmarks:
            return None

        hand = result.hand_landmarks[0]
        height, width = rgb_frame.shape[:2]
        norm = [(lm.x, lm.y) for lm in hand]
        landmarks = [(int(x * width), int(y * height)) for x, y in norm]

        handedness = "Right"
        if result.handedness:
            handedness = result.handedness[0][0].category_name

        return HandResult(norm, landmarks, handedness, hand)

    def close(self):
        self.landmarker.close()
