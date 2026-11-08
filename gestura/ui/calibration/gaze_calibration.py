# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura. Gestura is free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Full-screen eye calibration: follow a dot with the eyes, keep the head still.

9 dots train the gaze model (``gestures/gaze.py``), then 4 other dots measure how
accurate it really is, so the result shown to the user is an honest estimate.
Everything starts on its own (no click needed); Esc cancels, R retries.
Gesture commands are suspended while the screen is open.
"""

from __future__ import annotations

import time

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication, QKeyEvent, QPainter, QPen
from PySide6.QtWidgets import QWidget

from ...gestures import gaze
from .. import theme

INTRO_S = 3.5
SETTLE_S = 0.9
COLLECT_S = 1.3
MIN_SAMPLES_PER_POINT = 5
RESULT_CLOSE_S = 20.0


def rating(error_heights: float) -> tuple[str, str]:
    """(label, advice) for a mean error expressed in screen heights."""
    if error_heights <= 0.08:
        return "Good", "Good enough for most buttons. The head fine-tunes small targets."
    if error_heights <= 0.15:
        return "Fair", "Use larger targets (zoom in, bigger keyboard) or the hybrid pointer."
    return "Poor", ("Improve the light on your face, bring the webcam to eye level, keep your head "
                    "still and retry — or use the head pointer.")


class GazeCalibration(QWidget):
    done = Signal(bool)  # True when a model was saved

    def __init__(self, app, parent: QWidget | None = None, clock=time.monotonic) -> None:
        super().__init__(parent, Qt.WindowType.Window | Qt.WindowType.FramelessWindowHint
                         | Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowTitle("Gestura — eye calibration")
        self.app = app
        self._clock = clock
        self.points = list(gaze.CALIBRATION_POINTS) + list(gaze.VALIDATION_POINTS)
        self._timer = QTimer(self)
        self._timer.setInterval(30)
        self._timer.timeout.connect(self.tick)
        self.app.tracking.telemetry.connect(self._on_telemetry)
        self._restart()

    # ------------------------------------------------------------------ flow
    def _restart(self) -> None:
        self.phase = "intro"  # intro | settle | collect | result
        self.index = 0
        self.phase_t = self._clock()
        self.samples: list[tuple[int, tuple[float, float, float], float, float]] = []
        self.no_face = False
        self.result_text = ""
        self.result_ok = False
        self.model: gaze.GazeModel | None = None
        self.error = 0.0

    def start(self) -> None:
        """Show full screen on the primary display and begin."""
        screen = QGuiApplication.primaryScreen()
        if screen is not None:
            self.setGeometry(screen.geometry())
        self.app.tracking.set_suspended(True)
        if not self.app.tracking.running:
            self.app.start()
        self.showFullScreen()
        self.activateWindow()
        self._restart()
        self._timer.start()

    def finish(self, saved: bool) -> None:
        self._timer.stop()
        self.app.tracking.set_suspended(False)
        try:
            self.app.tracking.telemetry.disconnect(self._on_telemetry)
        except (RuntimeError, TypeError):
            pass
        self.close()
        self.done.emit(saved)

    def _on_telemetry(self, t) -> None:
        fs = t.face
        self.no_face = not fs.visible
        if self.phase != "collect" or not fs.visible or fs.features is None:
            return
        if fs.left_closed or fs.right_closed:
            return  # blinks corrupt the iris position
        self.samples.append((self.index, fs.features, fs.yaw, fs.pitch))

    def tick(self) -> None:
        now = self._clock()
        elapsed = now - self.phase_t
        if self.phase == "intro" and elapsed >= INTRO_S:
            self._enter("settle", now)
        elif self.phase == "settle" and elapsed >= SETTLE_S:
            self._enter("collect", now)
        elif self.phase == "collect" and elapsed >= COLLECT_S:
            got = sum(1 for i, *_ in self.samples if i == self.index)
            if got < MIN_SAMPLES_PER_POINT:
                self.phase_t = now  # wait on this dot until the face is seen
            else:
                self.index += 1
                if self.index == len(gaze.CALIBRATION_POINTS):
                    if not self._fit():
                        self._enter("result", now)
                        self.update()
                        return
                if self.index >= len(self.points):
                    self._validate()
                    self._enter("result", now)
                else:
                    self._enter("settle", now)
        elif self.phase == "result" and elapsed >= RESULT_CLOSE_S:
            self.finish(self.result_ok)
            return
        self.update()

    def _enter(self, phase: str, now: float) -> None:
        self.phase, self.phase_t = phase, now

    def _arrays(self, indices: range):
        rows = [s for s in self.samples if s[0] in indices]
        feats = np.array([r[1] for r in rows], dtype=float)
        targets = np.array([self.points[r[0]] for r in rows], dtype=float)
        yaw = np.array([r[2] for r in rows], dtype=float)
        pitch = np.array([r[3] for r in rows], dtype=float)
        return feats, targets, yaw, pitch

    def _fit(self) -> bool:
        feats, targets, yaw, pitch = self._arrays(range(len(gaze.CALIBRATION_POINTS)))
        try:
            self.model = gaze.fit(feats, targets, yaw, pitch)
        except ValueError as exc:
            self.result_ok = False
            self.result_text = f"Calibration failed: {exc}. Press R to retry or Esc to close."
            return False
        return True

    def _validate(self) -> None:
        assert self.model is not None
        n = len(gaze.CALIBRATION_POINTS)
        feats, targets, yaw, pitch = self._arrays(range(n, len(self.points)))
        aspect = self.width() / max(1, self.height()) if self.height() else 16 / 9
        half = self.app.settings.face.screen_half_angle_deg
        errors = gaze.point_errors(self.model, feats, targets, yaw, pitch, half, aspect)
        self.error = float(np.mean(errors)) if errors else 1.0
        label, advice = rating(self.error)
        px = self.error * max(1, self.height())
        s = self.app.settings.copy_deep()
        s.face.gaze_model = self.model.to_list()
        s.face.gaze_error = min(10.0, self.error)
        self.app.update_settings(s)
        self.result_ok = True
        self.result_text = (f"Saved. Accuracy: {label} — about {px:.0f} px ({self.error:.0%} of the screen height).\n"
                            f"{advice}\nPress Enter or Esc to close, R to calibrate again.")

    # ---------------------------------------------------------------- input
    def keyPressEvent(self, e: QKeyEvent) -> None:  # noqa: N802
        if e.key() == Qt.Key.Key_Escape:
            self.finish(self.result_ok)
        elif e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self.phase == "result":
            self.finish(self.result_ok)
        elif e.key() == Qt.Key.Key_R:
            self._restart()
        else:
            super().keyPressEvent(e)

    # -------------------------------------------------------------- drawing
    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor(theme.BG))
        w, h = self.width(), self.height()
        p.setPen(QColor(theme.TEXT))
        big = QFont()
        big.setPointSize(18)
        small = QFont()
        small.setPointSize(12)
        now = self._clock()
        if self.phase == "intro":
            p.setFont(big)
            left = max(0, INTRO_S - (now - self.phase_t))
            p.drawText(QRectF(0, h * 0.35, w, h * 0.3), int(Qt.AlignmentFlag.AlignCenter),
                       "Eye calibration\n\nKeep your head still and follow the dot with your eyes.\n"
                       f"Starting in {left:.0f} s…  (Esc to cancel)")
            return
        if self.phase == "result":
            p.setFont(big)
            p.setPen(QColor(theme.SUCCESS if self.result_ok else theme.WARN))
            p.drawText(QRectF(w * 0.1, h * 0.3, w * 0.8, h * 0.4),
                       int(Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap), self.result_text)
            return
        u, v = self.points[self.index]
        c = QPointF(u * w, v * h)
        elapsed = now - self.phase_t
        if self.phase == "settle":
            r = 34 - 22 * min(1.0, elapsed / SETTLE_S)
            p.setPen(QPen(QColor(theme.ACCENT), 3))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(c, r, r)
        else:
            p.setPen(QPen(QColor(theme.SUCCESS), 3))
            p.setBrush(Qt.BrushStyle.NoBrush)
            span = int(360 * 16 * min(1.0, elapsed / COLLECT_S))
            p.drawArc(QRectF(c.x() - 16, c.y() - 16, 32, 32), 90 * 16, -span)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#ffffff"))
        p.drawEllipse(c, 5, 5)
        p.setPen(QColor(theme.MUTED))
        p.setFont(small)
        validating = self.index >= len(gaze.CALIBRATION_POINTS)
        step = (f"Checking accuracy {self.index - len(gaze.CALIBRATION_POINTS) + 1}/{len(gaze.VALIDATION_POINTS)}"
                if validating else f"Point {self.index + 1}/{len(gaze.CALIBRATION_POINTS)}")
        if self.no_face:
            step += " — no face detected: face the camera"
        p.drawText(QRectF(0, h - 60, w, 40), int(Qt.AlignmentFlag.AlignCenter), step)
