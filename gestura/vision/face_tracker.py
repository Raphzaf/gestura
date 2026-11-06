"""MediaPipe Face Landmarker wrapper (Tasks API, VIDEO running mode)."""

from __future__ import annotations

import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions, vision

from ..core.types import FaceObservation
from .head_pose_estimator import head_pose_from_matrix
from .models import FACE_MODEL, model_path

# A light subset of the mesh for drawing (contours, not the full tesselation).
FACE_CONTOURS: list[tuple[int, int]] = [
    (c.start, c.end) for c in vision.FaceLandmarksConnections.FACE_LANDMARKS_CONTOURS
]
NOSE_TIP = 1


class FaceTracker:
    def __init__(self, min_detection: float = 0.5, min_presence: float = 0.5, min_tracking: float = 0.5) -> None:
        options = vision.FaceLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(model_path(FACE_MODEL))),
            running_mode=vision.RunningMode.VIDEO,
            num_faces=1,
            min_face_detection_confidence=min_detection,
            min_face_presence_confidence=min_presence,
            min_tracking_confidence=min_tracking,
            output_facial_transformation_matrixes=True,
        )
        self._landmarker = vision.FaceLandmarker.create_from_options(options)
        self._last_ts = -1

    def detect(self, image: mp.Image, timestamp_ms: int, mirrored: bool = True) -> FaceObservation | None:
        ts = max(timestamp_ms, self._last_ts + 1)
        self._last_ts = ts
        result = self._landmarker.detect_for_video(image, ts)
        if not result.face_landmarks:
            return None
        lms = np.array([(p.x, p.y, p.z) for p in result.face_landmarks[0]], dtype=np.float32)
        matrix = None
        pose = None
        if result.facial_transformation_matrixes:
            matrix = np.asarray(result.facial_transformation_matrixes[0], dtype=np.float64)
            pose = head_pose_from_matrix(matrix, mirrored=mirrored)
        return FaceObservation(landmarks=lms, matrix=matrix, pose=pose)

    def close(self) -> None:
        if self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None
