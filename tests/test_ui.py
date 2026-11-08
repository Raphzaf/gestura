# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Headless GUI tests (Qt offscreen platform)."""

import json

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDoubleSpinBox, QPushButton

from gestura.controllers.backends import RecordingBackend
from gestura.core.safety_manager import EngineState


@pytest.fixture(scope="module")
def qt():
    return QApplication.instance() or QApplication([])


@pytest.fixture()
def gapp(qt, tmp_path, monkeypatch):
    monkeypatch.setenv("GESTURA_CONFIG_DIR", str(tmp_path))
    from gestura.app.application import GesturaApp
    from gestura.services.configuration_service import ConfigurationService

    be = RecordingBackend()
    app = GesturaApp(ConfigurationService(tmp_path / "settings.json"), backend=be)
    yield app, be, tmp_path
    app.shutdown()


@pytest.fixture()
def window(gapp):
    from gestura.app.windows import build_main_window

    app, be, tmp = gapp
    w = build_main_window(app)
    w.show()
    yield w, app, be, tmp
    w.close()


def test_main_window_pages(window):
    w, app, be, _ = window
    for key in ("dashboard", "studio", "keyboard", "settings"):
        w.show_page(key)
        assert w.stack.currentWidget() is w.pages[key]
    assert w.title.text() == "Settings"


def test_emergency_button_and_clear(window, qt):
    w, app, be, _ = window
    app.safety.start()
    QTest.mouseClick(w.estop, Qt.MouseButton.LeftButton)
    qt.processEvents()
    assert app.safety.state == EngineState.EMERGENCY
    assert "EMERGENCY" in w.engine_chip.accessibleName()
    assert w.dashboard.clear_btn.isVisible() and not w.dashboard.start_btn.isEnabled()
    QTest.mouseClick(w.dashboard.clear_btn, Qt.MouseButton.LeftButton)
    assert app.safety.state == EngineState.STOPPED


def test_test_mode_toggle_from_dashboard(window, qt):
    w, app, be, _ = window
    assert app.safety.test_mode  # default
    w.dashboard.test_row.switch.click()
    assert not app.safety.test_mode


def test_generated_settings_apply_and_persist(window, qt):
    w, app, be, tmp = window
    page = w.settings_page
    spin = page._widgets[("cursor", "speed")]
    assert isinstance(spin, QDoubleSpinBox)
    spin.setValue(1.7)
    assert app.settings.cursor.speed == pytest.approx(1.7)
    app._save_now()
    saved = json.loads((tmp / "settings.json").read_text())
    assert saved["cursor"]["speed"] == pytest.approx(1.7)


def test_settings_page_rejects_invalid_combination(window, qt):
    w, app, be, _ = window
    page = w.settings_page
    page._widgets[("hand", "pinch_on_ratio")].setValue(0.6)  # above pinch_off (0.38)
    assert app.settings.hand.pinch_on_ratio == pytest.approx(0.25)
    assert not page.error.isHidden()


def test_mapping_change(window, qt):
    w, app, be, _ = window
    combo = w.settings_page._widgets[("mapping", "head.nod_down")]
    combo.setCurrentIndex(combo.findData("key.space"))
    assert app.settings.mappings.head["head.nod_down"] == "key.space"
    assert app.commands.mapping()["head.nod_down"] == "key.space"


def test_keyboard_mode_shows_window_and_keys_type(window, qt):
    w, app, be, _ = window
    app.set_test_mode(False)
    app.set_mode("keyboard", True)
    qt.processEvents()
    kw = w.keyboard_window
    assert kw.isVisible()
    assert kw.windowFlags() & Qt.WindowType.WindowStaysOnTopHint
    assert kw.windowFlags() & Qt.WindowType.WindowDoesNotAcceptFocus
    buttons = {b.text(): b for b in kw.findChildren(QPushButton)}
    # unshifted letter keys show lowercase: the key shows what it will type
    for label in "bonjour":
        QTest.mouseClick(buttons[label], Qt.MouseButton.LeftButton)
    assert "".join(c[1] for c in be.named("write_text")) == "bonjour"
    assert kw.preview.text() == "bonjour"
    kw.hide_keyboard()
    assert not app.settings.modes.keyboard


