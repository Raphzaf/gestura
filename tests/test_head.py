import json
from pathlib import Path

import numpy as np
import pytest
from synthetic import Clock, frame

from gestura.config.settings import HeadGestureSettings
from gestura.core.types import FaceObservation, HeadPose
from gestura.gestures.calibration import NeutralPoseCalibrator, PinchCalibrator
from gestura.gestures.head_gestures import HeadGestureEngine
from gestura.vision.head_pose_estimator import euler_from_matrix, head_pose_from_matrix, rotation_matrix

DATA = json.loads((Path(__file__).parent / "data" / "real_landmarks.json").read_text())


@pytest.mark.parametrize("ypr", [(0, 0, 0), (20, 0, 0), (0, -15, 0), (0, 0, 25), (12, -8, 5), (-30, 20, -10)])
def test_euler_round_trip(ypr):
    assert euler_from_matrix(rotation_matrix(*ypr)) == pytest.approx(ypr, abs=1e-6)


def test_scaled_matrix_is_normalized():
    m = np.eye(4)
    m[:3, :3] = rotation_matrix(10, 5, -3) * 1.7
    assert euler_from_matrix(m) == pytest.approx((10, 5, -3), abs=1e-6)


def test_real_frontal_portrait_is_near_zero():
    pose = head_pose_from_matrix(np.array(DATA["portrait"]["face_matrix"]))
    assert abs(pose.yaw) < 5 and abs(pose.pitch) < 6 and abs(pose.roll) < 5


def test_real_photo_downward_head_has_positive_pitch():
    # In the business-person photo the head is tilted down and turned slightly.
    pose = head_pose_from_matrix(np.array(DATA["business-person"]["face_matrix"]))
    assert pose.pitch > 8


def test_unmirrored_flips_yaw_and_roll():
    m = rotation_matrix(15, 5, 10)
    a, b = head_pose_from_matrix(m, True), head_pose_from_matrix(m, False)
    assert a.yaw == pytest.approx(-b.yaw) and a.roll == pytest.approx(-b.roll) and a.pitch == pytest.approx(b.pitch)


# --------------------------------------------------------------------------- gestures
def face(yaw=0.0, pitch=0.0, roll=0.0):
    return FaceObservation(landmarks=np.zeros((478, 3)), matrix=None, pose=HeadPose(yaw, pitch, roll))


def run(eng, clock, n, **pose):
    out = []
    for _ in range(n):
        out += eng.update(frame(clock.tick(), face=face(**pose)))
    return [e.name for e in out]


def mk(**kw):
    s = HeadGestureSettings(smoothing=0.0, **kw)
    return HeadGestureEngine(s), Clock()


def test_not_armed_until_neutral_seen():
    eng, clock = mk()
    assert run(eng, clock, 20, yaw=30) == []  # starts turned: never armed


def test_turn_right_fires_once_after_min_duration():
    eng, clock = mk(min_duration_ms=200)
    run(eng, clock, 10)
    assert run(eng, clock, 4, yaw=25) == []  # 133 ms < 200 ms
    assert run(eng, clock, 30, yaw=25) == ["head.turn_right"]


def test_brief_glance_is_ignored():
    eng, clock = mk(min_duration_ms=250)
    run(eng, clock, 10)
    assert run(eng, clock, 5, yaw=-30) + run(eng, clock, 10) == []


def test_requires_return_to_neutral_before_next():
    eng, clock = mk(min_duration_ms=100, cooldown_ms=300)
    run(eng, clock, 10)
    assert run(eng, clock, 10, yaw=-25) == ["head.turn_left"]
    assert run(eng, clock, 30, yaw=-25) == []  # still turned: no repeat
    run(eng, clock, 10)  # back to neutral (re-arm)
    assert run(eng, clock, 10, yaw=-25) == ["head.turn_left"]


@pytest.mark.parametrize("pose,expected", [
    ({"pitch": 18}, "head.nod_down"), ({"pitch": -18}, "head.tilt_up"),
    ({"yaw": 25}, "head.turn_right"), ({"roll": 30}, "head.roll_right")])
def test_each_axis(pose, expected):
    eng, clock = mk(min_duration_ms=100)
    run(eng, clock, 10)
    assert run(eng, clock, 15, **pose) == [expected]


def test_diagonal_movement_is_rejected():
    eng, clock = mk(min_duration_ms=100)
    run(eng, clock, 10)
    assert run(eng, clock, 30, yaw=22, pitch=15) == []


def test_neutral_offset_and_inversion():
    eng, clock = mk(min_duration_ms=100, neutral_yaw=10.0)
    run(eng, clock, 10, yaw=10)  # this is neutral now
    assert run(eng, clock, 15, yaw=22) == []  # only 12 deg relative
    eng, clock = mk(min_duration_ms=100, invert_yaw=True)
    run(eng, clock, 10)
    assert run(eng, clock, 15, yaw=25) == ["head.turn_left"]


def test_face_lost_disarms():
    eng, clock = mk(min_duration_ms=100)
    run(eng, clock, 10)
    eng.update(frame(clock.tick()))  # no face
    assert not eng.state.armed
    assert run(eng, clock, 15, yaw=25) == []


def test_smoothing_delays_but_still_fires():
    s = HeadGestureSettings(smoothing=0.6, min_duration_ms=100)
    eng, clock = HeadGestureEngine(s), Clock()
    run(eng, clock, 10)
    assert run(eng, clock, 30, yaw=30) == ["head.turn_right"]


# --------------------------------------------------------------------------- calibration
def test_neutral_calibration():
    cal = NeutralPoseCalibrator(min_samples=10)
    rng = np.random.default_rng(1)
    for _ in range(30):
        cal.add(HeadPose(5 + rng.normal(0, 1), -3 + rng.normal(0, 1), rng.normal(0, 1)))
    r = cal.result()
    assert r.ok and r.yaw == pytest.approx(5, abs=1) and r.pitch == pytest.approx(-3, abs=1)


def test_neutral_calibration_rejects_movement_and_too_few():
    cal = NeutralPoseCalibrator(min_samples=10)
    assert not cal.result().ok
    for i in range(30):
        cal.add(HeadPose(i * 2.0, 0, 0))
    assert not cal.result().ok


def test_pinch_calibration():
    cal = PinchCalibrator(min_samples=5)
    cal.open = [0.8, 0.9, 0.85, 0.95, 0.7, 0.88]
    cal.closed = [0.1, 0.12, 0.15, 0.09, 0.11, 0.13]
    r = cal.result()
    assert r.ok and 0.15 < r.on_ratio < r.off_ratio < 0.7
    cal.open = [0.2] * 6
    assert not cal.result().ok
