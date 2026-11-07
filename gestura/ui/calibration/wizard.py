"""Calibration wizard.

Steps: camera position -> face -> neutral head pose (+ direction check) ->
hand position -> pinch thresholds -> gesture test -> confirm.
Runs with test mode forced on, so nothing is executed while calibrating.
"""

from __future__ import annotations

import time

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (QDialog, QHBoxLayout, QLabel, QProgressBar, QPushButton, QStackedWidget, QVBoxLayout,
                               QWidget)

from ...gestures.calibration import NeutralPoseCalibrator, PinchCalibrator
from ...gestures.hand_features import Pose
from ...services.tracking_service import Telemetry
from .. import theme
from ..widgets.common import VideoView, label

CAPTURE_S = 2.0


class _Step(QWidget):
    def __init__(self, title: str, text: str) -> None:
        super().__init__()
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(0, 0, 0, 0)
        self.lay.setSpacing(10)
        self.lay.addWidget(label(title, "bigValue"))
        self.lay.addWidget(label(text, "value", wrap=True))
        self.status = label("", "muted", wrap=True)
        self.lay.addWidget(self.status)
        self.done = False

    def ok(self, text: str) -> None:
        self.status.setText(f'<span style="color:{theme.SUCCESS}">✓</span> {text}')

    def wait(self, text: str) -> None:
        self.status.setText(f'<span style="color:{theme.WARN}">…</span> {text}')


