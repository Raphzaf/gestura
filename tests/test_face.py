# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura. Gestura is free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Hands-free mouse: eye/face features, winks and blinks, pointers, gaze model.

Faces are real MediaPipe meshes (two sample photos, see tests/data). Eye closure,
gaze, mouth, smile and eyebrows are synthesized by moving the relevant landmarks.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from gestura.config.settings import FaceGesture, FaceMouseSettings, HeadGestureSettings, Settings
from gestura.core.types import FaceObservation, GestureEvent, HeadPose, TrackingFrame
from gestura.gestures import face_features as ff
from gestura.gestures import gaze
from gestura.gestures.face_gestures import FaceGestureEngine

DATA = json.loads((Path(__file__).parent / "data" / "face_landmarks.json").read_text())
FPS = 30


# --------------------------------------------------------------------- synthesis
def _image_sides(lm: np.ndarray) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """(image-left eye indices, image-right eye indices)."""
    a = lm[[ff.EYE_A[0], ff.EYE_A[3]], 0].mean()
    b = lm[[ff.EYE_B[0], ff.EYE_B[3]], 0].mean()
    return (ff.EYE_A, ff.EYE_B) if a <= b else (ff.EYE_B, ff.EYE_A)


def _close(lm: np.ndarray, eye: tuple[int, ...], amount: float) -> None:
    c1, u1, u2, c2, l2, l1 = eye
    for i in (u1, u2, l1, l2):
        t = (lm[i, 0] - lm[c1, 0]) / (lm[c2, 0] - lm[c1, 0])
        mid_y = lm[c1, 1] + t * (lm[c2, 1] - lm[c1, 1])
        lm[i, 1] = mid_y + (lm[i, 1] - mid_y) * (1 - amount)


def make_face(name: str = "business-person", close_left: float = 0.0, close_right: float = 0.0,
              iris: tuple[float, float] = (0.0, 0.0), mouth: float = 0.0, smile: float = 1.0,
              brows: float = 1.0, yaw: float = 0.0, pitch: float = 0.0) -> FaceObservation:
    d = DATA[name]
    lm = np.array(d["landmarks"], dtype=np.float32)
    left, right = _image_sides(lm)  # mirrored frame: image-left = the user's left eye
    _close(lm, left, close_left)
    _close(lm, right, close_right)
    for eye, iris_i in ((ff.EYE_A, ff.IRIS_A), (ff.EYE_B, ff.IRIS_B)):
        width = abs(lm[eye[3], 0] - lm[eye[0], 0])
        lm[iris_i, 0] += iris[0] * width
        lm[iris_i, 1] += iris[1] * width * d["width"] / d["height"]
    mouth_w = abs(lm[ff.MOUTH_RIGHT, 0] - lm[ff.MOUTH_LEFT, 0]) * d["width"]
    lm[ff.MOUTH_LOWER, 1] = lm[ff.MOUTH_UPPER, 1] + mouth * mouth_w / d["height"]
    cx = (lm[ff.MOUTH_LEFT, 0] + lm[ff.MOUTH_RIGHT, 0]) / 2
    for i in (ff.MOUTH_LEFT, ff.MOUTH_RIGHT):
        lm[i, 0] = cx + (lm[i, 0] - cx) * smile
    for brow, lid in ((ff.BROW_A, ff.LID_A), (ff.BROW_B, ff.LID_B)):
        lm[brow, 1] = lm[lid, 1] + (lm[brow, 1] - lm[lid, 1]) * brows
    y0, p0, r0 = d["pose"]
    return FaceObservation(landmarks=lm, matrix=None, pose=HeadPose(y0 + yaw, p0 + pitch, r0))


class Runner:
    def __init__(self, engine: FaceGestureEngine, name: str = "business-person") -> None:
        self.e, self.name, self.t, self.i = engine, name, 0.0, 0
        self.events: list[GestureEvent] = []

    def run(self, seconds: float, **face) -> list[GestureEvent]:
        out = []
        d = DATA[self.name]
        for _ in range(max(1, round(seconds * FPS))):
            tf = TrackingFrame(timestamp=self.t, index=self.i, width=d["width"], height=d["height"],
                               face=make_face(self.name, **face))
            out += self.e.update(tf)
            self.t += 1 / FPS
            self.i += 1
        self.events += out
        return out


def names(events, discrete_only: bool = True) -> list[str]:
    return [e.name for e in events if not (discrete_only and e.continuous)]


