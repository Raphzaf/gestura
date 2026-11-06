"""Plain data types shared between layers.

Nothing here imports Qt, OpenCV or MediaPipe, so the gesture and command layers
can be unit-tested with synthetic data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(slots=True)
class HandObservation:
    """One detected hand in a single frame.

    landmarks: (21, 3) normalized image coordinates (x, y in 0..1 of the
        *displayed* — i.e. already mirrored — frame; z relative depth).
    world: (21, 3) metric coordinates in meters, origin near the hand center.
    handedness: "Left" or "Right" from the user's point of view
        (correct when the frame is mirrored, which is the default).
    """

    landmarks: np.ndarray
    world: np.ndarray
    handedness: str
    score: float


@dataclass(slots=True)
class HeadPose:
    """Head orientation in degrees, in the user's frame of reference.

    yaw > 0: user turned to their right (with a mirrored frame).
    pitch > 0: user nodded down.
    roll > 0: head tilted toward the user's right shoulder.
    """

    yaw: float
    pitch: float
    roll: float


@dataclass(slots=True)
class FaceObservation:
    landmarks: np.ndarray  # (478, 3) normalized image coordinates
    matrix: np.ndarray | None  # (4, 4) facial transformation matrix
    pose: HeadPose | None


@dataclass(slots=True)
class TrackingFrame:
    timestamp: float  # seconds, monotonic clock
    index: int
    width: int
    height: int
    hands: list[HandObservation] = field(default_factory=list)
    face: FaceObservation | None = None
    hand_ms: float = 0.0
    face_ms: float = 0.0
    total_ms: float = 0.0  # capture-to-result latency for this frame


@dataclass(slots=True)
class GestureEvent:
    """Output of a gesture engine. Never executes anything by itself."""

    name: str  # e.g. "hand.pinch", "head.turn_left"
    timestamp: float
    data: dict[str, Any] = field(default_factory=dict)
    label: str = ""
    continuous: bool = False  # True for cursor / scroll streams

    def __str__(self) -> str:  # pragma: no cover - debug helper
        return self.label or self.name