def test_keyboard_does_not_send_in_test_mode_or_emergency(window, qt):
    w, app, be, _ = window
    app.set_mode("keyboard", True)
    kw = w.keyboard_window
    buttons = {b.text(): b for b in kw.findChildren(QPushButton)}
    QTest.mouseClick(buttons["a"], Qt.MouseButton.LeftButton)  # test mode on by default
    app.set_test_mode(False)
    app.emergency_stop()
    QTest.mouseClick(buttons["a"], Qt.MouseButton.LeftButton)
    assert be.named("write_text") == []


def test_keyboard_layout_switch_and_scale(window, qt):
    w, app, be, _ = window
    app.set_mode("keyboard", True)
    kw = w.keyboard_window
    w0 = kw.sizeHint().width()
    kw.set_scale(1.5)
    assert kw.sizeHint().width() > w0
    kw._toggle_layout()
    assert app.settings.keyboard.layout == "qwerty"
    labels = [b.text() for b in kw.findChildren(QPushButton)]
    assert "q" in labels and labels.index("q") < labels.index("w")


def test_overlay_announces_confirmation(window, qt):
    from gestura.core.types import GestureEvent

    w, app, be, _ = window
    app.set_test_mode(False)
    app.safety.start()
    app.commands.handle(GestureEvent("head.nod_down", 1.0, {}, "Nod down"))
    qt.processEvents()
    assert w.overlay.last_message.startswith("Repeat to confirm")
    assert be.calls == []


def test_calibration_wizard_steps(window, qt, monkeypatch):
    from gestura.core.types import HeadPose
    from gestura.gestures.head_gestures import HeadState
    from gestura.services.tracking_service import Telemetry
    from gestura.ui.calibration.wizard import CalibrationWizard

    w, app, be, _ = window
    monkeypatch.setattr(app, "start", lambda: None)  # no camera in tests
    wiz = CalibrationWizard(app, w)
    assert app.safety.test_mode
    for _ in range(2):
        wiz._next()
    wiz._start_neutral()
    for _ in range(25):
        wiz._on_tel(Telemetry(face_visible=True, head=HeadState(visible=True, raw=HeadPose(4.0, -2.0, 1.0))))
    wiz._capture_until = 0
    wiz._on_tel(Telemetry(face_visible=True, head=HeadState(visible=True, raw=HeadPose(4.0, -2.0, 1.0))))
    assert wiz.draft.head.calibrated and wiz.draft.head.neutral_yaw == pytest.approx(4.0)
    wiz.accept()
    assert app.settings.head.calibrated


def test_emergency_stop_releases_a_held_mouse_button(window, qt):
    w, app, be, _ = window
    app.mouse.drag_start()
    app.emergency_stop()
    qt.processEvents()
    assert be.named("mouse_down") and be.named("mouse_up") and not app.mouse.dragging


def test_drag_gestures_are_not_remappable_in_settings(window):
    w, app, be, _ = window
    keys = [k for k in w.settings_page._widgets if k[0] == "mapping"]
    assert ("mapping", "hand.zoom_in") in keys and ("mapping", "hand.three_swipe_left") in keys
    assert ("mapping", "hand.drag_start") not in keys and ("mapping", "hand.drag_end") not in keys


def test_dashboard_two_hand_mouse_switch(window, qt):
    w, app, be, _ = window
    row = w.dashboard.two_hand_row
    assert not app.settings.hand.two_hand_mouse
    row.switch.click()
    assert app.settings.hand.two_hand_mouse
    app.update_settings(app.settings.model_copy(update={}))
    assert row.switch.isChecked()


def test_preview_draws_movement_and_click_hands():
    import numpy as np
    from synthetic import frame, make_hand

    from gestura.vision.drawing import Overlay, annotate

    tf = frame(1.0, [make_hand("point", x=0.65, handedness="Right"), make_hand("pinch", x=0.3, handedness="Left")])
    img = np.zeros((480, 640, 3), np.uint8)
    out = annotate(img, tf, Overlay(control_hand=0, click_hand=1, pinch_active=True))
    assert out.shape == img.shape and out.any()