def engine(**changes) -> FaceGestureEngine:
    s = FaceMouseSettings(**{"pointer": "head", **changes})
    return FaceGestureEngine(s, HeadGestureSettings())


def warm(e: FaceGestureEngine, name: str = "business-person") -> Runner:
    r = Runner(e, name)
    r.run(1.5)  # learn the open-eye and neutral baselines
    return r


# ---------------------------------------------------------------------- features
@pytest.mark.parametrize("name", list(DATA))
def test_features_on_real_faces(name):
    d = DATA[name]
    f = ff.extract(np.array(d["landmarks"]), d["width"], d["height"], mirrored=True)
    assert f is not None
    assert 0.15 < f.left.ear < 0.4 and 0.15 < f.right.ear < 0.4
    assert f.left.center[0] < f.right.center[0]  # mirrored: the user's left eye is on the image left
    assert abs(f.gaze_h) < 0.15 and abs(f.gaze_v) < 0.2  # looking roughly at the camera
    assert 0.3 < f.smile < 1.2 and 0.1 < f.brows < 0.4
    unmirrored = ff.extract(np.array(d["landmarks"]), d["width"], d["height"], mirrored=False)
    assert unmirrored.left.center == f.right.center


def test_business_person_mouth_closed_and_portrait_teeth_not_open():
    for name, limit in (("business-person", 0.05), ("portrait", 0.3)):
        d = DATA[name]
        assert ff.extract(np.array(d["landmarks"]), d["width"], d["height"]).mouth_open < limit


def test_synthetic_changes_move_the_features():
    d = DATA["business-person"]
    base = ff.extract(make_face().landmarks, d["width"], d["height"])
    closed = ff.extract(make_face(close_left=0.9).landmarks, d["width"], d["height"])
    assert closed.left.ear < 0.2 * base.left.ear and abs(closed.right.ear - base.right.ear) < 1e-6
    looking = ff.extract(make_face(iris=(0.1, 0.05)).landmarks, d["width"], d["height"])
    assert looking.gaze_h == pytest.approx(base.gaze_h + 0.1, abs=0.01)
    assert looking.gaze_v > base.gaze_v
    assert ff.extract(make_face(mouth=0.5).landmarks, d["width"], d["height"]).mouth_open == pytest.approx(0.5, abs=0.02)


def test_too_few_landmarks_gives_none():
    assert ff.extract(np.zeros((468, 3)), 640, 480) is None


# ------------------------------------------------------------------ eye actions
def test_natural_blinks_trigger_nothing():
    r = warm(engine())
    for _ in range(4):
        r.run(0.13, close_left=0.95, close_right=0.95)  # ~130 ms blink
        r.run(0.6)
    assert names(r.events) == []


@pytest.mark.parametrize("side", ["left", "right"])
def test_wink_clicks_on_reopen(side):
    r = warm(engine())
    closing = {f"close_{side}": 0.95}
    assert names(r.run(0.3, **closing)) == []  # nothing while closed
    assert names(r.run(0.2)) == [f"eye.wink_{side}"]


def test_wink_survives_a_slight_squint_of_the_other_eye():
    r = warm(engine())
    r.run(0.1, close_left=0.95)
    r.run(0.2, close_left=0.95, close_right=0.4)  # other eye narrows but stays open
    assert names(r.run(0.2)) == ["eye.wink_left"]


def test_long_wink_fires_once_while_held_and_not_again_on_reopen():
    r = warm(engine())
    ev = r.run(1.0, close_right=0.95)
    assert names(ev) == ["eye.long_wink_right"]
    assert names(r.run(0.3)) == []


def test_too_short_wink_is_ignored():
    r = warm(engine())
    r.run(0.07, close_left=0.95)
    assert names(r.run(0.3)) == []


def test_long_blink_fires_on_reopen():
    r = warm(engine())
    assert names(r.run(0.8, close_left=0.95, close_right=0.95)) == []
    assert names(r.run(0.2)) == ["eye.long_blink"]


def test_eyes_closed_hold_fires_while_closed_and_suppresses_long_blink():
    r = warm(engine())
    assert names(r.run(2.3, close_left=0.95, close_right=0.95)) == ["eye.closed_hold"]
    assert names(r.run(0.3)) == []


def test_double_blink_needs_two_deliberate_blinks():
    r = warm(engine())
    r.run(0.25, close_left=0.95, close_right=0.95)
    r.run(0.25)
    r.run(0.25, close_left=0.95, close_right=0.95)
    assert names(r.run(0.2)) == ["eye.double_blink"]


