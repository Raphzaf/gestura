"""Runs the vision models on one frame and returns a TrackingFrame.

Models are created once and reused (no per-frame reloads). Hand and face
inference can run concurrently: MediaPipe's C++ graph runs outside the GIL, so
two worker threads cut per-frame latency to roughly max(hand, face) instead of
their sum.
"""

from __future__ import annotations

import logging
import time
from concurrent.futures import ThreadPoolExecutor

import cv2
import mediapipe as mp
import numpy as np

from ..config.settings import CameraSettings, TrackingSettings
from ..core.types import TrackingFrame
from .face_tracker import FaceTracker
from .hand_tracker import HandTracker

log = logging.getLogger(__name__)


class FrameProcessor:
    def __init__(self, tracking: TrackingSettings, camera: CameraSettings) -> None:
        self.tracking = tracking
        self.camera = camera
        self._hand: HandTracker | None = None
        self._face: FaceTracker | None = None
        self._pool: ThreadPoolExecutor | None = None
        self._index = 0
        self._t0 = time.monotonic()
        self._hand_key: tuple | None = None
        self._face_key: tuple | None = None
        self.configure(tracking, camera)

    def configure(self, tracking: TrackingSettings, camera: CameraSettings) -> None:
        """(Re)create models only when their construction parameters change."""
        self.tracking, self.camera = tracking, camera
        hand_key = (tracking.num_hands, tracking.min_hand_detection_confidence,
                    tracking.min_hand_presence_confidence, tracking.min_tracking_confidence)
        if tracking.hands_enabled and hand_key != self._hand_key:
            if self._hand:
                self._hand.close()
            self._hand = HandTracker(*hand_key)
            self._hand_key = hand_key
        face_key = (tracking.min_face_detection_confidence, tracking.min_tracking_confidence)
        if tracking.face_enabled and face_key != self._face_key:
            if self._face:
                self._face.close()
            self._face = FaceTracker(face_key[0], 0.5, face_key[1])
            self._face_key = face_key
        if tracking.parallel_inference and self._pool is None:
            self._pool = ThreadPoolExecutor(max_workers=2, thread_name_prefix="gestura-infer")

    def process(self, frame_bgr: np.ndarray, captured_at: float | None = None) -> tuple[np.ndarray, TrackingFrame]:
        """Returns (display_frame_bgr, tracking_frame). The display frame is mirrored if configured."""
        captured_at = captured_at if captured_at is not None else time.monotonic()
        mirrored = self.camera.mirror
        frame = cv2.flip(frame_bgr, 1) if mirrored else frame_bgr
        rgb = np.ascontiguousarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        ts_ms = int((captured_at - self._t0) * 1000)
        h, w = frame.shape[:2]
        tf = TrackingFrame(timestamp=captured_at, index=self._index, width=w, height=h)
        self._index += 1

        run_hand = self.tracking.hands_enabled and self._hand is not None
        run_face = self.tracking.face_enabled and self._face is not None

        def do_hand():
            t = time.perf_counter()
            hands = self._hand.detect(image, ts_ms, mirrored)
            return hands, (time.perf_counter() - t) * 1000

        def do_face():
            t = time.perf_counter()
            face = self._face.detect(image, ts_ms, mirrored)
            return face, (time.perf_counter() - t) * 1000

        if run_hand and run_face and self._pool is not None and self.tracking.parallel_inference:
            fh = self._pool.submit(do_hand)
            ff = self._pool.submit(do_face)
            tf.hands, tf.hand_ms = fh.result()
            tf.face, tf.face_ms = ff.result()
        else:
            if run_hand:
                tf.hands, tf.hand_ms = do_hand()
            if run_face:
                tf.face, tf.face_ms = do_face()
        tf.total_ms = (time.monotonic() - captured_at) * 1000
        return frame, tf

    def close(self) -> None:
        if self._pool:
            self._pool.shutdown(wait=True)
            self._pool = None
        for tracker in (self._hand, self._face):
            if tracker:
                tracker.close()
        self._hand = self._face = None
        self._hand_key = self._face_key = None
