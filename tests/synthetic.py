"""Synthetic hand generator for deterministic gesture tests.

Builds a 21-landmark articulated hand (metric world coordinates) from per-finger
curl angles, then projects it to normalized image coordinates at a chosen
position. Proportions approximate an adult hand (palm ≈ 9 cm).
"""

from __future__ import annotations

import math

import numpy as np

from gestura.core.types import HandObservation, TrackingFrame

MCP = {  # finger -> (mcp x, mcp y), meters, wrist at origin, fingers point +y
    "index": (-0.025, 0.085), "middle": (0.0, 0.090), "ring": (0.020, 0.085), "pinky": (0.038, 0.075)}
SEG = {"index": (0.040, 0.025, 0.020), "middle": (0.045, 0.028, 0.021),
       "ring": (0.042, 0.026, 0.020), "pinky": (0.032, 0.020, 0.018)}
BASE = {"index": 5, "middle": 9, "ring": 13, "pinky": 17}

STRAIGHT = (0.0, 0.0, 0.0)
CURLED = (60.0, 95.0, 70.0)
HALF = (25.0, 35.0, 20.0)


def _finger(name: str, curl: tuple[float, float, float]) -> list[np.ndarray]:
    x, y = MCP[name]
    p = np.array([x, y, 0.0])
    pts = [p.copy()]
    angle = 0.0
    for seg, c in zip(SEG[name], curl):
        angle += math.radians(c)
        # curl rotates the bone from +y toward -z (into the palm)
        d = np.array([0.0, math.cos(angle), -math.sin(angle)])
        p = p + d * seg
        pts.append(p.copy())
    return pts  # mcp, pip, dip, tip


def make_world(curls: dict[str, tuple[float, float, float]], thumb_tip: np.ndarray | None = None,
               thumb_out: bool = False) -> np.ndarray:
    w = np.zeros((21, 3))
    for name, base in BASE.items():
        for k, p in enumerate(_finger(name, curls.get(name, STRAIGHT))):
            w[base + k] = p
    # thumb: CMC, MCP, IP, TIP
    if thumb_out:
        chain = [(-0.020, 0.020, 0), (-0.045, 0.040, 0), (-0.065, 0.055, 0), (-0.080, 0.068, 0)]
    else:
        chain = [(-0.020, 0.020, 0), (-0.035, 0.040, -0.010), (-0.030, 0.055, -0.025), (-0.020, 0.065, -0.035)]
    for k, p in enumerate(chain):
        w[1 + k] = p
    if thumb_tip is not None:
        w[4] = thumb_tip
        w[3] = (w[2] + thumb_tip) / 2
    return w


def pose_world(pose: str) -> np.ndarray:
    if pose == "open":
        return make_world({}, thumb_out=True)
    if pose == "fist":
        w = make_world({f: CURLED for f in BASE})
        # thumb lies across the index/middle middle phalanges (like the real fist photo)
        w = make_world({f: CURLED for f in BASE}, thumb_tip=(w[6] + w[10]) / 2 + np.array([0, 0, -0.012]))
        return w
    if pose == "point":
        w = make_world({"middle": CURLED, "ring": CURLED, "pinky": CURLED})
        # thumb resting on the curled middle finger (the right-click false-positive trap)
        return make_world({"middle": CURLED, "ring": CURLED, "pinky": CURLED},
                          thumb_tip=w[11] + np.array([0.0, 0.0, -0.012]))
    if pose == "two":
        return make_world({"ring": CURLED, "pinky": CURLED})
    if pose == "pinch":
        w = make_world({"index": HALF, "middle": CURLED, "ring": CURLED, "pinky": CURLED})
        return make_world({"index": HALF, "middle": CURLED, "ring": CURLED, "pinky": CURLED},
                          thumb_tip=w[8] + np.array([0.006, 0.0, 0.006]))
    if pose == "middle_pinch":
        w = make_world({"middle": HALF, "ring": CURLED, "pinky": CURLED})
        return make_world({"middle": HALF, "ring": CURLED, "pinky": CURLED},
                          thumb_tip=w[12] + np.array([0.006, 0.0, 0.006]))
    raise ValueError(pose)


def make_hand(pose: str, x: float = 0.5, y: float = 0.6, handedness: str = "Right",
              scale: float = 1.6, score: float = 0.97) -> HandObservation:
    world = pose_world(pose)
    lm = np.zeros((21, 3), dtype=np.float32)
    # wrist at (x, y); index fingertip roughly 0.25 frame-heights above
    lm[:, 0] = x + world[:, 0] * scale
    lm[:, 1] = y - world[:, 1] * scale
    lm[:, 2] = world[:, 2]
    return HandObservation(landmarks=lm, world=world.astype(np.float32), handedness=handedness, score=score)


def frame(t: float, hands=None, face=None, index: int = 0) -> TrackingFrame:
    return TrackingFrame(timestamp=t, index=index, width=640, height=480, hands=list(hands or []), face=face)


class Clock:
    """Feeds frames at a fixed rate into an engine."""

    def __init__(self, fps: float = 30.0, t0: float = 100.0) -> None:
        self.t = t0
        self.dt = 1.0 / fps
        self.i = 0

    def tick(self) -> float:
        self.t += self.dt
        self.i += 1
        return self.t
