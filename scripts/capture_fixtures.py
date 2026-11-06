"""Run the real models on photos and save landmark outputs as test fixtures.

The photos themselves are NOT stored in the repository; only MediaPipe's
landmark output is. Usage:
    python scripts/capture_fixtures.py <image_dir> tests/data/real_landmarks.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import cv2

from gestura.config.settings import Settings
from gestura.vision.frame_processor import FrameProcessor


def main(src: str, out: str) -> None:
    s = Settings()
    proc = FrameProcessor(s.tracking, s.camera)
    data: dict[str, dict] = {}
    try:
        for path in sorted(Path(src).iterdir()):
            img = cv2.imread(str(path))
            if img is None:
                continue
            for _ in range(4):  # VIDEO mode: let the tracker settle on a still image
                _, tf = proc.process(img)
            data[path.stem] = {
                "hands": [{"handedness": h.handedness, "score": h.score,
                           "landmarks": h.landmarks.round(5).tolist(),
                           "world": h.world.round(5).tolist()} for h in tf.hands],
                "face_matrix": tf.face.matrix.round(6).tolist() if tf.face and tf.face.matrix is not None else None,
            }
            print(path.name, len(tf.hands), "hands", "face" if tf.face else "no face")
    finally:
        proc.close()
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    Path(out).write_text(json.dumps(data, indent=1))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
