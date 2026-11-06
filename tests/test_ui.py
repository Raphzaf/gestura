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
