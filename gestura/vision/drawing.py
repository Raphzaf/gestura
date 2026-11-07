"""Annotate preview frames with landmarks and tracking feedback (OpenCV)."""

from __future__ import annotations

from dataclasses import dataclass

import cv2
import numpy as np

from ..core.types import TrackingFrame
from .face_tracker import FACE_CONTOURS, NOSE_TIP
from .hand_tracker import HAND_CONNECTIONS

# BGR colours matching the UI theme
ACCENT = (255, 196, 64)  # cyan-ish
ACCENT_2 = (140, 230, 120)  # green
WARN = (60, 170, 255)  # orange
MUTED = (150, 150, 150)
WHITE = (245, 245, 245)
FINGERTIPS = (4, 8, 12, 16, 20)


@dataclass(slots=True)
class Overlay:
    show_hands: bool = True
    show_face: bool = True
    show_axes: bool = True
    show_region: bool = True
    region: tuple[float, float, float, float] | None = None  # l, t, r, b normalized
    control_hand: int | None = None  # index into tf.hands that drives the cursor
    click_hand: int | None = None  # two-hand mouse: index of the hand that clicks
    cursor: tuple[float, float] | None = None  # normalized smoothed cursor (frame space)
    pinch_active: bool = False
    banner: str = ""


def annotate(frame: np.ndarray, tf: TrackingFrame, ov: Overlay) -> np.ndarray:
    out = frame.copy()
    h, w = out.shape[:2]
    thick = max(1, round(w / 640))

    if ov.show_region and ov.region:
        l, t, r, b = ov.region
        cv2.rectangle(out, (int(l * w), int(t * h)), (int(r * w), int(b * h)), MUTED, 1, cv2.LINE_AA)

    if ov.show_face and tf.face is not None:
        pts = (tf.face.landmarks[:, :2] * (w, h)).astype(np.int32)
        for a, b in FACE_CONTOURS:
            cv2.line(out, tuple(pts[a]), tuple(pts[b]), (200, 200, 200), 1, cv2.LINE_AA)
        if ov.show_axes and tf.face.pose is not None:
            _draw_head_axes(out, pts[NOSE_TIP], tf.face.pose.yaw, tf.face.pose.pitch, w)

    if ov.show_hands:
        for i, hand in enumerate(tf.hands):
            pts = (hand.landmarks[:, :2] * (w, h)).astype(np.int32)
            primary = i == ov.control_hand
            clicker = i == ov.click_hand and not primary
            colour = ACCENT if primary else ACCENT_2 if clicker else MUTED
            for a, b in HAND_CONNECTIONS:
                cv2.line(out, tuple(pts[a]), tuple(pts[b]), colour, 2 * thick, cv2.LINE_AA)
            for j, p in enumerate(pts):
                r = 4 * thick if j in FINGERTIPS else 3 * thick
                cv2.circle(out, tuple(p), r, WHITE, -1, cv2.LINE_AA)
                cv2.circle(out, tuple(p), r, colour, 1, cv2.LINE_AA)
            role = " · moves" if primary and ov.click_hand is not None else " · clicks" if clicker else ""
            _tag(out, f"{hand.handedness} {hand.score:.0%}{role}", pts[0], colour, thick)
            if clicker or (primary and ov.click_hand is None):
                p4, p8 = tuple(pts[4]), tuple(pts[8])
                cv2.line(out, p4, p8, ACCENT_2 if ov.pinch_active else WARN, thick, cv2.LINE_AA)

    if ov.cursor is not None:
        cx, cy = int(ov.cursor[0] * w), int(ov.cursor[1] * h)
        cv2.circle(out, (cx, cy), 9 * thick, ACCENT_2 if ov.pinch_active else ACCENT, 2, cv2.LINE_AA)
        cv2.circle(out, (cx, cy), 2 * thick, ACCENT_2, -1, cv2.LINE_AA)

    if ov.banner:
        (tw, th), _ = cv2.getTextSize(ov.banner, cv2.FONT_HERSHEY_SIMPLEX, 0.8 * thick, 2 * thick)
        x0 = (w - tw) // 2
        cv2.rectangle(out, (x0 - 14, 12), (x0 + tw + 14, 12 + th + 20), (40, 30, 20), -1)
        cv2.putText(out, ov.banner, (x0, 12 + th + 10), cv2.FONT_HERSHEY_SIMPLEX,
                    0.8 * thick, ACCENT_2, 2 * thick, cv2.LINE_AA)
    return out


def _tag(img: np.ndarray, text: str, anchor: np.ndarray, colour, thick: int) -> None:
    """Small label with a dark backing box, placed below `anchor`."""
    font, scale = cv2.FONT_HERSHEY_SIMPLEX, 0.45 * thick
    (tw, th), base = cv2.getTextSize(text, font, scale, thick)
    h, w = img.shape[:2]
    x = int(min(max(4, anchor[0] - tw // 2), w - tw - 8))
    y = int(min(anchor[1] + 14 + th, h - 6))
    cv2.rectangle(img, (x - 5, y - th - 5), (x + tw + 5, y + base + 2), (24, 20, 16), -1)
    cv2.putText(img, text, (x, y), font, scale, colour, thick, cv2.LINE_AA)


def _draw_head_axes(img: np.ndarray, nose: np.ndarray, yaw: float, pitch: float, w: int) -> None:
    """Project the facing direction as an arrow from the nose tip."""
    length = w * 0.12
    dx = np.sin(np.radians(yaw)) * length
    dy = np.sin(np.radians(pitch)) * length
    tip = (int(nose[0] + dx), int(nose[1] + dy))
    cv2.arrowedLine(img, tuple(int(v) for v in nose), tip, ACCENT_2, 2, cv2.LINE_AA, tipLength=0.25)
