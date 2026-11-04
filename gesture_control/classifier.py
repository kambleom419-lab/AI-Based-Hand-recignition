"""Classifier module: load a trained scikit-learn model and predict gestures.

The model is produced by ``tools/train_model.py`` and saved as a joblib bundle
containing the fitted estimator, the class labels and the feature dimension.
"""

import os

import joblib
import numpy as np

from . import config, features, gestures


class GestureClassifier:
    """Loads ``models/gesture_model.joblib`` and predicts a gesture label."""

    def __init__(self, path=config.MODEL_PATH):
        self.path = path
        self.model = None
        self.labels = []
        self.ready = False
        if os.path.exists(path):
            bundle = joblib.load(path)
            self.model = bundle["model"]
            self.labels = list(bundle["labels"])
            self.ready = True

    def predict_label(self, normalized_landmarks):
        """Return the predicted label text, or ``None`` if no model is loaded."""
        if not self.ready:
            return None
        vector = features.pre_process_landmark(normalized_landmarks).reshape(1, -1)
        index = int(self.model.predict(vector)[0])
        return self.labels[index]

    def recognise(self, normalized_landmarks, pixel_landmarks, handedness="Right"):
        """Fuse the ML prediction with the rule-based recogniser.

        Returns ``(gesture, source)`` where ``source`` is ``"ML:<label>"`` or
        ``"rules"``. The ML label wins when it maps to a known, non-idle gesture;
        otherwise the deterministic rules cover gestures outside the model's
        vocabulary (for example right-click and scroll).
        """
        if config.GESTURE_ENGINE == "ml" and self.ready:
            label = self.predict_label(normalized_landmarks)
            gesture = gestures.gesture_from_label(label)
            if gesture is not None and gesture is not gestures.Gesture.IDLE:
                return gesture, "ML:{}".format(label)

        return gestures.classify(pixel_landmarks, handedness), "rules"
