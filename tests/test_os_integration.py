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


class _Recorder:
    """A real window that records the mouse/wheel events it receives from the OS."""

    def __init__(self, qt):
        from PySide6.QtCore import QEvent, QObject, Qt
        from PySide6.QtWidgets import QWidget

        self.events = []
        rec = self

        class Pad(QWidget):
            def mousePressEvent(self, e):  # noqa: N802
                rec.events.append(("press", e.globalPosition().toPoint().toTuple()))

            def mouseMoveEvent(self, e):  # noqa: N802
                if e.buttons() & Qt.MouseButton.LeftButton:
                    rec.events.append(("drag_move", e.globalPosition().toPoint().toTuple()))

            def mouseReleaseEvent(self, e):  # noqa: N802
                rec.events.append(("release", e.globalPosition().toPoint().toTuple()))

            def wheelEvent(self, e):  # noqa: N802
                rec.events.append(("wheel", e.angleDelta().y(),
                                   bool(e.modifiers() & Qt.KeyboardModifier.ControlModifier)))

        self.w = Pad()
        self.w.setMouseTracking(True)
        self.w.resize(1400, 900)
        self.w.move(20, 20)
        self.w.show()
        self.w.activateWindow()
        pump(qt, 0.5)


def test_pinch_hold_drags_with_the_real_mouse_button(rig, qt):
    be, eng, hands, safety, _ = rig
    rec = _Recorder(qt)
    clock = Clock()
    drive(eng, hands, clock, "point", 30, x=0.45, y=0.75)
    pump(qt)
    start = be.position()
    drive(eng, hands, clock, "pinch", 16, x=0.45, y=0.75)  # hold -> drag starts
    for i in range(20):
        drive(eng, hands, clock, "pinch", x=0.45 + i * 0.006, y=0.75)
        qt.processEvents()
    drive(eng, hands, clock, "point", 4, x=0.57, y=0.75)  # release -> drop
    pump(qt, 0.4)
    kinds = [e[0] for e in rec.events]
    assert "press" in kinds and "release" in kinds, rec.events
    press = next(e for e in rec.events if e[0] == "press")
    release = next(e for e in rec.events if e[0] == "release")
    assert kinds.index("press") < kinds.index("release")
    assert "drag_move" in kinds[kinds.index("press"):kinds.index("release")]
    assert abs(press[1][0] - start[0]) <= 3, "drag must start where the cursor was aimed"
    assert release[1][0] - press[1][0] > 80, "the button must stay held while the hand moves"
    rec.w.close()


def test_zoom_sends_a_real_ctrl_wheel(rig, qt):
    be, eng, hands, safety, kb = rig
    rec = _Recorder(qt)
    be.move_to(600, 400)
    pump(qt)
    from gestura.core.types import GestureEvent

    for _ in range(2):
        eng.handle(GestureEvent("hand.zoom_in", 1.0, {}, "Zoom in"))
    eng.handle(GestureEvent("hand.zoom_out", 1.0, {}, "Zoom out"))
    pump(qt, 0.4)
    wheels = [e for e in rec.events if e[0] == "wheel"]
    assert len(wheels) == 3 and all(e[2] for e in wheels), rec.events
    assert wheels[0][1] > 0 and wheels[2][1] < 0
    assert kb.held == frozenset()
    rec.w.close()


def test_two_hand_mouse_drags_with_the_real_button(rig, qt):
    from gestura.config.settings import Settings
    from gestura.gestures.hand_gestures import HandGestureEngine

    be, eng, _, safety, _ = rig
    s = Settings()
    s.tracking.dominant_hand = "right"
    s.hand.two_hand_mouse = True
    hands = HandGestureEngine(s.hand, s.cursor, s.tracking)
    rec = _Recorder(qt)
    clock = Clock()

    def step(move_x, click_pose, n=1):
        for _ in range(n):
            tf = frame(clock.tick(), [make_hand("point", x=move_x, y=0.75, handedness="Right"),
                                      make_hand(click_pose, x=0.25, y=0.75, handedness="Left")])
            for ev in hands.update(tf):
                eng.handle(ev)
        qt.processEvents()

    step(0.5, "relax", 30)
    start = be.position()
    step(0.5, "pinch", 16)  # left hand holds the pinch -> drag starts
    for i in range(20):
        step(0.5 + i * 0.006, "pinch")  # right hand moves
    step(0.62, "relax", 4)  # left hand opens -> drop
    pump(qt, 0.4)
    kinds = [e[0] for e in rec.events]
    press = next(e for e in rec.events if e[0] == "press")
    release = next(e for e in rec.events if e[0] == "release")
    assert abs(press[1][0] - start[0]) <= 3
    assert "drag_move" in kinds[kinds.index("press"):kinds.index("release")]
    assert release[1][0] - press[1][0] > 80
    rec.w.close()
