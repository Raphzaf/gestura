# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Dashboard: status at a glance, start/stop, modes, calibration."""

from __future__ import annotations

import time

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (QComboBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
                               QVBoxLayout, QWidget)

from ...core.safety_manager import EngineState
from ...services.tracking_service import CameraStatus, Telemetry
from .. import theme
from ..widgets.common import Card, StatusChip, ToggleRow, VideoView, label

STATE_TEXT = {
    EngineState.STOPPED: ("Stopped", "Press Start to turn on the camera and gesture control."),
    EngineState.ACTIVE: ("Active", "Gestures are being recognised."),
    EngineState.PAUSED: ("Paused", "Hold an open palm, or press Resume, to continue."),
    EngineState.EMERGENCY: ("Emergency stop", "All control is halted. Clear the stop to continue."),
}


class DashboardPage(QWidget):
    calibrate_requested = Signal()
    eye_calibrate_requested = Signal()

    def __init__(self, app, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.app = app
        self._last_gesture_t = 0.0
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(16)

        # ---- control card
        hero = Card()
        top = QHBoxLayout()
        left = QVBoxLayout()
        left.setSpacing(2)
        self.state_label = label("Stopped", "bigValue")
        self.state_hint = label("", "muted", wrap=True)
        left.addWidget(self.state_label)
        left.addWidget(self.state_hint)
        top.addLayout(left, 1)
        self.start_btn = QPushButton("Start")
        self.start_btn.setObjectName("primary")
        self.start_btn.setMinimumWidth(120)
        self.start_btn.clicked.connect(self._start_stop)
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(app.toggle_pause)
        self.clear_btn = QPushButton("Clear emergency stop")
        self.clear_btn.clicked.connect(app.clear_emergency)
        self.calib_btn = QPushButton("Calibrate…")
        self.calib_btn.clicked.connect(self.calibrate_requested)
        for b in (self.clear_btn, self.calib_btn, self.pause_btn, self.start_btn):
            top.addWidget(b, 0, Qt.AlignmentFlag.AlignVCenter)
        hero.body.addLayout(top)
        self.test_row = ToggleRow("Test mode", "Gestures are recognised and shown, but nothing is sent to your computer.",
                                  app.safety.test_mode)
        self.test_row.toggled.connect(app.set_test_mode)
        hero.body.addWidget(self.test_row)
        self.notice = label("", "bannerDanger", wrap=True)
        self.notice.hide()
        hero.body.addWidget(self.notice)
        root.addWidget(hero)

        # ---- status grid
        grid = QGridLayout()
        grid.setSpacing(16)
        self.cam_card, self.cam_chip, self.cam_detail = self._status_card("Camera")
        self.hand_card, self.hand_chip, self.hand_detail = self._status_card("Hand tracking")
        self.head_card, self.head_chip, self.head_detail = self._status_card("Head & eyes")
        gcard = Card("Current gesture")
        self.gesture_label = label("—", "bigValue")
        self.gesture_detail = label("", "hint", wrap=True)
        gcard.body.addWidget(self.gesture_label)
        gcard.body.addWidget(self.gesture_detail)
        gcard.body.addStretch(1)
        for i, c in enumerate((self.cam_card, self.hand_card, self.head_card, gcard)):
            grid.addWidget(c, 0, i)
        root.addLayout(grid)

        # ---- modes + preview
        bottom = QHBoxLayout()
        bottom.setSpacing(16)
        modes = Card("Operating modes")
        m = app.settings.modes
        self.mode_rows = {
            "mouse": ToggleRow("Mouse mode", "Point to move, pinch to click (hold to drag), two fingers scroll, three fingers set the volume, two open hands zoom.", m.mouse),
            "navigation": ToggleRow("Navigation mode", "Turn head for back / forward, nod to confirm.", m.navigation),
            "keyboard": ToggleRow("Keyboard mode", "Floating on-screen keyboard; select keys with the hand cursor.", m.keyboard),
            "face_mouse": ToggleRow(
                "Hands-free mouse (eyes & head)",
                "Point with your eyes and head. Wink left = click, wink right = right click, "
                "long blink = double click. All eye actions: Settings › Gesture mapping.",
                m.face_mouse),
        }
        for key, row in self.mode_rows.items():
            row.toggled.connect(lambda on, k=key: app.set_mode(k, on))
            modes.body.addWidget(row)
            if key == "mouse":
                self.two_hand_row = ToggleRow(
                    "Two-hand mouse", "Your control hand moves the cursor; the other hand pinches to click "
                    "and drag. Steadier clicks.", app.settings.hand.two_hand_mouse)
                self.two_hand_row.toggled.connect(self._set_two_hand)
                modes.body.addWidget(self.two_hand_row)
            if key == "face_mouse":
                opts = QHBoxLayout()
                opts.setContentsMargins(0, 0, 0, 0)
                self.pointer_combo = QComboBox()
                for text, value in (("Eyes + head (recommended)", "hybrid"), ("Eyes only", "gaze"),
                                    ("Head only", "head")):
                    self.pointer_combo.addItem(text, value)
                self.pointer_combo.setAccessibleName("Hands-free pointer")
                self.pointer_combo.setCurrentIndex(max(0, self.pointer_combo.findData(app.settings.face.pointer)))
                self.pointer_combo.currentIndexChanged.connect(self._set_pointer)
                self.eye_calib_btn = QPushButton("Calibrate eyes…")
                self.eye_calib_btn.clicked.connect(self.eye_calibrate_requested)
                opts.addWidget(label("Pointer", "hint"))
                opts.addWidget(self.pointer_combo, 1)
                opts.addWidget(self.eye_calib_btn)
                modes.body.addLayout(opts)
                self.eye_status = label("", "hint", wrap=True)
                modes.body.addWidget(self.eye_status)
                self.dwell_row = ToggleRow("Dwell click", "Keep the pointer still for a moment to click "
                                           "(for anyone who cannot wink).", app.settings.face.dwell_click)
                self.dwell_row.toggled.connect(self._set_dwell)
                modes.body.addWidget(self.dwell_row)
        modes.body.addStretch(1)
        self._update_eye_status()
        # The modes list is longer than small windows: scroll instead of squeezing rows.
        modes_scroll = QScrollArea()
        modes_scroll.setWidgetResizable(True)
        modes_scroll.setFrameShape(QFrame.Shape.NoFrame)
        modes_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        modes_scroll.setWidget(modes)
        bottom.addWidget(modes_scroll, 1)
        prev = Card("Live preview")
        self.preview = VideoView()
        self.preview.setMinimumSize(320, 200)
        prev.body.addWidget(self.preview, 1)
        self.privacy = label("Video is processed on this computer only. Nothing is recorded or uploaded.", "hint", wrap=True)
        prev.body.addWidget(self.privacy)
        bottom.addWidget(prev, 1)
        root.addLayout(bottom, 1)

        app.state_changed.connect(self.refresh)
        app.settings_changed.connect(self._on_settings)
        app.tracking.camera_status.connect(self._on_camera)
        app.tracking.telemetry.connect(self._on_telemetry)
        app.tracking.gesture.connect(self._on_gesture)
        app.tracking.command.connect(self._on_command)
        app.tracking.frame_ready.connect(self._on_frame)
        app.notice.connect(self.show_notice)
        self._fade = QTimer(self)
        self._fade.timeout.connect(self._fade_gesture)
        self._fade.start(500)
        if app.backend_error:
            self.show_notice(app.backend_error)
        if app.config.load_error:
            self.show_notice(app.config.load_error)
        self.refresh()

    def _status_card(self, title: str):
        c = Card(title)
        chip = StatusChip("Off", "off")
        detail = label("", "hint", wrap=True)
        c.body.addWidget(chip, 0, Qt.AlignmentFlag.AlignLeft)
        c.body.addWidget(detail)
        c.body.addStretch(1)
        return c, chip, detail

    # ------------------------------------------------------------- handlers
    def show_notice(self, text: str) -> None:
        self.notice.setText(text)
        self.notice.setVisible(bool(text))

    def _start_stop(self) -> None:
        if self.app.tracking.running:
            self.app.stop()
        else:
            self.app.start()

    def refresh(self) -> None:
        st = self.app.safety.state
        title, hint = STATE_TEXT[st]
        if st == EngineState.ACTIVE and self.app.safety.test_mode:
            title, hint = "Active — test mode", "Gestures are shown but not executed. Turn off test mode for real control."
        if st == EngineState.EMERGENCY and self.app.safety.last_reason:
            hint = f"Halted by {self.app.safety.last_reason}. Clear the stop to continue."
        color = theme.STATE_COLORS.get(st.value, theme.TEXT)
        self.state_label.setText(title)
        self.state_label.setStyleSheet(f"color: {color};")
        self.state_hint.setText(hint)
        running = self.app.tracking.running
        self.start_btn.setText("Stop" if running else "Start")
        self.start_btn.setEnabled(st != EngineState.EMERGENCY)
        self.pause_btn.setVisible(st in (EngineState.ACTIVE, EngineState.PAUSED))
        self.pause_btn.setText("Resume" if st == EngineState.PAUSED else "Pause")
        self.clear_btn.setVisible(st == EngineState.EMERGENCY)
        self.test_row.setChecked(self.app.safety.test_mode)
        if not running:
            self.preview.clear("Camera is off")
            for chip, det in ((self.hand_chip, self.hand_detail), (self.head_chip, self.head_detail)):
                chip.set("Off", "off")
                det.setText("")

    def _on_settings(self, s) -> None:
        for key, row in self.mode_rows.items():
            row.setChecked(getattr(s.modes, key))
        self.two_hand_row.setChecked(s.hand.two_hand_mouse)
        self.dwell_row.setChecked(s.face.dwell_click)
        idx = self.pointer_combo.findData(s.face.pointer)
        if idx != self.pointer_combo.currentIndex():
            self.pointer_combo.blockSignals(True)
            self.pointer_combo.setCurrentIndex(max(0, idx))
            self.pointer_combo.blockSignals(False)
        self._update_eye_status()

    def _update_eye_status(self) -> None:
        f = self.app.settings.face
        if f.pointer == "head":
            text = "Head pointer: no calibration needed. Use Calibrate… (head) to set your neutral position."
        elif f.gaze_model:
            px = f.gaze_error * 1080
            text = f"Eyes calibrated (about {px:.0f} px on a 1080p screen). Recalibrate if you move the webcam."
        else:
            text = "Eyes not calibrated yet: the head moves the pointer until you calibrate."
        self.eye_status.setText(text)

    def _set_pointer(self, _i: int) -> None:
        s = self.app.settings.copy_deep()
        s.face.pointer = self.pointer_combo.currentData()
        self.app.update_settings(s)

    def _set_dwell(self, on: bool) -> None:
        s = self.app.settings.copy_deep()
        s.face.dwell_click = on
        self.app.update_settings(s)

    def _set_two_hand(self, on: bool) -> None:
        s = self.app.settings.copy_deep()
        s.hand.two_hand_mouse = on
        self.app.update_settings(s)

    def _on_camera(self, status: str, message: str) -> None:
        text = {CameraStatus.ON: "On", CameraStatus.OFF: "Off", CameraStatus.STARTING: "Starting",
                CameraStatus.LOST: "Disconnected", CameraStatus.ERROR: "Error"}[status]
        self.cam_chip.set(text, status)
        self.cam_detail.setText(message)

    def _on_frame(self, img) -> None:
        if self.isVisible():
            self.preview.set_image(img)

    def _on_telemetry(self, t: Telemetry) -> None:
        self.cam_detail.setText(f"{t.source} · {t.fps:.0f} FPS · {t.latency_ms:.0f} ms")
        h = t.hand
        if h.two_hand and (h.visible or h.click_visible):
            moves = f"{h.handedness} moves" if h.visible else "move hand not visible"
            clicks = f"{h.click_handedness} clicks" if h.click_visible else "click hand not visible"
            self.hand_chip.set(f"{moves} · {clicks}", "on" if h.visible and h.click_visible else "lost")
            self.hand_detail.setText(f"Pose: {h.pose.value.replace('_', ' ')} · Mode: {h.mode}")
        elif h.visible:
            self.hand_chip.set(f"{h.handedness} hand · {h.score:.0%}", "on")
            self.hand_detail.setText(f"Pose: {h.pose.value.replace('_', ' ')} · Mode: {h.mode}")
        else:
            want = self.app.settings.tracking.dominant_hand
            if t.hands_visible:
                self.hand_chip.set("Waiting for control hand", "lost")
                self.hand_detail.setText(f"{t.hands_visible} hand(s) visible, but the control hand is set to "
                                         f"'{want}' (Settings › Tracking).")
            else:
                self.hand_chip.set("No hand in view", "lost" if self.app.settings.modes.mouse else "off")
                self.hand_detail.setText("")
        fs = t.face
        if fs.visible and self.app.settings.modes.face_mouse:
            eyes = ("closed" if fs.left_closed else "open", "closed" if fs.right_closed else "open")
            extra = " · scroll mode" if fs.scroll_mode else ""
            self.head_chip.set(f"Eyes {eyes[0]} / {eyes[1]}{extra}", "on")
            self.head_detail.setText(fs.activity or f"Pointer: {fs.pointer}")
            return
        hd = t.head
        if hd.visible:
            state = "Armed" if hd.armed else "Return to neutral"
            self.head_chip.set(f"Face · {state}", "on" if hd.armed else "starting")
            self.head_detail.setText(f"Yaw {hd.yaw:+.0f}° · Pitch {hd.pitch:+.0f}° · Roll {hd.roll:+.0f}°")
        else:
            self.head_chip.set("No face in view", "lost" if self.app.settings.modes.navigation else "off")
            self.head_detail.setText("")

    def _on_gesture(self, ev) -> None:
        self.gesture_label.setText(ev.label or ev.name)
        self.gesture_label.setStyleSheet(f"color: {theme.ACCENT};")
        self._last_gesture_t = time.monotonic()

    def _on_command(self, rec) -> None:
        if rec.executed:
            self.gesture_detail.setText(f"→ {rec.label}")
        elif rec.simulated:
            self.gesture_detail.setText(f"→ {rec.label} (test mode, not executed)")
        else:
            self.gesture_detail.setText(f"→ {rec.label}: {rec.reason}")

    def _fade_gesture(self) -> None:
        if self._last_gesture_t and time.monotonic() - self._last_gesture_t > 2.5:
            self.gesture_label.setStyleSheet(f"color: {theme.TEXT};")
