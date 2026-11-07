"""Measure Gestura's hand tracking under degraded webcam conditions.

Uses the real FrameProcessor (MediaPipe models, VIDEO mode) on sample photos with
synthetic degradations. Each condition runs N frames with fresh noise, as a webcam would.
Usage: python robustness.py <image_dir> <out.json>
"""
import json
import sys
import time
from pathlib import Path

import cv2
import numpy as np

from gestura.config.settings import Settings
from gestura.gestures.hand_features import compute
from gestura.vision.frame_processor import FrameProcessor

RNG = np.random.default_rng(0)
N = 20  # frames per image and condition


def low_light(img, f, gain):
    """Scene light scaled by f. Sensor noise grows when the camera's auto-gain brightens it back."""
    x = img.astype(np.float32) * f
    x += RNG.normal(0, 2.5, x.shape)  # read noise
    x += RNG.normal(0, 1.0, x.shape) * np.sqrt(np.clip(x, 0, None))  # shot noise
    if gain:
        x /= f  # auto-exposure/gain restores brightness and amplifies noise
    return np.clip(x, 0, 255).astype(np.uint8)


def blur(img, s):
    return cv2.GaussianBlur(img, (0, 0), s)


def low_res(img, w, q):
    h0, w0 = img.shape[:2]
    small = cv2.resize(img, (w, int(h0 * w / w0)), interpolation=cv2.INTER_AREA)
    ok, enc = cv2.imencode(".jpg", small, [cv2.IMWRITE_JPEG_QUALITY, q])
    small = cv2.imdecode(enc, cv2.IMREAD_COLOR)
    return cv2.resize(small, (w0, h0), interpolation=cv2.INTER_LINEAR)


def distance(img, k):
    """Subject k times smaller in the frame (farther from the camera)."""
    h, w = img.shape[:2]
    canvas = np.full_like(img, int(img.mean()))
    small = cv2.resize(img, (int(w * k), int(h * k)), interpolation=cv2.INTER_AREA)
    y, x = (h - small.shape[0]) // 2, (w - small.shape[1]) // 2
    canvas[y:y + small.shape[0], x:x + small.shape[1]] = small
    return canvas, (x, y, k)


def to_640(img):
    h, w = img.shape[:2]
    s = 640 / max(h, w)
    return cv2.resize(img, (int(w * s), int(h * s)), interpolation=cv2.INTER_AREA)


CONDITIONS = {
    "reference": lambda im: (im, None),
    "lumiere_50pct_gain": lambda im: (low_light(im, 0.5, True), None),
    "lumiere_20pct_gain": lambda im: (low_light(im, 0.2, True), None),
    "lumiere_10pct_gain": lambda im: (low_light(im, 0.1, True), None),
    "lumiere_5pct_gain": lambda im: (low_light(im, 0.05, True), None),
    "lumiere_20pct_sans_gain": lambda im: (low_light(im, 0.2, False), None),
    "lumiere_10pct_sans_gain": lambda im: (low_light(im, 0.1, False), None),
    "flou_leger_s1.5": lambda im: (blur(im, 1.5), None),
    "flou_fort_s4": lambda im: (blur(im, 4.0), None),
    "webcam_320px_jpeg40": lambda im: (low_res(im, 320, 40), None),
    "webcam_160px_jpeg25": lambda im: (low_res(im, 160, 25), None),
    "distance_x0.5": lambda im: distance(im, 0.5),
    "distance_x0.33": lambda im: distance(im, 0.33),
    "distance_x0.25": lambda im: distance(im, 0.25),
}


def run(src: Path, out: Path) -> None:
    s = Settings()
    s.tracking.face_enabled = False
    s.camera.mirror = False
    images = [to_640(cv2.imread(str(p))) for p in sorted(src.iterdir()) if cv2.imread(str(p)) is not None]
    results = {}
    for name, fn in CONDITIONS.items():
        det, frames, errs, jit, pose_ok, pose_n, hand_px = 0, 0, [], [], 0, 0, []
        for img in images:
            proc = FrameProcessor(s.tracking, s.camera)  # fresh tracker per image
            try:
                # baseline on the clean image
                for _ in range(4):
                    _, ref = proc.process(img)
                if not ref.hands:
                    continue
                proc.close()
                proc = FrameProcessor(s.tracking, s.camera)
                h, w = img.shape[:2]
                ref_pts = [hd.landmarks[:, :2] * (w, h) for hd in ref.hands]
                ref_pose = [compute(hd).pose for hd in ref.hands]
                tips = []
                for _ in range(N):
                    deg, geo = fn(img)
                    _, tf = proc.process(deg)
                    frames += len(ref.hands)
                    for rp, rpose in zip(ref_pts, ref_pose):
                        size = np.linalg.norm(rp.max(0) - rp.min(0))
                        if geo:  # map reference into the shrunken frame
                            x0, y0, k = geo
                            rp = rp * k + (x0, y0)
                            size *= k
                        # match the detection closest to this reference hand
                        best = None
                        for hd in tf.hands:
                            p = hd.landmarks[:, :2] * (w, h)
                            e = np.linalg.norm(p - rp, axis=1).mean()
                            if best is None or e < best[0]:
                                best = (e, hd, p)
                        if best and best[0] < 0.5 * size:
                            det += 1
                            errs.append(best[0] / size)
                            pose_n += 1
                            pose_ok += compute(best[1]).pose == rpose
                            hand_px.append(size)
                            if rp is ref_pts[0] or len(ref_pts) == 1:
                                tips.append(best[2][8])
                if len(tips) >= 5:
                    t = np.array(tips)
                    jit.append(float(np.linalg.norm(t - t.mean(0), axis=1).mean()))
            finally:
                proc.close()
        results[name] = {
            "detection_rate": round(det / max(1, frames), 3),
            "landmark_error_pct_of_hand": round(100 * float(np.mean(errs)), 1) if errs else None,
            "index_tip_jitter_px_640": round(float(np.mean(jit)), 2) if jit else None,
            "pose_agreement": round(pose_ok / max(1, pose_n), 3) if pose_n else None,
            "hand_size_px_640": round(float(np.mean(hand_px)), 0) if hand_px else None,
            "frames": frames,
        }
        print(name, results[name], flush=True)
    out.write_text(json.dumps(results, indent=1))


if __name__ == "__main__":
    t = time.time()
    run(Path(sys.argv[1]), Path(sys.argv[2]))
    print("done in", round(time.time() - t), "s")
