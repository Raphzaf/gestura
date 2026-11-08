# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura. Gestura is free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Webcam gaze estimation: iris position -> point on screen.

A per-user regression learned from a short calibration (the user looks at dots):

    features   f = (h, v, ear)       iris position in the eye frame + eye opening
    screen     (u, v) = P(f) · c     second-order polynomial, ridge-regularized
               + head compensation   gain · (head angle − head angle at calibration)

The eye opening is a feature because the upper lid follows vertical gaze: it is
the most reliable vertical cue a webcam gets. Head compensation is physical
rather than learned (users keep their head still while calibrating, so a learned
head term would be meaningless): gaze direction = head direction + eye-in-head
direction, and the screen spans about ±``screen_half_angle_deg`` from the eyes.

Expect an accuracy of a few degrees, i.e. 100–250 px on a 1080p screen at 60 cm.
That is enough for large targets and for coarse pointing that the head then
refines (the hybrid pointer); it is not mouse precision.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

N_FEATURES = 3
N_TERMS = 7  # 1, h, v, e, h², v², h·v
MODEL_LEN = 2 * N_FEATURES + 2 * N_TERMS + 2


def _design(z: np.ndarray) -> np.ndarray:
    h, v, e = z[:, 0], z[:, 1], z[:, 2]
    return np.column_stack([np.ones(len(z)), h, v, e, h * h, v * v, h * v])


@dataclass(slots=True)
class GazeModel:
    mean: np.ndarray  # (3,) feature means at calibration
    std: np.ndarray  # (3,) feature scales
    cx: np.ndarray  # (7,) coefficients for screen x
    cy: np.ndarray  # (7,) coefficients for screen y
    yaw0: float  # mean head yaw during calibration (deg)
    pitch0: float  # mean head pitch during calibration (deg)

    def predict(self, features: np.ndarray | tuple[float, float, float], yaw: float = 0.0,
                pitch: float = 0.0, half_angle_deg: float = 0.0) -> tuple[float, float]:
        """Screen point (0..1, may overshoot) for one sample. half_angle 0 = no head compensation."""
        z = (np.asarray(features, dtype=np.float64).reshape(1, N_FEATURES) - self.mean) / self.std
        d = _design(z)
        u, v = float((d @ self.cx)[0]), float((d @ self.cy)[0])
        if half_angle_deg > 0:
            gain = 0.5 / half_angle_deg
            u += gain * (yaw - self.yaw0)
            v += gain * (pitch - self.pitch0)
        return u, v

    def to_list(self) -> list[float]:
        return [float(x) for x in (*self.mean, *self.std, *self.cx, *self.cy, self.yaw0, self.pitch0)]

    @classmethod
    def from_list(cls, values: list[float] | None) -> "GazeModel | None":
        if not values or len(values) != MODEL_LEN:
            return None
        a = np.asarray(values, dtype=np.float64)
        n, t = N_FEATURES, N_TERMS
        std = a[n:2 * n]
        if not np.all(np.isfinite(a)) or np.any(std <= 0):
            return None
        return cls(mean=a[:n], std=std, cx=a[2 * n:2 * n + t], cy=a[2 * n + t:2 * n + 2 * t],
                   yaw0=float(a[-2]), pitch0=float(a[-1]))


def fit(features: np.ndarray, targets: np.ndarray, yaw: np.ndarray | None = None,
        pitch: np.ndarray | None = None, ridge: float = 0.05) -> GazeModel:
    """Fit from N samples: features (N, 3), targets (N, 2) in 0..1 screen units.

    Raises ValueError when the samples cannot support a fit (too few, or no spread).
    """
    x = np.asarray(features, dtype=np.float64)
    y = np.asarray(targets, dtype=np.float64)
    if x.ndim != 2 or x.shape[1] != N_FEATURES or len(x) != len(y) or len(x) < N_TERMS + 2:
        raise ValueError("not enough calibration samples")
    if len({(round(a, 3), round(b, 3)) for a, b in y}) < 5:
        raise ValueError("calibration needs at least 5 distinct targets")
    mean = x.mean(axis=0)
    std = x.std(axis=0)
    if std[0] < 1e-6 and std[1] < 1e-6:
        raise ValueError("the eyes did not move during calibration")
    std = np.where(std < 1e-6, 1.0, std)  # a constant feature simply drops out
    z = (x - mean) / std
    d = _design(z)
    reg = ridge * np.eye(N_TERMS)
    reg[0, 0] = 0.0  # never shrink the intercept
    a = d.T @ d + reg
    cx = np.linalg.solve(a, d.T @ y[:, 0])
    cy = np.linalg.solve(a, d.T @ y[:, 1])
    yaw0 = float(np.mean(yaw)) if yaw is not None and len(yaw) else 0.0
    pitch0 = float(np.mean(pitch)) if pitch is not None and len(pitch) else 0.0
    return GazeModel(mean=mean, std=std, cx=cx, cy=cy, yaw0=yaw0, pitch0=pitch0)


def point_errors(model: GazeModel, features: np.ndarray, targets: np.ndarray,
                 yaw: np.ndarray | None = None, pitch: np.ndarray | None = None,
                 half_angle_deg: float = 0.0, aspect: float = 16 / 9) -> list[float]:
    """Error per target (mean prediction vs target), in screen *heights*.

    Samples are grouped by target; averaging predictions per target mirrors what
    the smoothed pointer shows while the user fixates.
    """
    x = np.asarray(features, dtype=np.float64)
    y = np.asarray(targets, dtype=np.float64)
    yw = np.zeros(len(x)) if yaw is None else np.asarray(yaw, dtype=np.float64)
    pt = np.zeros(len(x)) if pitch is None else np.asarray(pitch, dtype=np.float64)
    groups: dict[tuple[float, float], list[tuple[float, float]]] = {}
    for f, t, a, b in zip(x, y, yw, pt):
        groups.setdefault((round(float(t[0]), 4), round(float(t[1]), 4)), []).append(
            model.predict(f, a, b, half_angle_deg))
    errors = []
    for (tu, tv), preds in groups.items():
        pu, pv = np.mean(preds, axis=0)
        errors.append(float(np.hypot((pu - tu) * aspect, pv - tv)))
    return errors


CALIBRATION_POINTS: tuple[tuple[float, float], ...] = (
    (0.5, 0.5), (0.08, 0.08), (0.5, 0.08), (0.92, 0.08), (0.92, 0.5),
    (0.92, 0.92), (0.5, 0.92), (0.08, 0.92), (0.08, 0.5),
)
VALIDATION_POINTS: tuple[tuple[float, float], ...] = (
    (0.28, 0.28), (0.72, 0.28), (0.72, 0.72), (0.28, 0.72),
)
