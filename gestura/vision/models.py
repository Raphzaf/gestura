"""Locations of the bundled MediaPipe model files."""

from __future__ import annotations

import sys
from pathlib import Path

HAND_MODEL = "hand_landmarker.task"
FACE_MODEL = "face_landmarker.task"

# SHA-256 of the bundled float16 models (downloaded 2026-11-06 from
# storage.googleapis.com/mediapipe-models/.../float16/latest/).
MODEL_SHA256 = {
    HAND_MODEL: "fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1",
    FACE_MODEL: "64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff",
}

MODEL_URLS = {
    HAND_MODEL: "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/latest/hand_landmarker.task",
    FACE_MODEL: "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/latest/face_landmarker.task",
}


def assets_dir() -> Path:
    base = getattr(sys, "_MEIPASS", None)  # PyInstaller one-file / one-dir bundle
    if base:
        return Path(base) / "gestura" / "assets"
    return Path(__file__).resolve().parent.parent / "assets"


def model_path(name: str) -> Path:
    path = assets_dir() / "models" / name
    if not path.is_file():
        raise FileNotFoundError(
            f"MediaPipe model {name!r} not found at {path}. "
            "Run `python scripts/download_models.py` to fetch it."
        )
    return path
