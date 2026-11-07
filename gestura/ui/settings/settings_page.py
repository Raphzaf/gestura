# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Settings screen, generated from the pydantic Settings model.

Each section becomes a tab. Widget type, range and label come from the field's
annotation and `Field(...)` metadata, so new settings appear automatically and
can never drift from validation. Edits are validated as a whole, applied live
and saved (debounced) by GesturaApp.
"""

from __future__ import annotations

import threading
import typing

from annotated_types import Ge, Le
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDoubleSpinBox, QFormLayout, QHBoxLayout, QMessageBox,
                               QPushButton, QScrollArea, QSpinBox, QTabWidget, QVBoxLayout, QWidget)

from ...config.settings import HandGesture, HeadGesture, Settings
from ...core.gesture_registry import COMMANDS, continuous_commands, discrete_commands
from ..widgets.common import label

SECTIONS = [
    ("camera", "Camera"), ("tracking", "Tracking"), ("cursor", "Cursor"), ("hand", "Hand gestures"),
    ("head", "Head gestures"), ("safety", "Safety"), ("keyboard", "Keyboard"), ("interface", "Interface"), ("startup", "Startup"),
]
HIDDEN = {
    "head": {"neutral_yaw", "neutral_pitch", "neutral_roll", "calibrated"},
    "keyboard": {"pos_x", "pos_y"},
}
CONTINUOUS_GESTURES = {HandGesture.CURSOR.value, HandGesture.SCROLL.value}
GESTURE_LABELS = {
    "hand.cursor": "Index finger extended", "hand.pinch": "Thumb + index pinch",
    "hand.middle_pinch": "Thumb + middle pinch", "hand.scroll": "Two fingers, move hand",
    "hand.swipe_left": "Open palm swipe left", "hand.swipe_right": "Open palm swipe right",
    "hand.palm_hold": "Open palm held still",
    "hand.volume_up": "Three fingers, move up",
    "hand.volume_down": "Three fingers, move down",
    "hand.zoom_in": "Two open hands, spread apart",
    "hand.zoom_out": "Two open hands, bring together",
    "hand.three_swipe_left": "Three-finger swipe left",
    "hand.three_swipe_right": "Three-finger swipe right",
    "head.turn_left": "Turn head left", "head.turn_right": "Turn head right",
    "head.nod_down": "Nod down", "head.tilt_up": "Tilt head up",
    "head.roll_left": "Tilt head to left shoulder", "head.roll_right": "Tilt head to right shoulder",
}


def _bounds(field) -> tuple[float | None, float | None]:
    lo = hi = None
    for m in field.metadata:
        if isinstance(m, Ge):
            lo = m.ge
        elif isinstance(m, Le):
            hi = m.le
    return lo, hi


class _CameraProbe(QObject):
    done = Signal(list)


class SettingsPage(QWidget):
    def __init__(self, app, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.app = app
        self._widgets: dict[tuple[str, str], QWidget] = {}
        self._loading = False
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(12)
        self.error = label("", "bannerDanger", wrap=True)
        self.error.hide()
        root.addWidget(self.error)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        for key, title in SECTIONS:
            self.tabs.addTab(self._build_section(key), title)
        self.tabs.addTab(self._build_mappings(), "Gesture mapping")

        buttons = QHBoxLayout()
        buttons.addWidget(label(f"Saved automatically to {app.config.path}", "hint"), 1)
        reset = QPushButton("Restore defaults")
        reset.clicked.connect(self._reset)
        buttons.addWidget(reset)
        root.addLayout(buttons)

        self._probe = _CameraProbe()
        self._probe.done.connect(self._on_cameras)
        app.settings_changed.connect(self.load)
        self.load(app.settings)

    # ------------------------------------------------------------- building
    def _build_section(self, section: str) -> QWidget:
        model_cls = type(getattr(Settings(), section))
        page = QWidget()
        form = QFormLayout(page)
        form.setContentsMargins(18, 18, 18, 18)
        form.setVerticalSpacing(10)
        form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
        form.setFormAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        if section == "camera":
            row = QHBoxLayout()
            self.camera_combo = QComboBox()
            self.camera_combo.setMinimumWidth(220)
            self.camera_combo.currentIndexChanged.connect(self._camera_picked)
            detect = QPushButton("Detect cameras")
            detect.clicked.connect(self._detect_cameras)
            row.addWidget(self.camera_combo)
            row.addWidget(detect)
            row.addStretch(1)
            form.addRow("Camera", row)
        for name, field in model_cls.model_fields.items():
            if name in HIDDEN.get(section, set()):
                continue
            ann = field.annotation
            w: QWidget
            if ann is bool:
                w = QCheckBox()
                w.toggled.connect(lambda _v, s=section, n=name: self._changed(s, n))
            elif typing.get_origin(ann) is typing.Literal:
                w = QComboBox()
                for opt in typing.get_args(ann):
                    w.addItem(str(opt), opt)
                w.currentIndexChanged.connect(lambda _i, s=section, n=name: self._changed(s, n))
            elif ann is int:
                w = QSpinBox()
                lo, hi = _bounds(field)
                w.setRange(int(lo if lo is not None else -10**6), int(hi if hi is not None else 10**6))
                w.valueChanged.connect(lambda _v, s=section, n=name: self._changed(s, n))
            elif ann is float:
                w = QDoubleSpinBox()
                lo, hi = _bounds(field)
                lo = -1e6 if lo is None else lo
                hi = 1e6 if hi is None else hi
                w.setRange(lo, hi)
                span = hi - lo
                w.setDecimals(3 if span <= 2 else 2 if span <= 50 else 1)
                w.setSingleStep(0.01 if span <= 2 else 0.1 if span <= 50 else 1.0)
                w.valueChanged.connect(lambda _v, s=section, n=name: self._changed(s, n))
            else:
                continue
            w.setAccessibleName(field.title or name)
            if not isinstance(w, QCheckBox):
                w.setMinimumWidth(200)
            self._widgets[(section, name)] = w
            if section == "camera" and name == "index":
                continue  # driven by the camera combo
            form.addRow(field.title or name, w)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        return scroll

    def _build_mappings(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(18, 18, 18, 18)
        lay.addWidget(label("Choose what each gesture does. Only built-in, safe commands can be assigned; "
                            "commands marked * ask you to repeat the gesture to confirm.", "hint", wrap=True))
        # Drag start/end work as a pair (press / release) and are not remappable.
        fixed = {HandGesture.DRAG_START.value, HandGesture.DRAG_END.value}
        hand = [g.value for g in HandGesture if g.value not in fixed]
        for title, gestures in (("Hand", hand), ("Head", [g.value for g in HeadGesture])):
            form = QFormLayout()
            form.setVerticalSpacing(8)
            form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.FieldsStayAtSizeHint)
            lay.addWidget(label(title.upper(), "cardTitle"))
            for g in gestures:
                combo = QComboBox()
                combo.setMinimumWidth(280)
                specs = continuous_commands() if g in CONTINUOUS_GESTURES else discrete_commands()
                for spec in specs:
                    combo.addItem(spec.label + (" *" if spec.sensitive else ""), spec.id)
                combo.currentIndexChanged.connect(lambda _i, gg=g: self._mapping_changed(gg))
                self._widgets[("mapping", g)] = combo
                form.addRow(GESTURE_LABELS.get(g, g), combo)
            lay.addLayout(form)
        lay.addStretch(1)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        return scroll

    # -------------------------------------------------------------- syncing
    def load(self, s: Settings) -> None:
        self._loading = True
        try:
            for (section, name), w in self._widgets.items():
                if section == "mapping":
                    group = s.mappings.hand if name.startswith("hand.") else s.mappings.head
                    idx = w.findData(group.get(name, "none"))
                    w.setCurrentIndex(max(0, idx))
                    continue
                val = getattr(getattr(s, section), name)
                if isinstance(w, QCheckBox):
                    w.setChecked(bool(val))
                elif isinstance(w, QComboBox):
                    w.setCurrentIndex(max(0, w.findData(val)))
                else:
                    w.setValue(val)
            if self.camera_combo.count() == 0 or self.camera_combo.findData(s.camera.index) < 0:
                self.camera_combo.addItem(f"Camera {s.camera.index}", s.camera.index)
            self.camera_combo.setCurrentIndex(self.camera_combo.findData(s.camera.index))
        finally:
            self._loading = False

    def _value(self, w: QWidget):
        if isinstance(w, QCheckBox):
            return w.isChecked()
        if isinstance(w, QComboBox):
            return w.currentData()
        return w.value()

    def _commit(self, mutate) -> None:
        data = self.app.settings.model_dump()
        mutate(data)
        try:
            new = Settings.model_validate(data)
        except ValueError as exc:
            msg = "; ".join(e.get("msg", str(e)) for e in getattr(exc, "errors", lambda: [])()) or str(exc)
            self.error.setText(f"Not applied: {msg}")
            self.error.show()
            return
        self.error.hide()
        self.app.update_settings(new)

    def _changed(self, section: str, name: str) -> None:
        if self._loading:
            return
        value = self._value(self._widgets[(section, name)])
        self._commit(lambda d: d[section].__setitem__(name, value))

    def _mapping_changed(self, gesture: str) -> None:
        if self._loading:
            return
        cmd = self._widgets[("mapping", gesture)].currentData()
        group = "hand" if gesture.startswith("hand.") else "head"
        if cmd not in COMMANDS:
            return
        self._commit(lambda d: d["mappings"][group].__setitem__(gesture, cmd))

    def _reset(self) -> None:
        if QMessageBox.question(self, "Restore defaults",
                                "Reset all settings (including calibration) to their defaults?") \
                == QMessageBox.StandardButton.Yes:
            fresh = Settings()
            fresh.modes = self.app.settings.modes.model_copy()
            self.app.update_settings(fresh)

    # -------------------------------------------------------------- cameras
    def _detect_cameras(self) -> None:
        if self.app.tracking.running:
            self.error.setText("Stop the camera before detecting cameras.")
            self.error.show()
            return
        self.camera_combo.setEnabled(False)
        backend = self.app.settings.camera.backend

        def probe() -> None:
            from ...vision.camera_manager import enumerate_cameras

            cams = enumerate_cameras(backend=backend)
            self._probe.done.emit([(c.index, c.label) for c in cams])

        threading.Thread(target=probe, daemon=True, name="gestura-camprobe").start()

    def _on_cameras(self, cams: list) -> None:
        self._loading = True
        self.camera_combo.clear()
        for index, text in cams or [(self.app.settings.camera.index, "No camera found")]:
            self.camera_combo.addItem(text, index)
        self._loading = False
        self.camera_combo.setEnabled(True)
        self.camera_combo.setCurrentIndex(max(0, self.camera_combo.findData(self.app.settings.camera.index)))

    def _camera_picked(self, _i: int) -> None:
        if self._loading or self.camera_combo.currentData() is None:
            return
        idx = int(self.camera_combo.currentData())
        self._commit(lambda d: d["camera"].__setitem__("index", idx))
