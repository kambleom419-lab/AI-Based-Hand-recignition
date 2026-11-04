"""Runtime evaluation harness: record gesture trials and report metrics.

Runs the live pipeline (no cursor/clicks are issued) and lets you label each
trial with a number key. Press the key for the gesture you are actually making;
the script records what the system predicted at that moment. On exit it writes a
CSV and prints accuracy, per-class precision/recall/F1, a confusion matrix and
FPS statistics - the numbers that fill the report's evaluation tables.

Keys:
    1 = Idle (open palm)   2 = Move (index)   3 = Left click (index pinch)
    4 = Right click        5 = Scroll        6 = Pause (fist)
    q / Esc = finish and report
"""

import argparse
import csv
import os
import sys
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gesture_control import config, gestures, ui  # noqa: E402
from gesture_control.camera import Camera  # noqa: E402
from gesture_control.classifier import GestureClassifier  # noqa: E402
from gesture_control.hand_tracker import HandTracker  # noqa: E402

KEY_TO_GESTURE = {
    ord("1"): gestures.Gesture.IDLE,
    ord("2"): gestures.Gesture.MOVE,
    ord("3"): gestures.Gesture.LEFT_CLICK,
    ord("4"): gestures.Gesture.RIGHT_CLICK,
    ord("5"): gestures.Gesture.SCROLL,
    ord("6"): gestures.Gesture.PAUSE,
}
ORDER = [gestures.Gesture.IDLE, gestures.Gesture.MOVE, gestures.Gesture.LEFT_CLICK,
         gestures.Gesture.RIGHT_CLICK, gestures.Gesture.SCROLL, gestures.Gesture.PAUSE]


def report(trials, fps_samples):
    if not trials:
        print("No trials recorded.")
        return
    truth = [t[0] for t in trials]
    pred = [t[1] for t in trials]
    names = [g.name for g in ORDER]

    correct = sum(1 for a, b in zip(truth, pred) if a == b)
    accuracy = correct / len(trials)

    matrix = np.zeros((len(ORDER), len(ORDER)), dtype=int)
    for a, b in zip(truth, pred):
        matrix[ORDER.index(gestures.Gesture[a])][ORDER.index(gestures.Gesture[b])] += 1

    print("\n=== Evaluation ===")
    print("Trials: {}   Correct: {}   Accuracy: {:.3f}".format(len(trials), correct, accuracy))
    if fps_samples:
        print("FPS: avg {:.1f}  min {:.1f}  max {:.1f}".format(
            float(np.mean(fps_samples)), float(np.min(fps_samples)), float(np.max(fps_samples))))

    print("\n{:<12} {:>10} {:>10} {:>10}".format("gesture", "precision", "recall", "f1"))
    for i, name in enumerate(names):
        tp = matrix[i][i]
        fp = matrix[:, i].sum() - tp
        fn = matrix[i, :].sum() - tp
        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
        print("{:<12} {:>10.3f} {:>10.3f} {:>10.3f}".format(name, precision, recall, f1))

    print("\nConfusion matrix (rows = true, cols = predicted):")
    print("{:<12}".format("") + "".join("{:>8}".format(n) for n in names))
    for i, name in enumerate(names):
        print("{:<12}".format(name) + "".join("{:>8}".format(v) for v in matrix[i]))


def main():
    parser = argparse.ArgumentParser(description="Record gesture trials and report accuracy.")
    parser.add_argument("--out", default=os.path.join(config.DATA_DIR, "evaluation_results.csv"))
    args = parser.parse_args()

    camera = Camera()
    if not camera.is_opened():
        print("ERROR: could not open the webcam.")
        return 1

    tracker = HandTracker()
    classifier = GestureClassifier()
    print("Evaluating with engine:", "ML" if classifier.ready else "rules")

    trials = []
    fps_samples = []
    prev_time = time.time()
    prev_gesture = gestures.Gesture.NONE

    try:
        while True:
            frame = camera.read()
            if frame is None:
                break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            result = tracker.process(rgb)

            if result is not None:
                gesture, source = classifier.recognise(
                    result.norm, result.landmarks, result.handedness)
                ui.draw_landmarks(frame, result.raw)
            else:
                gesture, source = gestures.Gesture.NONE, "-"

            now = time.time()
            fps = 1.0 / max(now - prev_time, 1e-6)
            prev_time = now
            fps_samples.append(fps)

            ui.draw_status(frame, gesture.value, source, fps, False, classifier.ready)
            cv2.putText(frame, "Label a trial: 1-6   q=finish", (10, frame.shape[0] - 15),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.putText(frame, "Recorded: {}".format(len(trials)), (10, frame.shape[0] - 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            cv2.imshow(config.WINDOW_NAME, frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (config.EXIT_KEY, config.ESC_KEY):
                break
            if key in KEY_TO_GESTURE:
                truth = KEY_TO_GESTURE[key]
                trials.append((truth.name, gesture.name, fps))
    finally:
        camera.release()
        tracker.close()
        cv2.destroyAllWindows()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["true_gesture", "predicted_gesture", "fps"])
        writer.writerows(trials)
    print("Saved trials -> {}".format(args.out))

    report(trials, fps_samples)
    return 0


if __name__ == "__main__":
    sys.exit(main())
