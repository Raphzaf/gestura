"""Personal calibration: neutral head pose and pinch thresholds."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..core.types import HeadPose


@dataclass(slots=True)
class NeutralResult:
    ok: bool
    yaw: float = 0.0
    pitch: float = 0.0
    roll: float = 0.0
    spread: float = 0.0  # worst per-axis std-dev (degrees)
    samples: int = 0
    message: str = ""


class NeutralPoseCalibrator:
    """Collect head poses while the user looks straight at the screen."""

    def __init__(self, min_samples: int = 20, max_spread_deg: float = 3.5) -> None:
        self.min_samples = min_samples
        self.max_spread_deg = max_spread_deg
        self._samples: list[tuple[float, float, float]] = []

    def add(self, pose: HeadPose | None) -> None:
        if pose is not None:
            self._samples.append((pose.yaw, pose.pitch, pose.roll))

    @property
    def count(self) -> int:
        return len(self._samples)

    def result(self) -> NeutralResult:
        n = len(self._samples)
        if n < self.min_samples:
            return NeutralResult(False, samples=n, message="Face not visible long enough. Look at the screen and try again.")
        arr = np.array(self._samples)
        med = np.median(arr, axis=0)
        spread = float(arr.std(axis=0).max())
        if spread > self.max_spread_deg:
            return NeutralResult(False, *med, spread=spread, samples=n,
                                 message="Too much head movement. Hold still and try again.")
        return NeutralResult(True, float(med[0]), float(med[1]), float(med[2]), spread, n, "Neutral position saved.")


@dataclass(slots=True)
class PinchResult:
    ok: bool
    on_ratio: float = 0.0
    off_ratio: float = 0.0
    message: str = ""


class PinchCalibrator:
    """Learn a user's pinch thresholds from relaxed-pointing and pinched samples."""

    def __init__(self, min_samples: int = 10) -> None:
        self.min_samples = min_samples
        self.open: list[float] = []
        self.closed: list[float] = []

    def result(self) -> PinchResult:
        if len(self.open) < self.min_samples or len(self.closed) < self.min_samples:
            return PinchResult(False, message="Not enough samples; keep your hand visible.")
        closed_hi = float(np.percentile(self.closed, 90))
        open_lo = float(np.percentile(self.open, 10))
        gap = open_lo - closed_hi
        if gap < 0.08:
            return PinchResult(False, message="Pinched and open positions are too similar. Pinch firmly, then open clearly.")
        on = round(closed_hi + gap * 0.35, 3)
        off = round(closed_hi + gap * 0.65, 3)
        return PinchResult(True, on, off, f"Pinch closes below {on:.2f}, opens above {off:.2f}.")