# ------------------------------------------------------------- hands-free mouse
def test_dashboard_hands_free_controls(window):
    w, app, _, _ = window
    d = w.dashboard
    d.mode_rows["face_mouse"].toggled.emit(True)
    assert app.settings.modes.face_mouse
    d.pointer_combo.setCurrentIndex(d.pointer_combo.findData("head"))
    assert app.settings.face.pointer == "head"
    assert "no calibration needed" in d.eye_status.text()
    d.dwell_row.toggled.emit(True)
    assert app.settings.face.dwell_click
    tabs = [w.settings_page.tabs.tabText(i) for i in range(w.settings_page.tabs.count())]
    assert "Eyes & face" in tabs
    combo = w.settings_page._widgets[("mapping", "eye.wink_left")]
    combo.setCurrentIndex(combo.findData("mouse.double_click"))
    assert app.settings.mappings.face["eye.wink_left"] == "mouse.double_click"
    assert ("face", "gaze_model") not in w.settings_page._widgets  # calibration data is not a form field


def _face_telemetry(u: float, v: float, closed: bool = False):
    from gestura.gestures.face_gestures import FaceState
    from gestura.services.tracking_service import Telemetry

    fs = FaceState(visible=True, pointer="hybrid", features=((u - 0.5) * 0.3, (v - 0.5) * 0.1, 0.3 - (v - 0.5) * 0.05),
                   yaw=2.0, pitch=-1.0, left_closed=closed)
    return Telemetry(face=fs)


def test_eye_calibration_flow_saves_a_model(gapp, qt):
    from gestura.gestures import gaze
    from gestura.ui.calibration import gaze_calibration as gc

    app, _, _ = gapp
    now = [0.0]
    cal = gc.GazeCalibration(app, clock=lambda: now[0])
    cal.resize(1600, 900)
    cal._restart()
    saved = []
    cal.done.connect(saved.append)
    for _ in range(4000):
        if cal.phase == "result":
            break
        if cal.phase == "collect":
            u, v = cal.points[cal.index]
            cal._on_telemetry(_face_telemetry(u, v))
            cal._on_telemetry(_face_telemetry(u, v, closed=True))  # blink samples are ignored
        now[0] += 0.07
        cal.tick()
    assert cal.phase == "result" and cal.result_ok, cal.result_text
    assert len(app.settings.face.gaze_model) == gaze.MODEL_LEN
    assert app.settings.face.gaze_error < 0.05
    assert "Accuracy: Good" in cal.result_text
    cal.paint_check = cal.grab()  # renders without error
    cal.finish(True)
    assert saved == [True]


def test_eye_calibration_waits_for_a_face(gapp, qt):
    from gestura.ui.calibration import gaze_calibration as gc

    app, _, _ = gapp
    now = [0.0]
    cal = gc.GazeCalibration(app, clock=lambda: now[0])
    cal._restart()
    for _ in range(200):  # 14 s without any face: stays on the first dot
        now[0] += 0.07
        cal.tick()
    assert cal.phase in ("settle", "collect") and cal.index == 0
    cal.finish(False)


def test_dwell_indicator(qt):
    from gestura.ui.widgets.dwell_indicator import DwellIndicator

    d = DwellIndicator()
    d.set_state(0.6, False)
    assert d.isVisible() and d.progress == 0.6
    d.grab()
    d.set_state(0.0, True)
    assert d.isVisible()
    d.set_state(0.0, False)
    assert not d.isVisible()
    d.close()


def test_studio_shows_eye_state(window):
    w, app, _, _ = window
    from gestura.services.tracking_service import Telemetry

    w.show_page("studio")
    t = _face_telemetry(0.5, 0.5)
    t.face.left_open, t.face.right_open, t.face.activity, t.face.progress = 0.2, 1.0, "Left eye closed", 0.5
    w.studio._on_telemetry(t)
    assert "Face detected" in w.studio.eyes_title.text()
    assert "Left eye closed" in w.studio.eyes_state.text()
    w.studio._on_telemetry(Telemetry())
    assert w.studio.eyes_title.text() == "No face in view"
