import ctypes
import json
from pathlib import Path

import pytest

from gestura.config.settings import Settings, default_settings_json
from gestura.controllers import register_executors
from gestura.controllers.backends import RecordingBackend
from gestura.controllers.keyboard_controller import KeyboardController
from gestura.controllers.mouse_controller import MouseController
from gestura.controllers.navigation_controller import NavigationController
from gestura.controllers import win32_input
from gestura.core.command_engine import CommandEngine
from gestura.core.event_bus import EventBus
from gestura.core.gesture_registry import COMMANDS
from gestura.core.safety_manager import EngineState, FailSafeTriggered, SafetyManager
from gestura.core.types import GestureEvent


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t


def rig(test_mode=False):
    clock = FakeClock()
    safety = SafetyManager(test_mode=test_mode, confirm_window_s=2.0, clock=clock)
    bus = EventBus()
    eng = CommandEngine(safety, bus)
    s = Settings()
    eng.set_mapping({**s.mappings.hand, **s.mappings.head})
    be = RecordingBackend()
    kb = KeyboardController(be)
    register_executors(eng, MouseController(be, s.cursor), kb, NavigationController(kb),
                       {"app.toggle_pause": lambda: safety.toggle_pause("palm"),
                        "app.emergency_stop": lambda: safety.emergency_stop()})
    return eng, safety, be, clock


def ev(name, continuous=False, **data):
    return GestureEvent(name, 1.0, data, name, continuous)


# --------------------------------------------------------------------------- settings
def test_default_settings_file_matches_model():
    path = Path(__file__).parent.parent / "gestura" / "config" / "default_settings.json"
    assert json.loads(path.read_text()) == json.loads(default_settings_json()), \
        "regenerate with: python -m gestura.config.settings"


def test_settings_validation():
    with pytest.raises(ValueError):
        Settings.model_validate({"hand": {"pinch_on_ratio": 0.5, "pinch_off_ratio": 0.4}})
    with pytest.raises(ValueError):
        Settings.model_validate({"camera": {"fps": 1000}})
    s = Settings.model_validate({"mappings": {"hand": {"hand.pinch": "mouse.right_click", "bogus": "x"}}})
    assert s.mappings.hand["hand.pinch"] == "mouse.right_click"
    assert "bogus" not in s.mappings.hand and "hand.cursor" in s.mappings.hand
    assert Settings.model_validate({"unknown_section": 1, "camera": {"zzz": 2}}).camera.index == 0


def test_every_default_mapping_targets_a_registered_command():
    s = Settings()
    for cmd in {**s.mappings.hand, **s.mappings.head}.values():
        assert cmd in COMMANDS


# --------------------------------------------------------------------------- safety / engine
def test_stopped_engine_executes_nothing():
    eng, safety, be, _ = rig()
    rec = eng.handle(ev("hand.pinch"))
    assert not rec.executed and be.calls == [] and rec.reason == "engine stopped"


def test_active_engine_executes_mapped_commands():
    eng, safety, be, _ = rig()
    safety.start()
    eng.handle(ev("hand.pinch"))
    eng.handle(ev("hand.middle_pinch"))
    eng.handle(ev("head.turn_left"))
    eng.handle(ev("hand.swipe_right"))
    eng.handle(ev("hand.cursor", True, x=0.5, y=0.5))
    eng.handle(ev("hand.scroll", True, dx=0.0, dy=2.0))
    assert ("click", "left", 1) in be.calls and ("click", "right", 1) in be.calls
    assert ("hotkey", "alt", "left") in be.calls and ("hotkey", "ctrl", "tab") in be.calls
    assert be.named("move_to") and ("scroll", 2) in be.calls


def test_test_mode_simulates_without_touching_the_os():
    eng, safety, be, _ = rig(test_mode=True)
    safety.start()
    rec = eng.handle(ev("hand.pinch"))
    assert rec.simulated and not rec.executed and be.calls == []
    assert eng.history[-1].command == "mouse.left_click"


def test_pause_blocks_actions_but_palm_resumes():
    eng, safety, be, _ = rig()
    safety.start()
    eng.handle(ev("hand.palm_hold"))
    assert safety.state == EngineState.PAUSED
    assert not eng.handle(ev("hand.pinch")).executed
    eng.handle(ev("hand.palm_hold"))
    assert safety.state == EngineState.ACTIVE
    assert eng.handle(ev("hand.pinch")).executed


def test_emergency_stop_blocks_everything_and_needs_explicit_clear():
    eng, safety, be, _ = rig()
    safety.start()
    safety.emergency_stop()
    assert not eng.handle(ev("hand.pinch")).executed
    eng.handle(ev("hand.palm_hold"))  # gestures cannot clear it
    assert safety.state == EngineState.EMERGENCY
    safety.start()
    assert safety.state == EngineState.EMERGENCY
    safety.clear_emergency()
    safety.start()
    assert eng.handle(ev("hand.pinch")).executed


