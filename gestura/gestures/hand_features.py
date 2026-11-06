"""Per-frame geometric features of a hand.

Features use MediaPipe's *world* landmarks (metric, hand-centred) so they are
independent of camera distance, image aspect ratio and in-plane rotation.
Distances are normalized by palm size (wrist -> middle-finger knuckle), which
makes thresholds portable between users and cameras.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass

import numpy as np

from ..core.types import HandObservation

WRIST = 0
THUMB = (1, 2, 3, 4)
INDEX = (5, 6, 7, 8)
MIDDLE = (9, 10, 11, 12)
RING = (13, 14, 15, 16)
PINKY = (17, 18, 19, 20)
FINGERS = (INDEX, MIDDLE, RING, PINKY)

# A finger counts as extended when its "reach" (straight-line wrist->tip
# distance over the length of the bone chain) exceeds EXTENDED_REACH.
# Measured on sample photos: straight fingers ≈ 0.93–0.99, fully curled
# ≈ 0.45–0.70; the gap between is the uncertainty band.
EXTENDED_REACH = 0.84
CURLED_REACH = 0.78


class Pose(str, enum.Enum):
    NONE = "none"
    OPEN = "open_palm"
    FIST = "fist"
    POINT = "point"
    TWO = "two_fingers"
    OTHER = "other"


@dataclass(slots=True)
class HandFeatures:
    palm_size: float
    reach: tuple[float, float, float, float]  # index, middle, ring, pinky
    extended: tuple[bool, bool, bool, bool]
    curled: tuple[bool, bool, bool, bool]
    thumb_index: float  # pinch ratio (distance / palm size)
    thumb_middle: float
    pose: Pose
    palm_center: tuple[float, float]  # normalized image coords
    index_tip: tuple[float, float]
    index_mcp: tuple[float, float]
    two_tip: tuple[float, float]  # midpoint of index + middle tips


def _reach(world: np.ndarray, chain: tuple[int, ...]) -> float:
    pts = world[[WRIST, *chain]]
    bones = np.linalg.norm(np.diff(pts, axis=0), axis=1).sum()
    if bones <= 1e-9:
        return 0.0
    return float(np.linalg.norm(pts[-1] - pts[0]) / bones)


def classify(extended: tuple[bool, ...], curled: tuple[bool, ...]) -> Pose:
    i, m, r, p = extended
    ci, cm, cr, cp = curled
    if all(extended):
        return Pose.OPEN
    if all(curled):
        return Pose.FIST
    if i and cm and cr and cp:
        return Pose.POINT
    if i and m and cr and cp:
        return Pose.TWO
    return Pose.OTHER


def compute(hand: HandObservation) -> HandFeatures:
    w = hand.world
    palm = float(np.linalg.norm(w[MIDDLE[0]] - w[WRIST])) or 1e-6
    reach = tuple(_reach(w, f) for f in FINGERS)
    extended = tuple(r >= EXTENDED_REACH for r in reach)
    curled = tuple(r < CURLED_REACH for r in reach)
    thumb_index = float(np.linalg.norm(w[THUMB[-1]] - w[INDEX[-1]]) / palm)
    thumb_middle = float(np.linalg.norm(w[THUMB[-1]] - w[MIDDLE[-1]]) / palm)
    lm = hand.landmarks
    palm_center = tuple(float(v) for v in lm[[WRIST, 5, 9, 13, 17], :2].mean(axis=0))
    return HandFeatures(
        palm_size=palm,
        reach=reach,  # type: ignore[arg-type]
        extended=extended,  # type: ignore[arg-type]
        curled=curled,  # type: ignore[arg-type]
        thumb_index=thumb_index,
        thumb_middle=thumb_middle,
        pose=classify(extended, curled),
        palm_center=palm_center,  # type: ignore[arg-type]
        index_tip=(float(lm[8, 0]), float(lm[8, 1])),
        index_mcp=(float(lm[5, 0]), float(lm[5, 1])),
        two_tip=(float((lm[8, 0] + lm[12, 0]) / 2), float((lm[8, 1] + lm[12, 1]) / 2)),
    )