def test_wink_that_turns_into_a_blink_is_cancelled():
    r = warm(engine())
    r.run(0.1, close_left=0.95)
    r.run(0.1, close_left=0.95, close_right=0.95)
    assert names(r.run(0.3)) == []


def test_cooldown_between_actions():
    r = warm(engine(action_cooldown_ms=2000))
    r.run(0.3, close_left=0.95)
    r.run(0.1)
    r.run(0.3, close_left=0.95)
    r.run(0.2)
    assert names(r.events) == ["eye.wink_left"]


# ---------------------------------------------------------------- expressions
@pytest.mark.parametrize("face,gesture", [
    ({"mouth": 0.5}, "face.mouth_open"), ({"smile": 1.3}, "face.smile"), ({"brows": 1.5}, "face.brows_raised"),
])
def test_expressions_fire_once_and_rearm(face, gesture):
    r = warm(engine(action_cooldown_ms=0))
    assert names(r.run(0.6, **face)) == [gesture]
    assert names(r.run(0.6, **face)) == []  # held: no repeat
    r.run(0.5)
    assert names(r.run(0.6, **face)) == [gesture]


def test_brief_expression_is_ignored():
    r = warm(engine())
    r.run(0.15, mouth=0.6)
    assert names(r.run(0.3)) == []


# --------------------------------------------------------------------- pointers
def _last_cursor(events):
    cur = [e for e in events if e.name == FaceGesture.CURSOR.value]
    return (cur[-1].data["x"], cur[-1].data["y"]) if cur else None


def test_head_pointer_maps_angles_to_screen():
    e = engine(head_range_yaw_deg=10, head_range_pitch_deg=8, head_smoothing_min_cutoff=10)
    r = warm(e)
    x, y = _last_cursor(r.run(0.5))
    yaw0, pitch0 = DATA["business-person"]["pose"][:2]
    assert x == pytest.approx(0.5 + 0.5 * yaw0 / 10, abs=0.02)
    assert y == 1.0  # uncalibrated: the photo's 15° downward pitch is off the bottom edge
    e.head = HeadGestureSettings(neutral_yaw=yaw0, neutral_pitch=pitch0)
    x, y = _last_cursor(r.run(0.5))
    assert (x, y) == pytest.approx((0.5, 0.5), abs=0.02)
    x2, y2 = _last_cursor(r.run(1.0, yaw=5, pitch=4))
    assert x2 - x == pytest.approx(0.25, abs=0.03) and y2 - y == pytest.approx(0.25, abs=0.03)


def test_head_pointer_respects_neutral_pose_and_recenter():
    head = HeadGestureSettings(neutral_yaw=DATA["business-person"]["pose"][0],
                               neutral_pitch=DATA["business-person"]["pose"][1])
    e = FaceGestureEngine(FaceMouseSettings(pointer="head", head_smoothing_min_cutoff=10), head)
    r = warm(e)
    assert _last_cursor(r.run(0.5)) == pytest.approx((0.5, 0.5), abs=0.02)
    r.run(1.0, yaw=6)
    e.recenter()
    assert _last_cursor(r.run(0.5, yaw=6)) == pytest.approx((0.5, 0.5), abs=0.02)


def test_pointer_freezes_while_an_eye_closes():
    r = warm(engine(head_smoothing_min_cutoff=10))
    before = _last_cursor(r.run(0.3))
    during = r.run(0.3, close_left=0.95, yaw=8)  # head moves while winking
    assert _last_cursor(during) is None  # no pointer movement during the wink
    assert r.e.state.frozen and r.e.state.cursor == pytest.approx(before, abs=1e-6)
    after = r.run(0.5, yaw=8)
    assert _last_cursor(after)[0] > before[0] + 0.1


def test_gaze_and_hybrid_fall_back_to_head_without_calibration():
    e = engine(pointer="gaze")
    assert e.effective_pointer == "head" and e.uses_head
    e = engine(pointer="hybrid")
    assert e.effective_pointer == "head"


def _model_for(name: str = "business-person") -> gaze.GazeModel:
    """A gaze model in which iris h/v map linearly to the screen, fitted on synthetic samples."""
    d = DATA[name]
    feats, targets = [], []
    for u, v in gaze.CALIBRATION_POINTS:
        for k in range(5):
            f = ff.extract(make_face(name, iris=((u - 0.5) * 0.4, (v - 0.5) * 0.3)).landmarks, d["width"], d["height"])
            feats.append((f.gaze_h, f.gaze_v + 0.001 * k, f.ear))
            targets.append((u, v))
    yaw0, pitch0 = d["pose"][:2]  # the head pose during this synthetic calibration
    n = len(feats)
    return gaze.fit(np.array(feats), np.array(targets), np.full(n, yaw0), np.full(n, pitch0))


