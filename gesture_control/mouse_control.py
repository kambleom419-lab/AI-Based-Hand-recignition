"""Control module: map the fingertip to the screen, smooth it and act."""

import time

import numpy as np
import pyautogui

from . import config


class CursorController:
    """Moves the cursor, clicks and scrolls through the operating system."""

    def __init__(self, frame_width, frame_height):
        pyautogui.FAILSAFE = config.FAILSAFE
        pyautogui.PAUSE = 0
        self.screen_width, self.screen_height = pyautogui.size()
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.prev_x = self.screen_width / 2
        self.prev_y = self.screen_height / 2
        self._last_left = 0.0
        self._last_right = 0.0
        self._last_scroll = 0.0

    def _map_to_screen(self, x_cam, y_cam):
        x = np.interp(
            x_cam,
            [config.FRAME_MARGIN, self.frame_width - config.FRAME_MARGIN],
            [0, self.screen_width],
        )
        y = np.interp(
            y_cam,
            [config.FRAME_MARGIN, self.frame_height - config.FRAME_MARGIN],
            [0, self.screen_height],
        )
        return x, y

    def move(self, x_cam, y_cam):
        target_x, target_y = self._map_to_screen(x_cam, y_cam)
        self.prev_x += (target_x - self.prev_x) / config.SMOOTHING
        self.prev_y += (target_y - self.prev_y) / config.SMOOTHING
        pyautogui.moveTo(int(self.prev_x), int(self.prev_y), duration=config.MOVE_DURATION)

    def click(self, button="left"):
        now = time.time()
        if button == "left":
            if now - self._last_left < config.CLICK_COOLDOWN:
                return
            self._last_left = now
        else:
            if now - self._last_right < config.CLICK_COOLDOWN:
                return
            self._last_right = now
        pyautogui.click(button=button)

    def scroll(self, direction):
        now = time.time()
        if now - self._last_scroll < config.SCROLL_DEBOUNCE:
            return
        self._last_scroll = now
        pyautogui.scroll(config.SCROLL_STEP * direction)
