# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura. Gestura is free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Eye, iris, mouth and eyebrow measurements from the 478 face landmarks.

Pure numpy: no MediaPipe, no Qt, so every rule built on top is unit-testable.

* **Eye openness** — the eye aspect ratio (EAR, Soukupová & Čech 2016): mean
  lid-to-lid distance divided by the eye width. Scale-free; about 0.2–0.35 for an
  open eye on MediaPipe's mesh and below ~0.1 when closed.
* **Iris position** — the iris centre (landmarks 468 / 473) expressed in the eye's
  own frame: ``h`` along the corner-to-corner axis (−0.5 … +0.5, + = toward the
  image right) and ``v`` across it (+ = down), both divided by the eye width.
* **Mouth** — inner-lip gap / mouth width (≈ 0 closed, > 0.35 clearly open) and
  mouth width / inter-ocular distance (rises when smiling).
* **Eyebrows** — mean brow-to-upper-lid distance / inter-ocular distance (rises
  when the brows are raised).

Landmarks are normalized image coordinates; x is scaled by the frame width and y
by its height before measuring, so non-square frames do not distort ratios.

User sides: in the default mirrored (selfie) frame the user's left eye is the
one on the image left. ``mirrored=False`` swaps them.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

# MediaPipe face mesh indices. Eye "A" uses corners 33/133 and iris 468; eye "B"
# uses corners 362/263 and iris 473 (checked on real photos).
EYE_A = (33, 160, 158, 133, 153, 144)  # p1 corner, p2 p3 upper lid, p4 corner, p5 p6 lower lid
EYE_B = (362, 385, 387, 263, 373, 380)
IRIS_A, IRIS_B = 468, 473
BROW_A, LID_A = 105, 159
BROW_B, LID_B = 334, 386
MOUTH_UPPER, MOUTH_LOWER = 13, 14
MOUTH_LEFT, MOUTH_RIGHT = 78, 308
OUTER_A, OUTER_B = 33, 263
EYE_CONTOURS = (
    (33, 160), (160, 158), (158, 133), (133, 153), (153, 144), (144, 33),
    (362, 385), (385, 387), (387, 263), (263, 373), (373, 380), (380, 362),
)
MIN_LANDMARKS = 478


@dataclass(slots=True)
class EyeMeasure:
    ear: float  # eye aspect ratio
    h: float  # iris along the eye axis, -0.5..0.5 (+ = image right)
    v: float  # iris across the eye axis (+ = down), in eye widths
    center: tuple[float, float]  # eye centre, normalized image coordinates


@dataclass(slots=True)
class FaceFeatures:
    left: EyeMeasure  # the user's left eye
    right: EyeMeasure  # the user's right eye
    mouth_open: float  # inner-lip gap / mouth width
    smile: float  # mouth width / inter-ocular distance
    brows: float  # mean brow-to-lid distance / inter-ocular distance

    @property
    def gaze_h(self) -> float:
        return (self.left.h + self.right.h) / 2

    @property
    def gaze_v(self) -> float:
        return (self.left.v + self.right.v) / 2

    @property
    def ear(self) -> float:
        return (self.left.ear + self.right.ear) / 2


def _eye(p: np.ndarray, idx: tuple[int, ...], iris: int) -> EyeMeasure:
    c1, u1, u2, c2, l2, l1 = (p[i] for i in idx)
    width = float(np.linalg.norm(c2 - c1)) or 1e-6
    ear = (float(np.linalg.norm(u1 - l1)) + float(np.linalg.norm(u2 - l2))) / (2 * width)
    # Eye axis pointing toward the image right, normal pointing down.
    a, b = (c1, c2) if c1[0] <= c2[0] else (c2, c1)
    axis = (b - a) / width
    normal = np.array([-axis[1], axis[0]])
    if normal[1] < 0:
        normal = -normal
    mid = (a + b) / 2
    rel = p[iris] - mid
    return EyeMeasure(ear=ear, h=float(rel @ axis) / width, v=float(rel @ normal) / width,
                      center=(float(mid[0]), float(mid[1])))


def extract(landmarks: np.ndarray, width: int, height: int, mirrored: bool = True) -> FaceFeatures | None:
    """Measure one face. Returns None when the mesh has no iris points."""
    if landmarks is None or len(landmarks) < MIN_LANDMARKS:
        return None
    p = np.asarray(landmarks, dtype=np.float64)[:, :2] * (float(width), float(height))
    a = _eye(p, EYE_A, IRIS_A)
    b = _eye(p, EYE_B, IRIS_B)
    # Normalize the eye centres back to 0..1 for drawing.
    a.center = (a.center[0] / width, a.center[1] / height)
    b.center = (b.center[0] / width, b.center[1] / height)
    image_left, image_right = (a, b) if a.center[0] <= b.center[0] else (b, a)
    left, right = (image_left, image_right) if mirrored else (image_right, image_left)

    inter = float(np.linalg.norm(p[OUTER_A] - p[OUTER_B])) or 1e-6
    mouth_w = float(np.linalg.norm(p[MOUTH_LEFT] - p[MOUTH_RIGHT])) or 1e-6
    gap = float(np.linalg.norm(p[MOUTH_UPPER] - p[MOUTH_LOWER]))
    brows = (float(np.linalg.norm(p[BROW_A] - p[LID_A])) + float(np.linalg.norm(p[BROW_B] - p[LID_B]))) / (2 * inter)
    return FaceFeatures(left=left, right=right, mouth_open=gap / mouth_w, smile=mouth_w / inter, brows=brows)
