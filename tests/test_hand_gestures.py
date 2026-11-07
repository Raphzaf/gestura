# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
import json
from pathlib import Path

import numpy as np
import pytest
from synthetic import Clock, frame, make_hand

from gestura.config.settings import Settings
from gestura.core.types import HandObservation
from gestura.gestures.hand_features import Pose, compute
from gestura.gestures.hand_gestures import HandGestureEngine

DATA = json.loads((Path(__file__).parent / "data" / "real_landmarks.json").read_text())


def real_hand(name: str, i: int = 0) -> HandObservation:
    h = DATA[name]["hands"][i]
    return HandObservation(np.array(h["landmarks"], np.float32), np.array(h["world"], np.float32),
                           h["handedness"], h["score"])


def engine(**hand_overrides) -> HandGestureEngine:
    s = Settings()
    s.tracking.dominant_hand = "any"
    for k, v in hand_overrides.items():
        setattr(s.hand, k, v)
    return HandGestureEngine(s.hand, s.cursor, s.tracking)


def feed(eng, clock, pose, n=1, **kw):
    out = []
    for _ in range(n):
        out += eng.update(frame(clock.tick(), [make_hand(pose, **kw)]))
    return out


def names(events, continuous=False):
    return [e.name for e in events if e.continuous == continuous]


# --------------------------------------------------------------------------- features
@pytest.mark.parametrize("name,expected", [
    ("fist", Pose.FIST), ("victory", Pose.TWO), ("pointing_up", Pose.POINT), ("thumb_up", Pose.FIST),
])
def test_real_photo_poses(name, expected):
    assert compute(real_hand(name)).pose == expected


def test_real_fist_is_not_a_pinch_and_pointing_is_not_a_right_click():
    """Regression for the two false-trigger traps measured on real photos."""
    for name in ("fist", "pointing_up", "thumb_up", "victory"):
        eng, clock = engine(), Clock()
        events = []
        for _ in range(30):
            events += eng.update(frame(clock.tick(), [real_hand(name)]))
        assert "hand.pinch" not in names(events), name
        assert "hand.middle_pinch" not in names(events), name


@pytest.mark.parametrize("pose,expected", [
    ("open", Pose.OPEN), ("fist", Pose.FIST), ("point", Pose.POINT), ("two", Pose.TWO)])
def test_synthetic_poses(pose, expected):
    assert compute(make_hand(pose)).pose == expected


# --------------------------------------------------------------------------- cursor
def test_pointing_moves_cursor_smoothly_and_maps_into_screen():
    eng, clock = engine(), Clock()
    feed(eng, clock, "point", 5, x=0.4)
    xs = []
    for i in range(20):
        ev = feed(eng, clock, "point", x=0.4 + i * 0.01)
        cur = [e for e in ev if e.name == "hand.cursor"]
        assert cur, "cursor event expected while pointing"
        xs.append(cur[0].data["x"])
        assert 0.0 <= cur[0].data["x"] <= 1.0 and 0.0 <= cur[0].data["y"] <= 1.0
    assert all(b >= a for a, b in zip(xs, xs[1:])), "cursor should follow monotonic motion"
    assert eng.state.mode == "cursor"


def test_cursor_jitter_is_suppressed():
    eng, clock = engine(), Clock()
    rng = np.random.default_rng(0)
    feed(eng, clock, "point", 5)
    out = []
    for _ in range(60):
        ev = feed(eng, clock, "point", x=0.5 + rng.normal(0, 0.004), y=0.6 + rng.normal(0, 0.004))
        out += [e.data["x"] for e in ev if e.name == "hand.cursor"]
    raw_std = 0.004 / (0.82 - 0.18)  # jitter expressed in screen units
    assert np.std(out[10:]) < raw_std * 0.5


def test_no_cursor_for_fist_open_or_two_fingers():
    for pose in ("fist", "open", "two"):
        eng, clock = engine(), Clock()
        ev = feed(eng, clock, pose, 15)
        assert "hand.cursor" not in names(ev, continuous=True), pose


# --------------------------------------------------------------------------- clicks
def test_quick_pinch_clicks_once_on_release():
    eng, clock = engine(), Clock()
    feed(eng, clock, "point", 6)
    during = feed(eng, clock, "pinch", 5)  # ~170 ms, shorter than the drag hold
    assert "hand.pinch" not in names(during)
    after = feed(eng, clock, "point", 6)
    assert names(after).count("hand.pinch") == 1


