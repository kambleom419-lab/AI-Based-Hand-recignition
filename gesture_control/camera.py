"""Input module: capture webcam frames and mirror them for natural interaction."""

import cv2

from . import config


class Camera:
    """Thin wrapper around ``cv2.VideoCapture`` returning mirrored frames."""

    def __init__(self, index=config.CAM_INDEX):
        self.cap = cv2.VideoCapture(index)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAM_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAM_HEIGHT)

    def is_opened(self):
        return self.cap.isOpened()

    def read(self):
        """Return the next mirrored frame, or ``None`` if the read failed."""
        ok, frame = self.cap.read()
        if not ok:
            return None
        if config.FLIP_HORIZONTAL:
            frame = cv2.flip(frame, 1)
        return frame

    def release(self):
        self.cap.release()
