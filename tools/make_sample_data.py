"""Generate a small synthetic dataset in the MediaPipe keypoint CSV format.

This lets the whole train -> evaluate pipeline be run without downloading the
Kaggle dataset or owning a webcam. The generated landmarks are jittered copies
of four hand poses (Open, Close, Pointer, OK), matching the label names used by
the popular hand-gesture-recognition dataset, so the pipeline can be smoke
tested end to end.

    python tools/make_sample_data.py
    python tools/train_model.py --data data/sample
"""

import argparse
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gesture_control import config, features  # noqa: E402

LABELS = ["Open", "Close", "Pointer", "OK"]


def _base():
    return {
        0: (0.50, 0.90),  # wrist
        1: (0.42, 0.82), 2: (0.35, 0.75), 3: (0.30, 0.70), 4: (0.25, 0.65),  # thumb
        5: (0.45, 0.65), 6: (0.44, 0.50), 7: (0.43, 0.42), 8: (0.42, 0.35),  # index
        9: (0.50, 0.63), 10: (0.50, 0.47), 11: (0.50, 0.38), 12: (0.50, 0.31),  # middle
        13: (0.55, 0.65), 14: (0.56, 0.50), 15: (0.57, 0.42), 16: (0.58, 0.35),  # ring
        17: (0.60, 0.68), 18: (0.62, 0.55), 19: (0.63, 0.48), 20: (0.64, 0.42),  # pinky
    }


def _fold(landmarks, tip, pip):
    landmarks[tip] = (landmarks[pip][0], landmarks[pip][1] + 0.08)


def pose(kind):
    """Return 21 normalised (x, y) landmarks for a named pose."""
    lm = dict(_base())
    if kind == "open":
        return lm
    if kind == "close":
        for tip, pip in ((8, 6), (12, 10), (16, 14), (20, 18)):
            _fold(lm, tip, pip)
        lm[4] = (0.46, 0.74)  # thumb folded across the palm
        return lm
    if kind == "pointer":
        for tip, pip in ((12, 10), (16, 14), (20, 18)):
            _fold(lm, tip, pip)
        lm[4] = (0.46, 0.74)
        return lm
    if kind == "ok":
        lm[4] = (lm[8][0], lm[8][1])  # thumb tip pinched to the index tip
        return lm
    raise ValueError("unknown pose: {}".format(kind))


def landmarks_to_row(kind_id, kind):
    lm = pose(kind)
    jittered = [(x + np.random.normal(0, 0.01), y + np.random.normal(0, 0.01))
                for x, y in (lm[i] for i in range(21))]
    vector = features.pre_process_landmark(jittered)
    return [kind_id] + ["{:.6f}".format(v) for v in vector]


def main():
    parser = argparse.ArgumentParser(description="Generate a synthetic keypoint dataset.")
    parser.add_argument("--out", default=os.path.join(config.DATA_DIR, "sample"))
    parser.add_argument("--samples", type=int, default=150, help="samples per class")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    np.random.seed(args.seed)
    os.makedirs(args.out, exist_ok=True)

    data_path = os.path.join(args.out, "keypoint.csv")
    label_path = os.path.join(args.out, "keypoint_classifier_label.csv")

    with open(data_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        for class_id, kind in enumerate(["open", "close", "pointer", "ok"]):
            for _ in range(args.samples):
                writer.writerow(landmarks_to_row(class_id, kind))

    with open(label_path, "w", newline="", encoding="utf-8") as handle:
        for name in LABELS:
            handle.write(name + "\n")

    print("Wrote {} ({} rows) and {}".format(
        data_path, args.samples * len(LABELS), label_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