def test_click_fires_on_close_when_drag_is_disabled():
    eng, clock = engine(drag_enabled=False), Clock()
    feed(eng, clock, "point", 6)
    ev = feed(eng, clock, "pinch", 20)
    assert names(ev) == ["hand.pinch"]


def test_single_frame_pinch_is_ignored():
    eng, clock = engine(), Clock()
    feed(eng, clock, "point", 6)
    ev = feed(eng, clock, "pinch", 1) + feed(eng, clock, "point", 6)
    assert "hand.pinch" not in names(ev)


def test_two_quick_pinches_are_a_double_click():
    eng, clock = engine(), Clock()
    feed(eng, clock, "point", 6)
    ev = (feed(eng, clock, "pinch", 3) + feed(eng, clock, "point", 3) + feed(eng, clock, "pinch", 3)
          + feed(eng, clock, "point", 3))
    clicks = [e for e in ev if e.name == "hand.pinch"]
    assert [c.data["count"] for c in clicks] == [1, 2]
    assert clicks[1].label == "Double click"


def test_slow_pinches_are_two_single_clicks():
    eng, clock = engine(), Clock()
    feed(eng, clock, "point", 6)
    ev = (feed(eng, clock, "pinch", 3) + feed(eng, clock, "point", 30) + feed(eng, clock, "pinch", 3)
          + feed(eng, clock, "point", 3))
    assert [e.data["count"] for e in ev if e.name == "hand.pinch"] == [1, 1]


def test_cursor_freezes_during_pinch():
    eng, clock = engine(), Clock()
    feed(eng, clock, "point", 8)
    ev = feed(eng, clock, "pinch", 6, x=0.55)
    assert "hand.cursor" not in names(ev[2:], continuous=True)
    assert eng.state.frozen


def test_middle_pinch_is_right_click():
    eng, clock = engine(), Clock()
    feed(eng, clock, "point", 6)
    ev = feed(eng, clock, "middle_pinch", 5)
    assert names(ev) == ["hand.middle_pinch"]


def test_fist_is_a_clutch():
    eng, clock = engine(), Clock()
    ev = feed(eng, clock, "fist", 30, x=0.3) + feed(eng, clock, "fist", 30, x=0.7)
    assert ev == []
    assert eng.state.mode == "clutch"


def test_losing_the_hand_releases_pinch_state():
    eng, clock = engine(), Clock()
    feed(eng, clock, "point", 6)
    feed(eng, clock, "pinch", 5)
    assert eng.state.left_pinch == "closed"
    for _ in range(15):
        eng.update(frame(clock.tick(), []))
    assert eng.state.left_pinch == "open" and not eng.state.visible
    # the interrupted pinch never clicks; a fresh pinch afterwards does
    feed(eng, clock, "point", 6)
    ev = feed(eng, clock, "pinch", 5) + feed(eng, clock, "point", 4)
    assert names(ev).count("hand.pinch") == 1


def test_dominant_hand_filter():
    s = Settings()
    s.tracking.dominant_hand = "right"
    eng, clock = HandGestureEngine(s.hand, s.cursor, s.tracking), Clock()
    ev = []
    for _ in range(10):
        ev += eng.update(frame(clock.tick(), [make_hand("point", handedness="Left")]))
    assert ev == [] and not eng.state.visible


# --------------------------------------------------------------------------- scroll / swipe / palm
def test_two_finger_vertical_motion_scrolls():
    eng, clock = engine(), Clock()
    feed(eng, clock, "two", 6, y=0.6)
    ev = []
    for i in range(15):  # hand moves up
        ev += feed(eng, clock, "two", y=0.6 - i * 0.01)
    dys = [e.data["dy"] for e in ev if e.name == "hand.scroll"]
    assert dys and all(d > 0 for d in dys)  # hand up -> scroll up
    assert sum(dys) == pytest.approx(0.14 * 25, rel=0.35)


def test_scroll_invert_and_dead_zone():
    eng, clock = engine(scroll_invert=True), Clock()
    feed(eng, clock, "two", 6, y=0.6)
    ev = []
    for i in range(10):
        ev += feed(eng, clock, "two", y=0.6 - i * 0.01)
    assert all(e.data["dy"] < 0 for e in ev if e.name == "hand.scroll")
    eng, clock = engine(), Clock()
    ev = feed(eng, clock, "two", 30, y=0.6)  # still hand
    assert "hand.scroll" not in names(ev, continuous=True)


