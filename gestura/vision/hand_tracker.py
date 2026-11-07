# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""MediaPipe Hand Landmarker wrapper (Tasks API, VIDEO running mode)."""

from __future__ import annotations

import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

from ..core.types import HandObservation
from .models import HAND_MODEL, model_path

HAND_CONNECTIONS: list[tuple[int, int]] = [
    (c.start, c.end) for c in vision.HandLandmarksConnections.HAND_CONNECTIONS
]


class HandTracker:
    def __init__(self, num_hands: int = 2, min_detection: float = 0.6,
                 min_presence: float = 0.5, min_tracking: float = 0.5) -> None:
        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path(HAND_MODEL))),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=num_hands,
            min_hand_detection_confidence=min_detection,
            min_hand_presence_confidence=min_presence,
            min_tracking_confidence=min_tracking,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)
        self._last_ts = -1

    def detect(self, image: mp.Image, timestamp_ms: int, mirrored: bool = True) -> list[HandObservation]:
        # VIDEO mode requires strictly increasing timestamps.
        ts = max(timestamp_ms, self._last_ts + 1)
        self._last_ts = ts
        result = self._landmarker.detect_for_video(image, ts)
        hands: list[HandObservation] = []
        for lms, world, handed in zip(result.hand_landmarks, result.hand_world_landmarks, result.handedness):
            label = handed[0].category_name if handed else "Unknown"
            if not mirrored:
                # MediaPipe assumes a mirrored (selfie) image when labelling.
                label = {"Left": "Right", "Right": "Left"}.get(label, label)
            hands.append(
                HandObservation(
                    landmarks=np.array([(p.x, p.y, p.z) for p in lms], dtype=np.float32),
                    world=np.array([(p.x, p.y, p.z) for p in world], dtype=np.float32),
                    handedness=label,
                    score=float(handed[0].score) if handed else 0.0,
                )
            )
        return hands

    def close(self) -> None:
        if self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None
