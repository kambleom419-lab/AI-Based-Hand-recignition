"""Interface module: draw landmarks, the gesture label, FPS and pause state."""

import cv2
from mediapipe.tasks.python import vision


def draw_landmarks(frame, raw_landmarks):
    """Draw the 21 landmarks and their connections onto the BGR frame."""
    vision.drawing_utils.draw_landmarks(
        frame,
        raw_landmarks,
        connections=vision.HandLandmarksConnections.HAND_CONNECTIONS,
    )


def draw_status(frame, gesture_name, source, fps, paused, ml_ready):
    height, width = frame.shape[:2]
    cv2.putText(
        frame, "Gesture: {}".format(gesture_name), (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2,
    )
    engine = "ML" if ml_ready else "rules"
    cv2.putText(
        frame, "Engine: {} ({})".format(engine, source), (10, 60),
        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 200, 0), 2,
    )
    cv2.putText(
        frame, "FPS: {:.1f}".format(fps), (10, 90),
        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2,
    )
    if paused:
        cv2.putText(
            frame, "PAUSED", (width // 2 - 90, height // 2),
            cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 255), 3,
        )
    return frame