def test_open_palm_swipe_right_and_cooldown():
    eng, clock = engine(), Clock()
    feed(eng, clock, "open", 6, x=0.3)
    ev = []
    for i in range(9):  # 0.36 frame widths in 300 ms
        ev += feed(eng, clock, "open", x=0.3 + i * 0.045)
    assert names(ev) == ["hand.swipe_right"]
    ev = []
    for i in range(9):  # immediately back: within cooldown
        ev += feed(eng, clock, "open", x=0.66 - i * 0.045)
    assert "hand.swipe_left" not in names(ev)


def test_slow_drift_is_not_a_swipe():
    eng, clock = engine(), Clock()
    ev = []
    for i in range(60):
        ev += feed(eng, clock, "open", x=0.3 + i * 0.006)
    assert not [n for n in names(ev) if "swipe" in n]


def test_palm_hold_fires_once_after_hold_time():
    eng, clock = engine(palm_hold_ms=1000), Clock()
    ev = feed(eng, clock, "open", 25)  # ~0.83 s
    assert "hand.palm_hold" not in names(ev)
    ev = feed(eng, clock, "open", 60)
    assert names(ev).count("hand.palm_hold") == 1
    ev = feed(eng, clock, "point", 5) + feed(eng, clock, "open", 10)
    assert "hand.palm_hold" not in names(ev)  # cooldown


def test_moving_palm_does_not_pause():
    eng, clock = engine(palm_hold_ms=800), Clock()
    ev = []
    for i in range(80):
        ev += feed(eng, clock, "open", x=0.5 + 0.12 * np.sin(i / 3))
    assert "hand.palm_hold" not in names(ev)


# --------------------------------------------------------------------------- volume
def test_three_fingers_pose():
    assert compute(make_hand("three")).pose == Pose.THREE


def test_three_fingers_up_raises_volume_down_lowers_it():
    eng, clock = engine(), Clock()
    feed(eng, clock, "three", 6, y=0.6)
    up = []
    for i in range(12):  # hand moves up 0.12 frame heights
        up += feed(eng, clock, "three", y=0.6 - i * 0.01)
    assert set(names(up)) == {"hand.volume_up"}
    assert 2 <= names(up).count("hand.volume_up") <= 0.12 * 30 + 1
    down = []
    for i in range(12):
        down += feed(eng, clock, "three", y=0.49 + i * 0.01)
    assert set(names(down)) == {"hand.volume_down"}
    assert eng.state.mode == "volume"


def test_still_three_fingers_and_other_poses_do_not_change_volume():
    eng, clock = engine(), Clock()
    ev = feed(eng, clock, "three", 40, y=0.6)  # still hand
    assert not [n for n in names(ev) if "volume" in n]
    eng, clock = engine(), Clock()
    ev = []
    for i in range(15):  # same motion with two fingers scrolls instead
        ev += feed(eng, clock, "two", y=0.6 - i * 0.01)
    assert not [n for n in names(ev) if "volume" in n]


def test_volume_steps_are_capped_per_frame_and_no_backlog():
    eng, clock = engine(volume_max_steps_per_frame=2), Clock()
    feed(eng, clock, "three", 6, y=0.7)
    jump = feed(eng, clock, "three", y=0.4)  # huge jump in one frame
    assert names(jump).count("hand.volume_up") <= 2
    after = feed(eng, clock, "three", 10, y=0.4)  # hand now still: smoothing settles, no backlog burst
    assert names(after).count("hand.volume_up") <= 6


def test_switching_three_to_open_palm_does_not_change_volume():
    eng, clock = engine(), Clock()
    feed(eng, clock, "three", 8, y=0.6)
    ev = feed(eng, clock, "open", 20, y=0.6)
    assert not [n for n in names(ev) if "volume" in n]


# --------------------------------------------------------------------------- drag and drop
def test_pinch_and_hold_drags_and_release_drops():
    eng, clock = engine(), Clock()
    feed(eng, clock, "point", 8, x=0.4)
    hold = feed(eng, clock, "pinch", 16, x=0.4)  # ~530 ms > 450 ms hold
    assert names(hold) == ["hand.drag_start"]
    assert eng.state.dragging and eng.state.mode == "drag"
    moves = []
    for i in range(15):  # move while still pinched: the cursor must follow
        moves += feed(eng, clock, "pinch", x=0.4 + i * 0.01)
    xs = [e.data["x"] for e in moves if e.name == "hand.cursor"]
    assert len(xs) >= 10 and xs[-1] > xs[0] + 0.1
    drop = feed(eng, clock, "point", 4, x=0.54)
    assert names(drop) == ["hand.drag_end"]
    assert "hand.pinch" not in names(hold + moves + drop)
    assert not eng.state.dragging