class CalibrationWizard(QDialog):
    def __init__(self, app, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.app = app
        self.setWindowTitle("Calibrate Gestura")
        self.resize(1040, 620)
        self.draft = app.settings.copy_deep()
        self._prev_test_mode = app.safety.test_mode
        self._was_running = app.tracking.running
        self._tel: Telemetry | None = None
        self._capture: str | None = None
        self._capture_until = 0.0
        self._neutral = NeutralPoseCalibrator()
        self._pinch = PinchCalibrator()
        self._dir_phase = ""
        self._dir_since = 0.0
        self._seen: set[str] = set()

        root = QHBoxLayout(self)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(20)
        self.video = VideoView()
        root.addWidget(self.video, 3)
        right = QVBoxLayout()
        self.step_label = label("", "cardTitle")
        right.addWidget(self.step_label)
        self.stack = QStackedWidget()
        right.addWidget(self.stack, 1)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.hide()
        right.addWidget(self.progress)
        nav = QHBoxLayout()
        self.back_btn = QPushButton("Back")
        self.next_btn = QPushButton("Next")
        self.next_btn.setObjectName("primary")
        cancel = QPushButton("Cancel")
        cancel.setObjectName("ghost")
        cancel.clicked.connect(self.reject)
        self.back_btn.clicked.connect(lambda: self._go(self.stack.currentIndex() - 1))
        self.next_btn.clicked.connect(self._next)
        nav.addWidget(cancel)
        nav.addStretch(1)
        nav.addWidget(self.back_btn)
        nav.addWidget(self.next_btn)
        right.addLayout(nav)
        root.addLayout(right, 2)

        self.s_camera = _Step("Position your camera",
                              "Place the webcam at eye level, about 50–80 cm away. Your face and raised hand should "
                              "both be visible, with light in front of you rather than behind.")
        self.s_face = _Step("Face detection", "Look at the screen. Gestura needs to see your whole face.")
        self.s_neutral = _Step("Neutral head position",
                               "Sit comfortably and look at the centre of the screen. Press Capture and hold still "
                               "for two seconds. Then follow the prompts to turn and nod once.")
        self.capture_neutral = QPushButton("Capture neutral position")
        self.capture_neutral.clicked.connect(self._start_neutral)
        self.s_neutral.lay.addWidget(self.capture_neutral, 0, Qt.AlignmentFlag.AlignLeft)
        self.dir_label = label("", "value", wrap=True)
        self.s_neutral.lay.addWidget(self.dir_label)
        self.s_hand = _Step("Hand position",
                            "Raise your hand inside the grey rectangle and point at the screen with your index "
                            "finger (other fingers folded).")
        self.s_pinch = _Step("Pinch calibration",
                             "Step 1: point with your index finger, thumb relaxed, and press Capture open.\n"
                             "Step 2: pinch thumb and index tips together firmly, and press Capture pinch.")
        row = QHBoxLayout()
        self.cap_open = QPushButton("Capture open")
        self.cap_closed = QPushButton("Capture pinch")
        self.cap_open.clicked.connect(lambda: self._start_capture("open"))
        self.cap_closed.clicked.connect(lambda: self._start_capture("closed"))
        row.addWidget(self.cap_open)
        row.addWidget(self.cap_closed)
        row.addStretch(1)
        self.s_pinch.lay.addLayout(row)
        self.s_test = _Step("Try your gestures", "Each gesture ticks when it is recognised. Nothing is executed.")
        self.checks: dict[str, QLabel] = {}
        for key, text in (("hand.pinch", "Pinch (left click)"), ("hand.middle_pinch", "Thumb + middle (right click)"),
                          ("hand.scroll", "Two fingers up/down (scroll)"),
                          ("hand.volume", "Three fingers up/down (volume)"),
                          ("hand.drag", "Pinch and hold, move, release (drag)"),
                          ("hand.zoom", "Two open hands apart / together (zoom)"),
                          ("hand.palm_hold", "Hold open palm (pause)"),
                          ("head.turn_left", "Turn head left"), ("head.turn_right", "Turn head right"),
                          ("head.nod_down", "Nod down")):
            lab = label(f"○  {text}", "value")
            self.checks[key] = lab
            self.s_test.lay.addWidget(lab)
        self.s_done = _Step("All set", "Review the result and save your calibration.")
        self.summary = label("", "value", wrap=True)
        self.s_done.lay.addWidget(self.summary)
        self.steps = [self.s_camera, self.s_face, self.s_neutral, self.s_hand, self.s_pinch, self.s_test, self.s_done]
        for s in self.steps:
            s.lay.addStretch(1)
            self.stack.addWidget(s)

        app.set_test_mode(True)
        app.tracking.frame_ready.connect(self.video.set_image)
        app.tracking.telemetry.connect(self._on_tel)
        app.tracking.gesture.connect(self._on_gesture)
        if not app.tracking.running:
            app.start()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(100)
        self._go(0)

    # ------------------------------------------------------------ navigation
    def _go(self, i: int) -> None:
        i = max(0, min(len(self.steps) - 1, i))
        self.stack.setCurrentIndex(i)
        self.step_label.setText(f"STEP {i + 1} OF {len(self.steps)}")
        self.back_btn.setEnabled(i > 0)
        self.next_btn.setText("Save calibration" if i == len(self.steps) - 1 else "Next")
        if self.steps[i] is self.s_done:
            self._summarise()

    def _next(self) -> None:
        if self.stack.currentIndex() == len(self.steps) - 1:
            self.accept()
        else:
            self._go(self.stack.currentIndex() + 1)

    def accept(self) -> None:
        from ...config.settings import Settings

        try:  # re-validate as a whole (cross-field rules such as pinch hysteresis)
            final = Settings.model_validate(self.draft.model_dump())
        except ValueError as exc:
            self.summary.setText(f"Could not save: {exc}")
            return
        self.app.update_settings(final)
        super().accept()

    def done(self, result: int) -> None:  # called by accept/reject
        self._timer.stop()
        for sig, slot in ((self.app.tracking.frame_ready, self.video.set_image),
                          (self.app.tracking.telemetry, self._on_tel), (self.app.tracking.gesture, self._on_gesture)):
            try:
                sig.disconnect(slot)
            except (RuntimeError, TypeError):
                pass
        self.app.set_test_mode(self._prev_test_mode)
        if not self._was_running:
            self.app.stop()
        super().done(result)

    # ----------------------------------------------------------- live checks
    def _on_tel(self, t: Telemetry) -> None:
        self._tel = t
        now = time.monotonic()
        if self._capture == "neutral" and t.head.raw is not None:
            self._neutral.add(t.head.raw)
        elif self._capture in ("open", "closed") and t.hand.visible and t.hand.features is not None:
            (self._pinch.open if self._capture == "open" else self._pinch.closed).append(t.hand.features.thumb_index)
        if self._capture and now >= self._capture_until:
            self._finish_capture()
        self._direction_check(t, now)
        if t.hand.mode == "scroll" and self.steps[self.stack.currentIndex()] is self.s_test:
            # scrolling is a continuous stream (not a discrete gesture event)
            self._mark("hand.scroll")

    def _tick(self) -> None:
        t = self._tel
        step = self.steps[self.stack.currentIndex()]
        if self._capture:
            left = max(0.0, self._capture_until - time.monotonic())
            self.progress.show()
            self.progress.setValue(int((1 - left / CAPTURE_S) * 100))
        else:
            self.progress.hide()
        if t is None:
            step.wait("Waiting for the camera…") if step in (self.s_camera, self.s_face, self.s_hand) else None
            return
        if step is self.s_camera:
            if t.face_visible and t.hands_visible:
                step.ok("Face and hand visible. Good position.")
            elif t.face_visible:
                step.wait("Face visible. Raise a hand so it is visible too.")
            else:
                step.wait("No face detected yet. Adjust the camera or lighting.")
        elif step is self.s_face:
            step.ok("Face detected.") if t.face_visible else step.wait("Looking for your face…")
        elif step is self.s_hand:
            h = t.hand
            if h.visible and h.pose == Pose.POINT:
                step.ok(f"{h.handedness} hand pointing — tracking confidence {h.score:.0%}.")
            elif h.visible:
                step.wait(f"Hand found ({h.pose.value.replace('_', ' ')}). Point with your index finger.")
            elif t.hands_visible:
                step.wait(f"A hand is visible, but the control hand is set to "
                          f"'{self.app.settings.tracking.dominant_hand}' (Settings › Tracking).")
            else:
                step.wait("No hand detected.")

    def _start_capture(self, what: str) -> None:
        if what == "open":
            self._pinch.open = []
        elif what == "closed":
            self._pinch.closed = []
        self._capture = what
        self._capture_until = time.monotonic() + CAPTURE_S

    def _start_neutral(self) -> None:
        self._neutral = NeutralPoseCalibrator()
        self._dir_phase = ""
        self.dir_label.setText("")
        self._start_capture("neutral")

    def _finish_capture(self) -> None:
        what, self._capture = self._capture, None
        if what == "neutral":
            r = self._neutral.result()
            if not r.ok:
                self.s_neutral.wait(r.message)
                return
            h = self.draft.head
            h.neutral_yaw, h.neutral_pitch, h.neutral_roll = round(r.yaw, 2), round(r.pitch, 2), round(r.roll, 2)
            h.calibrated = True
            self.s_neutral.ok(f"Neutral saved (yaw {r.yaw:+.1f}°, pitch {r.pitch:+.1f}°, roll {r.roll:+.1f}°).")
            self._dir_phase = "right"
            self.dir_label.setText("Now turn your head to your RIGHT, then back.")
        elif what in ("open", "closed"):
            n_open, n_closed = len(self._pinch.open), len(self._pinch.closed)
            if n_open and n_closed:
                r = self._pinch.result()
                if r.ok:
                    self.draft.hand.pinch_on_ratio = r.on_ratio
                    self.draft.hand.pinch_off_ratio = r.off_ratio
                    self.draft.cursor.freeze_ratio = round(min(1.0, r.off_ratio + 0.02), 3)
                    self.s_pinch.ok(r.message)
                else:
                    self.s_pinch.wait(r.message)
            else:
                self.s_pinch.wait(f"Captured {'open' if n_open else 'pinch'} ({max(n_open, n_closed)} samples). "
                                  "Now capture the other one.")

    def _direction_check(self, t: Telemetry, now: float) -> None:
        """Learn the sign of yaw/pitch for this user and camera."""
        if not self._dir_phase or t.head.raw is None:
            return
        h = self.draft.head
        if self._dir_phase == "right":
            d = t.head.raw.yaw - h.neutral_yaw
            if abs(d) > 12:
                if not self._dir_since:
                    self._dir_since = now
                elif now - self._dir_since > 0.4:
                    h.invert_yaw = d < 0
                    self._dir_phase, self._dir_since = "down", 0.0
                    self.dir_label.setText("Now nod your head DOWN, then back.")
            else:
                self._dir_since = 0.0
        elif self._dir_phase == "down":
            d = t.head.raw.pitch - h.neutral_pitch
            if abs(d) > 9:
                if not self._dir_since:
                    self._dir_since = now
                elif now - self._dir_since > 0.4:
                    h.invert_pitch = d < 0
                    self._dir_phase, self._dir_since = "", 0.0
                    self.dir_label.setText(f'<span style="color:{theme.SUCCESS}">✓</span> Directions learned'
                                           + (" (left/right inverted for your camera)" if h.invert_yaw else "") + ".")
            else:
                self._dir_since = 0.0

    def _on_gesture(self, ev) -> None:
        name = ev.name
        for prefix, key in (("hand.volume", "hand.volume"), ("hand.drag", "hand.drag"), ("hand.zoom", "hand.zoom")):
            if name.startswith(prefix):
                name = key
        self._mark(name)

    def _mark(self, name: str) -> None:
        if name in self.checks and name not in self._seen:
            self._seen.add(name)
            text = self.checks[name].text()[3:]
            self.checks[name].setText(f'<span style="color:{theme.SUCCESS}">●</span>  {text}')

    def _summarise(self) -> None:
        d = self.draft
        lines = [
            f"Head neutral: {'calibrated' if d.head.calibrated else 'not calibrated'}"
            + (f" (yaw {d.head.neutral_yaw:+.1f}°, pitch {d.head.neutral_pitch:+.1f}°)" if d.head.calibrated else ""),
            f"Direction: left/right {'inverted' if d.head.invert_yaw else 'normal'}, "
            f"up/down {'inverted' if d.head.invert_pitch else 'normal'}",
            f"Pinch closes below {d.hand.pinch_on_ratio:.2f}, opens above {d.hand.pinch_off_ratio:.2f}",
            f"Gestures recognised in the test: {len(self._seen)} of {len(self.checks)}",
        ]
        self.summary.setText("<br>".join(lines))