def test_gaze_pointer_follows_the_iris():
    m = _model_for()
    e = engine(pointer="gaze", gaze_model=m.to_list(), gaze_smoothing_min_cutoff=5, gaze_fixation_radius=0.0)
    assert e.effective_pointer == "gaze" and not e.uses_head
    r = warm(e)
    x, y = _last_cursor(r.run(0.5, iris=(0.1, 0.0)))  # (u - 0.5) * 0.4 = 0.1 -> u = 0.75
    assert x == pytest.approx(0.75, abs=0.05) and y == pytest.approx(0.5, abs=0.08)


def test_gaze_fixation_radius_ignores_small_jitter():
    m = _model_for()
    e = engine(pointer="gaze", gaze_model=m.to_list(), gaze_smoothing_min_cutoff=5, gaze_fixation_radius=0.05)
    r = warm(e)
    p1 = _last_cursor(r.run(0.4))
    p2 = _last_cursor(r.run(0.4, iris=(0.005, 0.0)))  # ~1 % of the screen
    assert p2 == pytest.approx(p1, abs=1e-9)


def test_hybrid_head_refines_and_gaze_jumps():
    m = _model_for()
    e = engine(pointer="hybrid", gaze_model=m.to_list(), gaze_smoothing_min_cutoff=5,
               head_smoothing_min_cutoff=10, hybrid_head_gain=1.0, head_range_yaw_deg=10)
    r = warm(e)
    start = _last_cursor(r.run(0.3))
    assert start == pytest.approx((0.5, 0.5), abs=0.06)
    fine = _last_cursor(r.run(0.5, yaw=2))  # head refines: 2° -> 0.5 * 2 / 10 = 0.1
    assert fine[0] - start[0] == pytest.approx(0.1, abs=0.03)
    jump = _last_cursor(r.run(0.8, yaw=2, iris=(-0.16, 0.0)))  # look far left -> u ≈ 0.1
    assert jump[0] < 0.25


def test_dwell_click_once_per_rest():
    e = engine(dwell_click=True, dwell_ms=800, head_smoothing_min_cutoff=10)
    r = warm(e)  # 1.5 s at rest: one dwell click
    assert names(r.events).count("face.dwell") == 1
    r.run(1.2)
    assert names(r.events).count("face.dwell") == 1  # resting longer does not click again
    r.run(0.5, yaw=5)  # move away and rest again
    r.run(1.2, yaw=5)
    assert names(r.events).count("face.dwell") == 2


def test_dwell_off_by_default():
    r = warm(engine())
    r.run(2.0)
    assert "face.dwell" not in names(r.events)


def test_scroll_mode_scrolls_instead_of_moving():
    e = engine(head_smoothing_min_cutoff=10, head_range_pitch_deg=10)
    r = warm(e)
    e.toggle_scroll_mode()
    ev = r.run(0.2) + r.run(0.6, pitch=5)  # tilt down: 0.25 screen below the reference
    assert _last_cursor(ev) is None
    scrolls = [x for x in ev if x.name == FaceGesture.SCROLL.value]
    assert scrolls and all(x.data["dy"] < 0 for x in scrolls)  # content scrolls down
    e.toggle_scroll_mode()
    assert _last_cursor(r.run(0.2, pitch=5)) is not None


def test_face_lost_resets_but_keeps_baselines():
    e = engine()
    r = warm(e)
    e.update(TrackingFrame(timestamp=r.t, index=0, width=640, height=480, face=None))
    assert not e.state.visible
    assert e._left.baseline.ready  # learned open-eye size survives a lost face


# ------------------------------------------------------------------- gaze model
def test_gaze_fit_recovers_a_mapping_and_round_trips():
    rng = np.random.default_rng(0)
    feats, targets = [], []
    for u, v in gaze.CALIBRATION_POINTS:
        for _ in range(12):
            h = (u - 0.5) * 0.3 + rng.normal(0, 0.003)
            vv = (v - 0.5) * 0.1 + rng.normal(0, 0.003)
            ear = 0.3 - (v - 0.5) * 0.08 + rng.normal(0, 0.003)
            feats.append((h, vv, ear))
            targets.append((u, v))
    m = gaze.fit(np.array(feats), np.array(targets))
    errs = gaze.point_errors(m, np.array(feats), np.array(targets))
    assert max(errs) < 0.03
    again = gaze.GazeModel.from_list(m.to_list())
    assert again.predict(feats[0]) == pytest.approx(m.predict(feats[0]))


