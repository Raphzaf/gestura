"""End-to-end OS control through the real PyAutoGUI backend.

Runs only with a display and GESTURA_OS_TESTS=1, because it really moves the
mouse and types. On Linux CI use a virtual display:

    GESTURA_OS_TESTS=1 xvfb-run -a python -m pytest tests/test_os_integration.py

Pipeline under test: synthetic hand frames -> HandGestureEngine ->
CommandEngine/SafetyManager -> controllers -> PyAutoGuiBackend -> OS.
"""

import os
import sys
import time

import pytest
from synthetic import Clock, frame, make_hand

pytestmark = pytest.mark.skipif(
    os.environ.get("GESTURA_OS_TESTS") != "1" or (sys.platform.startswith("linux") and not os.environ.get("DISPLAY")),
    reason="set GESTURA_OS_TESTS=1 with a display to run real OS input tests")


@pytest.fixture(scope="module")
def qt():
    from PySide6.QtWidgets import QApplication

    return QApplication.instance() or QApplication([])


@pytest.fixture()
def rig(qt):
    from gestura.config.settings import Settings
    from gestura.controllers import register_executors
    from gestura.controllers.backends import PyAutoGuiBackend
    from gestura.controllers.keyboard_controller import KeyboardController
    from gestura.controllers.mouse_controller import MouseController
    from gestura.controllers.navigation_controller import NavigationController
    from gestura.core.command_engine import CommandEngine
    from gestura.core.safety_manager import SafetyManager
    from gestura.gestures.hand_gestures import HandGestureEngine

    s = Settings()
    s.tracking.dominant_hand = "any"
    s.cursor.post_click_freeze_ms = 0
    be = PyAutoGuiBackend(failsafe=True)
    safety = SafetyManager(test_mode=False)
    eng = CommandEngine(safety)
    eng.set_mapping(s.mappings.hand)
    kb = KeyboardController(be)
    register_executors(eng, MouseController(be, s.cursor), kb, NavigationController(kb))
    hands = HandGestureEngine(s.hand, s.cursor, s.tracking)
    safety.start()
    return be, eng, hands, safety, kb


def pump(qt, seconds=0.15):
    end = time.monotonic() + seconds
    while time.monotonic() < end:
        qt.processEvents()
        time.sleep(0.01)


def drive(eng, hands, clock, pose, n=1, **kw):
    for _ in range(n):
        for ev in hands.update(frame(clock.tick(), [make_hand(pose, **kw)])):
            eng.handle(ev)


def test_hand_moves_real_cursor(rig, qt):
    be, eng, hands, safety, _ = rig
    clock = Clock()
    drive(eng, hands, clock, "point", 30, x=0.3, y=0.75)
    left = be.position()
    drive(eng, hands, clock, "point", 30, x=0.6, y=0.75)
    right = be.position()
    assert right[0] - left[0] > 200, (left, right)


def test_pinch_clicks_a_real_button_and_test_mode_does_not(rig, qt):
    from PySide6.QtCore import QPoint
    from PySide6.QtWidgets import QPushButton

    be, eng, hands, safety, _ = rig
    btn = QPushButton("target")
    btn.resize(600, 400)
    btn.move(50, 50)
    btn.show()
    pump(qt, 0.5)
    clicks = []
    btn.clicked.connect(lambda: clicks.append(1))
    center = btn.mapToGlobal(QPoint(300, 200))
    sw, sh = be.screen_size()
    # Drive the hand until the cursor sits over the button centre.
    clock = Clock()
    hx = 0.18 + (center.x() / sw) * 0.64  # inverse of the default active-region mapping
    hy_tip = 0.12 + (center.y() / sh) * 0.58
    from synthetic import pose_world
    tip_offset = pose_world("point")[8][1] * 1.6
    drive(eng, hands, clock, "point", 40, x=hx + 0.025 * 1.6, y=hy_tip + tip_offset)
    pump(qt)
    pos = be.position()
    assert btn.rect().contains(btn.mapFromGlobal(QPoint(*pos))), (pos, center)

    drive(eng, hands, clock, "pinch", 4, x=hx + 0.025 * 1.6, y=hy_tip + tip_offset)
    drive(eng, hands, clock, "point", 4, x=hx + 0.025 * 1.6, y=hy_tip + tip_offset)
    pump(qt, 0.4)
    assert clicks == [1]

    safety.set_test_mode(True)
    for _ in range(3):
        drive(eng, hands, clock, "pinch", 4, x=hx + 0.025 * 1.6, y=hy_tip + tip_offset)
        drive(eng, hands, clock, "point", 20, x=hx + 0.025 * 1.6, y=hy_tip + tip_offset)
    pump(qt, 0.4)
    assert clicks == [1], "test mode must not click"
    btn.close()


def test_keyboard_text_and_keys_reach_a_focused_widget(rig, qt):
    from PySide6.QtWidgets import QLineEdit

    be, eng, hands, safety, kb = rig
    edit = QLineEdit()
    edit.resize(400, 40)
    edit.show()
    edit.activateWindow()
    edit.setFocus()
    pump(qt, 0.5)
    from PySide6.QtCore import QPoint

    c = edit.mapToGlobal(QPoint(200, 20))
    be.move_to(c.x(), c.y())
    be.click()
    pump(qt, 0.2)
    kb.type_text("hello")
    kb.press("backspace")
    kb.press("space")
    pump(qt, 0.4)
    assert edit.text() == "hell "
    edit.close()


def test_virtual_keyboard_types_into_another_window_via_real_clicks(rig, qt):
    """Milestone 5 acceptance path: real OS clicks on the floating keyboard type
    into a *different* window that keeps focus."""
    from PySide6.QtCore import QPoint
    from PySide6.QtWidgets import QLineEdit, QPushButton

    from gestura.controllers.virtual_keyboard_controller import VirtualKeyboardController
    from gestura.ui.keyboard.keyboard_window import KeyboardWindow

    be, eng, hands, safety, kb = rig
    target = QLineEdit()
    target.resize(500, 40)
    target.move(40, 40)
    target.show()
    target.activateWindow()
    target.setFocus()
    kw = KeyboardWindow(VirtualKeyboardController(kb), "azerty")
    kw.show_keyboard()
    kw.move(40, 300)
    pump(qt, 0.6)
    keys = {b.text(): b for b in kw.findChildren(QPushButton)}
    for ch in "salut":
        b = keys[ch]
        c = b.mapToGlobal(QPoint(b.width() // 2, b.height() // 2))
        be.move_to(c.x(), c.y())
        be.click()
        pump(qt, 0.15)
    pump(qt, 0.4)
    assert kw.controller.preview == "salut"
    assert target.text() == "salut", "keystrokes must reach the focused window, not the keyboard"
    kw.close()
    target.close()
