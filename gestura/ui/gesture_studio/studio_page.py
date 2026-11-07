# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Gesture Studio: live annotated feed and recogniser diagnostics."""

from __future__ import annotations

import time

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QCheckBox, QGridLayout, QHBoxLayout, QListWidget, QListWidgetItem, QPushButton,
                               QScrollArea, QVBoxLayout, QWidget)

from ...services.tracking_service import Telemetry
from .. import theme
from ..widgets.common import Card, Meter, VideoView, label


class StudioPage(QWidget):
    def __init__(self, app, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.app = app
        root = QHBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(16)

        # ---- left: video + overlay toggles
        left = QVBoxLayout()
        left.setSpacing(10)
        bar = QHBoxLayout()
        self.test_banner = label("", "banner", wrap=True)
        bar.addWidget(self.test_banner, 1)
        self.test_btn = QPushButton("Enable test mode")
        self.test_btn.clicked.connect(lambda: app.set_test_mode(True))
        bar.addWidget(self.test_btn)
        self.start_btn = QPushButton("Start camera")
        self.start_btn.setObjectName("primary")
        self.start_btn.clicked.connect(lambda: app.stop() if app.tracking.running else app.start())
        bar.addWidget(self.start_btn)
        left.addLayout(bar)
        self.video = VideoView()
        left.addWidget(self.video, 1)
        toggles = QHBoxLayout()
        for key, text in (("hands", "Hand landmarks"), ("face", "Face mesh"), ("axes", "Head direction"),
                          ("region", "Active region")):
            cb = QCheckBox(text)
            cb.setChecked(True)
            cb.toggled.connect(lambda on, k=key: app.tracking.set_overlay(k, on))
            toggles.addWidget(cb)
        toggles.addStretch(1)
        left.addLayout(toggles)
        root.addLayout(left, 3)

        # ---- right: diagnostics
        panel = QWidget()
        side = QVBoxLayout(panel)
        side.setContentsMargins(0, 0, 6, 0)
        side.setSpacing(12)

        perf = Card("Performance")
        g = QGridLayout()
        self.fps = label("—", "bigValue")
        self.lat = label("—", "bigValue")
        g.addWidget(label("FPS", "hint"), 0, 0)
        g.addWidget(label("Latency", "hint"), 0, 1)
        g.addWidget(self.fps, 1, 0)
        g.addWidget(self.lat, 1, 1)
        perf.body.addLayout(g)
        self.perf_detail = label("", "hint")
        perf.body.addWidget(self.perf_detail)
        side.addWidget(perf)

        hand = Card("Hand")
        self.hand_title = label("No hand", "value")
        self.hand_pose = label("", "hint")
        hand.body.addWidget(self.hand_title)
        hand.body.addWidget(self.hand_pose)
        hs = app.settings.hand
        self.m_ti = Meter(0, 1.2, marks=(hs.pinch_on_ratio, hs.pinch_off_ratio))
        self.m_tm = Meter(0, 1.2, marks=(hs.pinch_on_ratio, hs.pinch_off_ratio))
        self.m_palm = Meter(0, 1)
        for title, meter in (("Thumb–index (left click)", self.m_ti), ("Thumb–middle (right click)", self.m_tm),
                             ("Open-palm hold (pause)", self.m_palm)):
            hand.body.addWidget(label(title, "hint"))
            hand.body.addWidget(meter)
        self.fingers = label("", "hint")
        hand.body.addWidget(self.fingers)
        side.addWidget(hand)

        head = Card("Head")
        self.head_title = label("No face", "value")
        head.body.addWidget(self.head_title)
        hd = app.settings.head
        self.m_yaw = Meter(-45, 45, centered=True, marks=(-hd.yaw_threshold_deg, hd.yaw_threshold_deg))
        self.m_pitch = Meter(-35, 35, centered=True, marks=(-hd.pitch_up_threshold_deg, hd.pitch_down_threshold_deg))
        self.m_roll = Meter(-45, 45, centered=True, marks=(-hd.roll_threshold_deg, hd.roll_threshold_deg))
        self.head_labels = {}
        for key, title, meter in (("yaw", "Yaw (turn)", self.m_yaw), ("pitch", "Pitch (nod)", self.m_pitch),
                                  ("roll", "Roll (tilt)", self.m_roll)):
            lab = label(title, "hint")
            self.head_labels[key] = (lab, title)
            head.body.addWidget(lab)
            head.body.addWidget(meter)
        self.head_state = label("", "hint", wrap=True)
        head.body.addWidget(self.head_state)
        side.addWidget(head)

        log_card = Card("Gesture log")
        self.log = QListWidget()
        self.log.setMinimumHeight(160)
        log_card.body.addWidget(self.log)
        clear = QPushButton("Clear")
        clear.setObjectName("ghost")
        clear.clicked.connect(self.log.clear)
        log_card.body.addWidget(clear, 0, Qt.AlignmentFlag.AlignRight)
        side.addWidget(log_card)
        side.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(panel)
        scroll.setMinimumWidth(330)
        scroll.setMaximumWidth(400)
        root.addWidget(scroll, 0)

        app.tracking.frame_ready.connect(self._on_frame)
        app.tracking.telemetry.connect(self._on_telemetry)
        app.tracking.command.connect(self._on_command)
        app.tracking.gesture.connect(self._on_gesture)
        app.state_changed.connect(self.refresh)
        app.settings_changed.connect(self._on_settings)
        self.refresh()

    # ------------------------------------------------------------------ slots
    def refresh(self) -> None:
        test = self.app.safety.test_mode
        self.test_banner.setText("Test mode is ON — gestures are recognised and logged, but nothing is executed."
                                 if test else "Test mode is OFF — recognised gestures control your computer.")
        self.test_banner.setObjectName("banner" if test else "bannerDanger")
        self.test_banner.style().unpolish(self.test_banner)
        self.test_banner.style().polish(self.test_banner)
        self.test_btn.setVisible(not test)
        self.start_btn.setText("Stop camera" if self.app.tracking.running else "Start camera")
        if not self.app.tracking.running:
            self.video.clear("Camera is off — press Start camera")

    def _on_settings(self, s) -> None:
        self.m_ti.marks = self.m_tm.marks = (s.hand.pinch_on_ratio, s.hand.pinch_off_ratio)
        self.m_yaw.marks = (-s.head.yaw_threshold_deg, s.head.yaw_threshold_deg)
        self.m_pitch.marks = (-s.head.pitch_up_threshold_deg, s.head.pitch_down_threshold_deg)
        self.m_roll.marks = (-s.head.roll_threshold_deg, s.head.roll_threshold_deg)

    def _on_frame(self, img) -> None:
        if self.isVisible():
            self.video.set_image(img)

    def _on_telemetry(self, t: Telemetry) -> None:
        if not self.isVisible():
            return
        self.fps.setText(f"{t.fps:.0f}")
        self.lat.setText(f"{t.latency_ms:.0f} ms")
        self.perf_detail.setText(f"Hand model {t.hand_ms:.0f} ms · Face model {t.face_ms:.0f} ms · "
                                 f"{t.frame_size[0]}×{t.frame_size[1]}")
        h = t.hand
        if (h.visible or h.click_visible) and h.features is not None:
            f = h.click_features or h.features  # pinch meters follow the hand that clicks
            if h.two_hand:
                moves = f"{h.handedness} hand moves" if h.visible else "move hand not visible"
                clicks = f"{h.click_handedness} hand clicks" if h.click_visible else "click hand not visible"
                self.hand_title.setText(f"{moves} · {clicks}")
            else:
                self.hand_title.setText(f"{h.handedness} hand · confidence {h.score:.0%}")
            frozen = " · cursor frozen" if h.frozen else ""
            self.hand_pose.setText(f"Pose: {h.pose.value.replace('_', ' ')} · Mode: {h.mode}{frozen}")
            on = self.app.settings.hand.pinch_on_ratio
            self.m_ti.set(f.thumb_index, theme.SUCCESS if h.left_pinch == "closed" else
                          (theme.WARN if f.thumb_index < on * 1.6 else theme.ACCENT))
            self.m_tm.set(f.thumb_middle, theme.SUCCESS if h.right_pinch == "closed" else theme.ACCENT)
            self.m_palm.set(h.palm_progress, theme.WARN if h.palm_progress < 1 else theme.SUCCESS)
            names = ("Index", "Middle", "Ring", "Pinky")
            self.fingers.setText("  ".join(f"{n} {'▲' if e else '▼'}" for n, e in zip(names, h.features.extended)))
        else:
            self.hand_title.setText("No hand in view" if t.hands_visible == 0 else
                                    f"{t.hands_visible} hand(s) — not the control hand")
            self.hand_pose.setText("")
            for m in (self.m_ti, self.m_tm, self.m_palm):
                m.set(0)
        hd = t.head
        if hd.visible:
            self.head_title.setText("Face detected · " + ("armed" if hd.armed else "waiting for neutral"))
            for key, meter, val in (("yaw", self.m_yaw, hd.yaw), ("pitch", self.m_pitch, hd.pitch),
                                    ("roll", self.m_roll, hd.roll)):
                lab, title = self.head_labels[key]
                lab.setText(f"{title}: {val:+.1f}°")
                meter.set(val, theme.ACCENT if hd.armed else theme.MUTED)
            cand = f"Candidate: {hd.candidate} ({hd.progress:.0%})" if hd.candidate else "No candidate gesture"
            calib = "" if self.app.settings.head.calibrated else " · not calibrated"
            self.head_state.setText(cand + (" · cooling down" if hd.cooling else "") + calib)
        else:
            self.head_title.setText("No face in view")
            self.head_state.setText("")
            for m in (self.m_yaw, self.m_pitch, self.m_roll):
                m.set(0)

    def _on_gesture(self, ev) -> None:
        if self.app.settings.modes.mouse or self.app.settings.modes.keyboard or ev.name.startswith("head."):
            return  # the command record (below) will describe it
        self._add(f"{ev.label}  (mode off — not mapped)", theme.MUTED)

    def _on_command(self, rec) -> None:
        if rec.executed:
            text, color = f"{rec.label}  ✓ executed", theme.SUCCESS
        elif rec.simulated:
            text, color = f"{rec.label}  · simulated", theme.ACCENT
        else:
            text, color = f"{rec.label}  ✗ {rec.reason}", theme.WARN
        self._add(f"{rec.gesture.split('.', 1)[-1].replace('_', ' ')} → {text}", color)

    def _add(self, text: str, color: str) -> None:
        item = QListWidgetItem(time.strftime("%H:%M:%S  ") + text)
        item.setForeground(QColor(color))
        self.log.insertItem(0, item)
        while self.log.count() > 200:
            self.log.takeItem(self.log.count() - 1)
