"""Vision pipeline tests with the real MediaPipe models (no webcam needed)."""

import time

import cv2
import numpy as np
import pytest

from gestura.config.settings import Settings
from gestura.vision.camera_manager import ImageSource, VideoFileSource, make_source
from gestura.vision.models import FACE_MODEL, HAND_MODEL, MODEL_SHA256, model_path


def test_bundled_models_match_pinned_hashes():
    import hashlib

    for name in (HAND_MODEL, FACE_MODEL):
        assert hashlib.sha256(model_path(name).read_bytes()).hexdigest() == MODEL_SHA256[name]


def test_frame_processor_runs_both_models_on_a_frame():
    from gestura.vision.frame_processor import FrameProcessor

    s = Settings()
    p = FrameProcessor(s.tracking, s.camera)
    try:
        frame = np.full((480, 640, 3), 90, np.uint8)
        display, tf = p.process(frame)
        assert display.shape == frame.shape and tf.hands == [] and tf.face is None
        assert tf.hand_ms > 0 and tf.face_ms > 0 and tf.width == 640
        _, tf2 = p.process(frame)
        assert tf2.index == tf.index + 1  # timestamps/indices keep increasing
    finally:
        p.close()


def test_video_and_image_sources(tmp_path):
    path = tmp_path / "clip.avi"
    w = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"MJPG"), 30, (160, 120))
    for i in range(6):
        w.write(np.full((120, 160, 3), i * 40, np.uint8))
    w.release()
    src = make_source(str(path), Settings().camera)
    assert isinstance(src, VideoFileSource) and src.open()
    frames = [src.read() for _ in range(8)]  # loops past the end
    assert all(f is not None and f.shape == (120, 160, 3) for f in frames)
    src.release()

    img = tmp_path / "a.png"
    cv2.imwrite(str(img), np.zeros((50, 60, 3), np.uint8))
    s2 = make_source(str(tmp_path), Settings().camera)
    assert isinstance(s2, ImageSource) and s2.open() and s2.read().shape == (50, 60, 3)
    assert make_source("2", Settings().camera).index == 2


class FlakyCamera:
    """Delivers frames, then stops (unplugged), then works again after reopening."""

    is_live = True
    name = "Flaky camera"
    opens = 0

    def open(self):
        FlakyCamera.opens += 1
        self.n = 0
        return True

    def read(self):
        self.n += 1
        time.sleep(0.01)
        if FlakyCamera.opens == 1 and self.n > 5:
            return None  # unplugged
        return np.full((240, 320, 3), 80, np.uint8)

    def release(self):
        pass


def test_worker_recovers_from_camera_disconnect(monkeypatch):
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from gestura.core.command_engine import CommandEngine
    from gestura.core.event_bus import EventBus
    from gestura.core.safety_manager import SafetyManager
    from gestura.services import tracking_service as ts
    from gestura.vision import camera_manager

    app = QApplication.instance() or QApplication([])  # GUI app: other test modules need widgets
    FlakyCamera.opens = 0
    monkeypatch.setattr(camera_manager, "make_source", lambda spec, cam: FlakyCamera())
    monkeypatch.setattr(ts.TrackingWorker, "LOST_AFTER_S", 0.2)
    monkeypatch.setattr(ts.TrackingWorker, "RECONNECT_S", 0.2)
    w = ts.TrackingWorker(Settings(), CommandEngine(SafetyManager()), EventBus())
    w.preview_enabled = False
    statuses = []
    w.camera_status.connect(lambda s, m: statuses.append(s), Qt.ConnectionType.DirectConnection)
    w.start()
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline and not (FlakyCamera.opens >= 2 and w.frames_processed > 10):
        app.processEvents()
        time.sleep(0.05)
    w.request_stop()
    w.wait(5000)
    assert "lost" in statuses, statuses
    assert FlakyCamera.opens >= 2 and w.frames_processed > 10
    assert statuses[-1] == "off"