def test_losing_the_hand_mid_drag_drops():
    eng, clock = engine(), Clock()
    feed(eng, clock, "point", 8)
    feed(eng, clock, "pinch", 16)
    assert eng.state.dragging
    ev = []
    for _ in range(12):
        ev += eng.update(frame(clock.tick(), []))
    assert names(ev) == ["hand.drag_end"]
    assert not eng.state.dragging


# --------------------------------------------------------------------------- two-hand zoom
def two_open(clock, eng, gap, n=1):
    out = []
    for _ in range(n):
        hands = [make_hand("open", x=0.5 - gap / 2, handedness="Left"),
                 make_hand("open", x=0.5 + gap / 2, handedness="Right")]
        out += eng.update(frame(clock.tick(), hands))
    return out


def test_spreading_two_open_hands_zooms_in_and_closing_zooms_out():
    eng, clock = engine(), Clock()
    two_open(clock, eng, 0.30, 6)
    zin = []
    for i in range(12):
        zin += two_open(clock, eng, 0.30 + i * 0.02)
    assert set(names(zin)) == {"hand.zoom_in"} and eng.state.mode == "zoom"
    zout = []
    for i in range(12):
        zout += two_open(clock, eng, 0.52 - i * 0.02)
    assert set(names(zout)) == {"hand.zoom_out"}


def test_still_two_hands_do_not_zoom_pause_or_swipe():
    eng, clock = engine(palm_hold_ms=600), Clock()
    ev = two_open(clock, eng, 0.35, 60)  # two still open palms for 2 s
    assert names(ev) == []


def test_zoom_requires_both_hands_open():
    eng, clock = engine(), Clock()
    ev = []
    for i in range(15):
        hands = [make_hand("open", x=0.3 - i * 0.01, handedness="Left"),
                 make_hand("point", x=0.7 + i * 0.01, handedness="Right")]
        ev += eng.update(frame(clock.tick(), hands))
    assert not [n for n in names(ev) if "zoom" in n]


def test_zoom_disabled_setting():
    eng, clock = engine(zoom_enabled=False), Clock()
    two_open(clock, eng, 0.30, 6)
    ev = []
    for i in range(12):
        ev += two_open(clock, eng, 0.30 + i * 0.02)
    assert not [n for n in names(ev) if "zoom" in n]


# --------------------------------------------------------------------------- three-finger swipes
def test_three_finger_swipe_snaps_window_without_volume_change():
    eng, clock = engine(), Clock()
    feed(eng, clock, "three", 6, x=0.3)
    ev = []
    for i in range(9):
        ev += feed(eng, clock, "three", x=0.3 + i * 0.045)
    assert names(ev) == ["hand.three_swipe_right"]
    eng, clock = engine(), Clock()
    feed(eng, clock, "three", 6, x=0.7)
    ev = []
    for i in range(9):
        ev += feed(eng, clock, "three", x=0.7 - i * 0.045)
    assert names(ev) == ["hand.three_swipe_left"]


# --------------------------------------------------------------------------- two-hand mouse
def two_hand_engine(**kw):
    s = Settings()
    s.tracking.dominant_hand = "right"  # the right hand moves the cursor
    s.hand.two_hand_mouse = True
    for k, v in kw.items():
        setattr(s.hand, k, v)
    return HandGestureEngine(s.hand, s.cursor, s.tracking)


def both(eng, clock, move_pose, click_pose, n=1, mx=0.65, my=0.6, cx=0.3, cy=0.6, move_label="Right",
         click_label="Left"):
    out = []
    for _ in range(n):
        hands = [make_hand(move_pose, x=mx, y=my, handedness=move_label),
                 make_hand(click_pose, x=cx, y=cy, handedness=click_label)]
        out += eng.update(frame(clock.tick(), hands))
    return out


def test_two_hand_mode_other_hand_clicks_while_cursor_hand_points():
    eng, clock = two_hand_engine(), Clock()
    both(eng, clock, "point", "relax", 8)
    ev = both(eng, clock, "point", "pinch", 4) + both(eng, clock, "point", "relax", 4)
    assert names(ev).count("hand.pinch") == 1
    assert eng.state.two_hand and eng.state.click_visible and eng.state.handedness == "Right"