def test_sensitive_command_needs_confirmation_within_window():
    eng, safety, be, clock = rig()
    safety.start()
    r1 = eng.handle(ev("head.nod_down"))  # mapped to Enter (sensitive)
    assert not r1.executed and safety.pending_confirmation == "key.enter"
    clock.t = 1.0
    assert eng.handle(ev("head.nod_down")).executed
    assert ("press", "enter") in be.calls
    # expired confirmation starts over
    be.calls.clear()
    eng.handle(ev("head.nod_down"))
    clock.t = 5.0
    assert not eng.handle(ev("head.nod_down")).executed
    assert be.calls == []


def test_failsafe_triggers_emergency_stop():
    eng, safety, be, _ = rig()
    safety.start()

    def boom(*_):
        raise FailSafeTriggered("corner")

    be.click = boom
    rec = eng.handle(ev("hand.pinch"))
    assert not rec.executed and safety.state == EngineState.EMERGENCY


def test_mapping_rejects_unknown_and_mismatched_commands():
    eng, safety, be, _ = rig()
    safety.start()
    eng.set_mapping({"hand.pinch": "rm -rf /", "hand.swipe_left": "mouse.move"})
    assert eng.handle(ev("hand.pinch")) is None
    assert eng.handle(ev("hand.swipe_left")) is None  # discrete gesture -> continuous command
    assert be.calls == []


def test_event_bus_isolates_failing_handlers():
    bus = EventBus()
    seen = []
    bus.subscribe("t", lambda p: 1 / 0)
    unsub = bus.subscribe("t", seen.append)
    bus.publish("t", 1)
    unsub()
    bus.publish("t", 2)
    assert seen == [1]


# --------------------------------------------------------------------------- controllers
def test_mouse_mapping_never_reaches_failsafe_corners():
    be = RecordingBackend((1920, 1080))
    m = MouseController(be, Settings().cursor)
    for u, v in ((0, 0), (1, 1), (0, 1), (1, 0)):
        m.reset()
        m.move_normalized(u, v)
    corners = {(0, 0), (1919, 0), (0, 1079), (1919, 1079)}
    assert not corners & {c[1:] for c in be.named("move_to")}


def test_mouse_dead_zone():
    be = RecordingBackend((1000, 1000))
    s = Settings().cursor
    s.dead_zone_px = 3
    m = MouseController(be, s)
    assert m.move_normalized(0.5, 0.5)
    assert not m.move_normalized(0.502, 0.5)
    assert m.move_normalized(0.51, 0.5)


def test_integer_scroll_accumulates_fractions():
    be = RecordingBackend()
    m = MouseController(be, Settings().cursor)
    for _ in range(10):
        m.scroll(0.0, 0.35)
    assert sum(c[1] for c in be.named("scroll")) == 3
    be2 = RecordingBackend(fractional_scroll=True)
    MouseController(be2, Settings().cursor).scroll(0.25, 0.35)
    assert be2.calls == [("scroll", 0.35), ("hscroll", 0.25)]


def test_keyboard_release_all():
    be = RecordingBackend()
    kb = KeyboardController(be)
    kb.hold("ctrl")
    kb.hold("shift")
    kb.hold("ctrl")
    kb.release_all()
    assert sorted(c[1] for c in be.named("key_down")) == ["ctrl", "shift"]
    assert sorted(c[1] for c in be.named("key_up")) == ["ctrl", "shift"]
    assert kb.held == frozenset()


@pytest.mark.skipif(ctypes.sizeof(ctypes.c_void_p) != 8, reason="64-bit layout")
def test_win32_input_struct_layout_matches_windows_x64():
    assert ctypes.sizeof(win32_input.MOUSEINPUT) == 32
    assert ctypes.sizeof(win32_input.KEYBDINPUT) == 24
    assert ctypes.sizeof(win32_input.INPUT) == 40


def test_win32_unicode_inputs_handle_accents_and_surrogates():
    events = win32_input.unicode_inputs("é€😀")
    # é and € are one UTF-16 unit each, the emoji is a surrogate pair -> 4 units x (down, up)
    assert len(events) == 8
    assert events[0].ki.wScan == ord("é") and events[1].ki.dwFlags & win32_input.KEYEVENTF_KEYUP
    assert events[4].ki.wScan == 0xD83D and events[6].ki.wScan == 0xDE00
    assert win32_input.wheel_input(-120).mi.mouseData == 0xFFFFFF88
