# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Frame sources: physical cameras, video files and still images.

All sources return BGR uint8 frames. Video files and images exist so the whole
pipeline (and the UI) can be exercised without a webcam — useful for
development, CI and reproducing tracking issues from a recording.
Nothing is ever written to disk by these classes.
"""

from __future__ import annotations

import logging
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

import cv2
import numpy as np

log = logging.getLogger(__name__)

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}


class FrameSource(Protocol):
    name: str

    def open(self) -> bool: ...
    def read(self) -> np.ndarray | None: ...
    def release(self) -> None: ...
    @property
    def is_live(self) -> bool: ...


def _backend_flag(backend: str) -> int:
    if sys.platform != "win32" or backend == "any":
        return cv2.CAP_ANY
    if backend == "msmf":
        return cv2.CAP_MSMF
    # "auto" and "dshow": DirectShow opens much faster than MSMF on most
    # Windows webcams and honours MJPG/resolution requests reliably.
    return cv2.CAP_DSHOW


class CameraSource:
    is_live = True

    def __init__(self, index: int, width: int = 640, height: int = 480, fps: int = 30, backend: str = "auto"):
        self.index = index
        self.width, self.height, self.fps = width, height, fps
        self.backend = backend
        self.name = f"Camera {index}"
        self._cap: cv2.VideoCapture | None = None

    def open(self) -> bool:
        self.release()
        cap = cv2.VideoCapture(self.index, _backend_flag(self.backend))
        if not cap.isOpened() and self.backend == "auto" and sys.platform == "win32":
            cap.release()
            cap = cv2.VideoCapture(self.index, cv2.CAP_MSMF)
        if not cap.isOpened():
            cap.release()
            return False
        # MJPG lets USB webcams deliver 30 FPS at 640x480+ instead of ~10 with raw YUY2.
        cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        cap.set(cv2.CAP_PROP_FPS, self.fps)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # minimise queued (stale) frames
        self._cap = cap
        w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.name = f"Camera {self.index} ({w}x{h})"
        return True

    def read(self) -> np.ndarray | None:
        if self._cap is None:
            return None
        ok, frame = self._cap.read()
        return frame if ok and frame is not None and frame.size else None

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None


class VideoFileSource:
    """Plays a video file in (approximately) real time, looping."""

    is_live = False

    def __init__(self, path: str | Path, loop: bool = True):
        self.path = Path(path)
        self.loop = loop
        self.name = f"Video: {self.path.name}"
        self._cap: cv2.VideoCapture | None = None
        self._interval = 1 / 30
        self._next = 0.0

    def open(self) -> bool:
        self._cap = cv2.VideoCapture(str(self.path))
        if not self._cap.isOpened():
            return False
        fps = self._cap.get(cv2.CAP_PROP_FPS) or 30
        self._interval = 1.0 / max(1.0, min(fps, 60.0))
        self._next = time.monotonic()
        return True

    def read(self) -> np.ndarray | None:
        if self._cap is None:
            return None
        _pace(self)
        ok, frame = self._cap.read()
        if not ok and self.loop:
            self._cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, frame = self._cap.read()
        return frame if ok else None

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None


class ImageSource:
    """Cycles through still images (each shown for `hold_frames` frames)."""

    is_live = False

    def __init__(self, paths: list[Path], fps: float = 15.0, hold_frames: int = 15):
        self.paths = paths
        self.name = f"Images ({len(paths)})"
        self._interval = 1.0 / fps
        self._next = 0.0
        self.hold_frames = hold_frames
        self._frames: list[np.ndarray] = []
        self._i = 0

    def open(self) -> bool:
        self._frames = [f for f in (cv2.imread(str(p)) for p in self.paths) if f is not None]
        self._next = time.monotonic()
        return bool(self._frames)

    def read(self) -> np.ndarray | None:
        if not self._frames:
            return None
        _pace(self)
        frame = self._frames[(self._i // self.hold_frames) % len(self._frames)]
        self._i += 1
        return frame.copy()

    def release(self) -> None:
        self._frames = []


def _pace(src) -> None:
    now = time.monotonic()
    if src._next > now:
        time.sleep(src._next - now)
    src._next = max(src._next + src._interval, time.monotonic() - src._interval)


def make_source(spec: str | int | None, camera_settings) -> FrameSource:
    """Build a source from a CLI spec: None/int -> camera, path -> file(s)."""
    if spec is None or (isinstance(spec, str) and spec.isdigit()) or isinstance(spec, int):
        index = camera_settings.index if spec is None else int(spec)
        return CameraSource(index, camera_settings.width, camera_settings.height,
                            camera_settings.fps, camera_settings.backend)
    path = Path(spec)
    if path.is_dir():
        images = sorted(p for p in path.iterdir() if p.suffix.lower() in IMAGE_EXTS)
        return ImageSource(images)
    if path.suffix.lower() in IMAGE_EXTS:
        return ImageSource([path])
    return VideoFileSource(path)


@dataclass(slots=True)
class CameraInfo:
    index: int
    label: str


def enumerate_cameras(max_index: int = 5, backend: str = "auto") -> list[CameraInfo]:
    """Probe camera indices. Opens each device briefly; call off the GUI thread."""
    found: list[CameraInfo] = []
    for i in range(max_index):
        cap = cv2.VideoCapture(i, _backend_flag(backend))
        try:
            if cap.isOpened():
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                found.append(CameraInfo(i, f"Camera {i} ({w}x{h})"))
        finally:
            cap.release()
    return found