def test_two_hand_mode_cursor_hand_pinch_does_not_click():
    eng, clock = two_hand_engine(), Clock()
    both(eng, clock, "point", "relax", 8)
    ev = both(eng, clock, "pinch", "relax", 5) + both(eng, clock, "point", "relax", 5)
    assert "hand.pinch" not in names(ev)


def test_two_hand_mode_click_hand_pointing_does_not_move_the_cursor():
    eng, clock = two_hand_engine(), Clock()
    ev = []
    for i in range(15):
        ev += both(eng, clock, "relax", "point", cx=0.2 + i * 0.01)
    assert "hand.cursor" not in names(ev, continuous=True)


def test_two_hand_mode_cursor_keeps_moving_between_clicks():
    eng, clock = two_hand_engine(), Clock()
    both(eng, clock, "point", "relax", 8, mx=0.5)
    xs = []
    for i in range(20):
        ev = both(eng, clock, "point", "relax", mx=0.5 + i * 0.01)
        xs += [e.data["x"] for e in ev if e.name == "hand.cursor"]
    assert len(xs) == 20 and xs[-1] > xs[0]  # never frozen: the moving hand never pinches


def test_two_hand_drag_click_hand_holds_and_cursor_hand_moves():
    eng, clock = two_hand_engine(), Clock()
    both(eng, clock, "point", "relax", 8, mx=0.5)
    hold = both(eng, clock, "point", "pinch", 16, mx=0.5)
    assert names(hold) == ["hand.drag_start"]
    xs = []
    for i in range(15):
        ev = both(eng, clock, "point", "pinch", mx=0.5 + i * 0.01)
        xs += [e.data["x"] for e in ev if e.name == "hand.cursor"]
    assert len(xs) >= 10 and xs[-1] > xs[0] + 0.1
    drop = both(eng, clock, "point", "relax", 4, mx=0.64)
    assert names(drop) == ["hand.drag_end"]


def test_two_hand_mode_click_hand_alone_still_clicks():
    eng, clock = two_hand_engine(), Clock()
    ev = []
    for pose, n in (("relax", 6), ("pinch", 4), ("relax", 4)):
        for _ in range(n):
            ev += eng.update(frame(clock.tick(), [make_hand(pose, x=0.3, handedness="Left")]))
    assert names(ev) == ["hand.pinch"]


def test_two_hand_mode_same_labels_fall_back_to_image_side():
    eng, clock = two_hand_engine(), Clock()
    both(eng, clock, "point", "relax", 8, move_label="Right", click_label="Right")
    ev = both(eng, clock, "point", "pinch", 4, move_label="Right", click_label="Right") + \
        both(eng, clock, "point", "relax", 4, move_label="Right", click_label="Right")
    assert names(ev).count("hand.pinch") == 1  # the hand on the right side of the image moves


def test_two_hand_mode_losing_click_hand_mid_drag_drops():
    eng, clock = two_hand_engine(), Clock()
    both(eng, clock, "point", "relax", 8)
    both(eng, clock, "point", "pinch", 16)
    assert eng.state.dragging
    ev = []
    for _ in range(12):  # only the cursor hand remains
        ev += eng.update(frame(clock.tick(), [make_hand("point", x=0.65, handedness="Right")]))
    assert names(ev) == ["hand.drag_end"] and not eng.state.dragging


def test_two_hand_mode_fist_stops_cursor_but_not_clicks():
    eng, clock = two_hand_engine(), Clock()
    both(eng, clock, "fist", "relax", 8)
    ev = both(eng, clock, "fist", "pinch", 4) + both(eng, clock, "fist", "relax", 4)
    assert "hand.cursor" not in names(ev, continuous=True)
    assert names(ev).count("hand.pinch") == 1


def test_two_hand_mode_click_hand_palm_does_not_pause_and_zoom_still_works():
    eng, clock = two_hand_engine(palm_hold_ms=600), Clock()
    ev = both(eng, clock, "point", "open", 40)
    assert "hand.palm_hold" not in names(ev)
    eng, clock = two_hand_engine(), Clock()
    zin = []
    for i in range(18):
        zin += both(eng, clock, "open", "open", mx=0.6 + i * 0.01, cx=0.4 - i * 0.01)
    assert "hand.zoom_in" in names(zin)