def test_gaze_head_compensation_is_physical():
    m = _model_for()
    base = m.predict((0.0, 0.0, 0.3))
    turned = m.predict((0.0, 0.0, 0.3), yaw=m.yaw0 + 11, pitch=m.pitch0, half_angle_deg=22)
    assert turned[0] - base[0] == pytest.approx(0.25, abs=1e-6)


def test_gaze_fit_rejects_bad_calibrations():
    with pytest.raises(ValueError):
        gaze.fit(np.zeros((3, 3)), np.zeros((3, 2)))
    feats = np.ones((20, 3))
    targets = np.array([gaze.CALIBRATION_POINTS[i % 9] for i in range(20)])
    with pytest.raises(ValueError):
        gaze.fit(feats, targets)  # eyes never moved
    assert gaze.GazeModel.from_list([1.0, 2.0]) is None
    assert gaze.GazeModel.from_list([0.0] * gaze.MODEL_LEN) is None  # zero spread


# ------------------------------------------------------------ settings & wiring
def test_face_mappings_and_validation():
    s = Settings()
    assert s.mappings.face["eye.wink_left"] == "mouse.left_click"
    assert s.mappings.face["face.cursor"] == "mouse.move" and not s.modes.face_mouse
    data = s.model_dump()
    data["mappings"]["face"] = {"eye.wink_left": "mouse.double_click", "bogus": "none"}
    s2 = Settings.model_validate(data)
    assert s2.mappings.face["eye.wink_left"] == "mouse.double_click" and "bogus" not in s2.mappings.face
    data["face"]["eye_open_ratio"] = 0.3
    data["face"]["eye_close_ratio"] = 0.5
    with pytest.raises(ValueError):
        Settings.model_validate(data)


def test_every_default_face_mapping_is_a_known_command():
    from gestura.core.gesture_registry import COMMANDS

    for gesture, command in Settings().mappings.face.items():
        assert command in COMMANDS, gesture
        assert COMMANDS[command].continuous == (gesture in ("face.cursor", "face.scroll"))


def test_worker_dispatch_rules():
    from gestura.core.command_engine import CommandEngine
    from gestura.core.event_bus import EventBus
    from gestura.core.safety_manager import SafetyManager
    from gestura.services.tracking_service import TrackingWorker

    s = Settings()
    s.modes.navigation = True
    s.modes.face_mouse = True
    bus = EventBus()
    w = TrackingWorker(s, CommandEngine(SafetyManager(), bus), bus)
    handled = []
    w.commands.handle = lambda ev: handled.append(ev.name)
    head = [GestureEvent("head.turn_left", 0.0)]
    face = [GestureEvent("face.cursor", 0.0, {"x": 0.5, "y": 0.5}, continuous=True), GestureEvent("eye.wink_left", 0.0)]
    w._dispatch_all(s, [], head, face)
    assert handled == ["face.cursor", "eye.wink_left"]  # head pointer active: no head turn command
    handled.clear()
    s.modes.face_mouse = False
    w._dispatch_all(s, [], head, face)
    assert handled == ["head.turn_left"]
    handled.clear()
    s.modes.face_mouse = True
    w.hand_engine.state.mode = "cursor"  # a hand is moving the mouse
    w._dispatch_all(s, [], [], face)
    assert handled == ["eye.wink_left"] and w.face_engine.state.paused_by_hand


def test_drag_toggle_command():
    from gestura.controllers import register_executors
    from gestura.controllers.backends import RecordingBackend
    from gestura.controllers.keyboard_controller import KeyboardController
    from gestura.controllers.mouse_controller import MouseController
    from gestura.controllers.navigation_controller import NavigationController
    from gestura.core.command_engine import CommandEngine
    from gestura.core.safety_manager import SafetyManager

    safety = SafetyManager(test_mode=False)
    safety.start()
    eng = CommandEngine(safety)
    b = RecordingBackend()
    mouse, kb = MouseController(b, Settings().cursor), KeyboardController(b)
    register_executors(eng, mouse, kb, NavigationController(kb))
    eng.set_mapping({"eye.long_wink_left": "mouse.drag_toggle"})
    eng.handle(GestureEvent("eye.long_wink_left", 0.0))
    assert mouse.dragging
    eng.handle(GestureEvent("eye.long_wink_left", 1.0))
    assert not mouse.dragging
    assert math.isfinite(0.0)
