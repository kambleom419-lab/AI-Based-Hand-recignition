"""Orchestrator: wire the per-frame pipeline together and run the loop."""

import time

import cv2

from . import config, gestures, ui
from .camera import Camera
from .classifier import GestureClassifier
from .hand_tracker import HandTracker
from .mouse_control import CursorController


def run():
    camera = Camera()
    if not camera.is_opened():
        print("ERROR: could not open the webcam (index {}).".format(config.CAM_INDEX))
        return 1

    tracker = HandTracker()
    classifier = GestureClassifier()
    if classifier.ready:
        print("Loaded ML model: {} ({} classes)".format(classifier.path, len(classifier.labels)))
    else:
        print("No ML model found at {} - using rule-based gestures.".format(config.MODEL_PATH))

    frame = camera.read()
    height = frame.shape[0] if frame is not None else config.CAM_HEIGHT
    width = frame.shape[1] if frame is not None else config.CAM_WIDTH
    controller = CursorController(width, height)

    prev_time = time.time()
    prev_gesture = gestures.Gesture.NONE

    try:
        while True:
            frame = camera.read()
            if frame is None:
                print("ERROR: failed to read a frame from the webcam.")
                break
            height, width = frame.shape[:2]

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = tracker.process(rgb)

            gesture = gestures.Gesture.NONE
            source = "-"
            if result is not None:
                gesture, source = classifier.recognise(
                    result.norm, result.landmarks, result.handedness
                )

                if gesture is gestures.Gesture.MOVE:
                    x, y = result.landmarks[gestures.INDEX_TIP]
                    controller.move(x, y)
                elif gesture is gestures.Gesture.LEFT_CLICK:
                    if prev_gesture is not gestures.Gesture.LEFT_CLICK:
                        controller.click("left")
                elif gesture is gestures.Gesture.RIGHT_CLICK:
                    if prev_gesture is not gestures.Gesture.RIGHT_CLICK:
                        controller.click("right")
                elif gesture is gestures.Gesture.SCROLL:
                    y = result.landmarks[gestures.MIDDLE_TIP][1]
                    controller.scroll(1 if y < height / 2 else -1)

                ui.draw_landmarks(frame, result.raw)

            now = time.time()
            fps = 1.0 / max(now - prev_time, 1e-6)
            prev_time = now

            paused = gesture is gestures.Gesture.PAUSE
            ui.draw_status(frame, gesture.value, source, fps, paused, classifier.ready)

            cv2.imshow(config.WINDOW_NAME, frame)
            if cv2.waitKey(1) & 0xFF in (config.EXIT_KEY, config.ESC_KEY):
                break

            prev_gesture = gesture
    finally:
        camera.release()
        tracker.close()
        cv2.destroyAllWindows()

    return 0
