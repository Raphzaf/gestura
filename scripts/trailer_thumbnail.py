# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura. Gestura is free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Render the 16:9 trailer thumbnail for the Microsoft Store listing.

    python scripts/trailer_thumbnail.py   # writes store/listing/art/trailer_thumbnail_*.png

Two languages (fr, en) at 1920 x 1080 and 3840 x 2160. Drawn in vector at a
1920 x 1080 design size and scaled, so both sizes are pixel-sharp. The face mesh
and the hand are real MediaPipe landmarks from the test fixtures (no photo).
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
OUT = ROOT / "store" / "listing" / "art"
W, H = 1920, 1080
SIZES = ((1920, 1080), (3840, 2160))
BG_TOP, BG_BOTTOM = "#1b2230", "#0e1014"
TEXT, MUTED, ACCENT, GREEN = "#e7e9ef", "#8a93a6", "#40c4ff", "#5fd38d"

COPY = {
    "fr": {
        "tagline": ["Contrôlez votre PC", "avec les mains, les yeux et la tête"],
        "pills": ["Mains", "Yeux", "Tête", "100 % local"],
    },
    "en": {
        "tagline": ["Control your PC", "with your hands, eyes and head"],
        "pills": ["Hands", "Eyes", "Head", "100% local"],
    },
}


def main() -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    import numpy as np
    from PySide6.QtCore import QPointF, QRectF, Qt
    from PySide6.QtGui import (QBrush, QColor, QFont, QImage, QLinearGradient, QPainter, QPainterPath, QPen,
                               QRadialGradient)
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtWidgets import QApplication

    from gestura.gestures.face_features import EYE_A, EYE_B, IRIS_A, IRIS_B
    from gestura.vision.face_tracker import FACE_CONTOURS
    from gestura.vision.hand_tracker import HAND_CONNECTIONS

    _app = QApplication.instance() or QApplication([])  # noqa: F841 - needed by QPainter
    svg = QSvgRenderer(str(ROOT / "gestura" / "assets" / "icon.svg"))
    face = json.loads((ROOT / "tests" / "data" / "face_landmarks.json").read_text())["business-person"]
    hands = json.loads((ROOT / "tests" / "data" / "real_landmarks.json").read_text())
    hand = np.array(hands["pointing_up"]["hands"][0]["landmarks"])[:, :2]

    # Face mesh in pixel space, normalized to its own bounding box.
    fl = np.array(face["landmarks"])[:, :2] * (face["width"], face["height"])
    fl -= fl.min(axis=0)
    fl /= fl.max(axis=0)[1]  # height = 1
    hl = hand - hand.min(axis=0)
    hl /= hl.max(axis=0)[1]

    def pt(a: np.ndarray, x0: float, y0: float, s: float) -> QPointF:
        return QPointF(x0 + a[0] * s, y0 + a[1] * s)

    def draw(lang: str, p: QPainter) -> None:
        p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        g = QLinearGradient(QPointF(0, 0), QPointF(W, H))
        g.setColorAt(0, QColor(BG_TOP))
        g.setColorAt(1, QColor(BG_BOTTOM))
        p.fillRect(QRectF(0, 0, W, H), g)
        glow = QRadialGradient(QPointF(1390, 520), 620)
        glow.setColorAt(0, QColor(64, 196, 255, 70))
        glow.setColorAt(1, QColor(64, 196, 255, 0))
        p.fillRect(QRectF(0, 0, W, H), QBrush(glow))

        # ---- right: face mesh with tracked eyes
        fx, fy, fs = 1000, 110, 720
        p.setPen(QPen(QColor(138, 147, 166, 150), 2.2))
        for a, b in FACE_CONTOURS:
            p.drawLine(pt(fl[a], fx, fy, fs), pt(fl[b], fx, fy, fs))
        for eye in (EYE_A, EYE_B):
            c1, u1, u2, c2, l2, l1 = eye
            path = QPainterPath(pt(fl[c1], fx, fy, fs))
            for i in (u1, u2, c2, l2, l1, c1):
                path.lineTo(pt(fl[i], fx, fy, fs))
            p.setPen(QPen(QColor(GREEN), 5))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawPath(path)
        for iris in (IRIS_A, IRIS_B):
            c = pt(fl[iris], fx, fy, fs)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(ACCENT))
            p.drawEllipse(c, 9, 9)
            p.setPen(QPen(QColor(ACCENT), 2.5))
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawEllipse(c, 26, 26)

        # gaze beam from the eyes to a pointer
        eyes_mid = (pt(fl[IRIS_A], fx, fy, fs) + pt(fl[IRIS_B], fx, fy, fs)) / 2
        target = QPointF(860, 300)
        beam = QLinearGradient(eyes_mid, target)
        beam.setColorAt(0, QColor(64, 196, 255, 160))
        beam.setColorAt(1, QColor(64, 196, 255, 20))
        pen = QPen(QBrush(beam), 4, Qt.PenStyle.DashLine)
        p.setPen(pen)
        p.drawLine(eyes_mid, target)
        arrow = QPainterPath(target)
        for dx, dy in ((0, 64), (17, 49), (29, 75), (40, 70), (28, 45), (50, 45)):
            arrow.lineTo(target + QPointF(dx, dy))
        arrow.closeSubpath()
        p.setPen(QPen(QColor(BG_BOTTOM), 3))
        p.setBrush(QColor("#ffffff"))
        p.drawPath(arrow)
        ring = QPen(QColor(GREEN), 7)
        ring.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(ring)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawArc(QRectF(target.x() + 38, target.y() + 58, 54, 54), 90 * 16, -270 * 16)

        # ---- right: pointing hand
        hx, hy, hs = 1585, 520, 500
        hp = QPen(QColor(ACCENT), 9)
        hp.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(hp)
        for a, b in HAND_CONNECTIONS:
            p.drawLine(pt(hl[a], hx, hy, hs), pt(hl[b], hx, hy, hs))
        for i in range(21):
            c = pt(hl[i], hx, hy, hs)
            r = 13 if i in (4, 8, 12, 16, 20) else 10
            p.setPen(QPen(QColor(ACCENT), 3))
            p.setBrush(QColor("#ffffff"))
            p.drawEllipse(c, r, r)

        # ---- left: brand, tagline, pills
        svg.render(p, QRectF(120, 170, 200, 200))
        title = QFont()
        title.setPixelSize(170)
        title.setBold(True)
        p.setFont(title)
        p.setPen(QColor(TEXT))
        p.drawText(QRectF(110, 390, 900, 210), int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter),
                   "Gestura")
        tag = QFont()
        tag.setPixelSize(58)
        tag.setBold(True)
        p.setFont(tag)
        lines = COPY[lang]["tagline"]
        p.setPen(QColor(TEXT))
        p.drawText(QRectF(120, 610, 900, 80), int(Qt.AlignmentFlag.AlignLeft), lines[0])
        p.setPen(QColor(MUTED))
        sub = QFont(tag)
        sub.setBold(False)
        sub.setPixelSize(46)
        p.setFont(sub)
        p.drawText(QRectF(120, 690, 900, 70), int(Qt.AlignmentFlag.AlignLeft), lines[1])
        pill = QFont()
        pill.setPixelSize(36)
        pill.setBold(True)
        p.setFont(pill)
        x = 120.0
        for i, word in enumerate(COPY[lang]["pills"]):
            wpx = p.fontMetrics().horizontalAdvance(word) + 56
            r = QRectF(x, 820, wpx, 70)
            colour = QColor(GREEN if i == len(COPY[lang]["pills"]) - 1 else ACCENT)
            fill = QColor(colour)
            fill.setAlpha(40)
            p.setPen(QPen(colour, 2.5))
            p.setBrush(fill)
            p.drawRoundedRect(r, 35, 35)
            p.setPen(QColor(TEXT))
            p.drawText(r, int(Qt.AlignmentFlag.AlignCenter), word)
            x += wpx + 18

    OUT.mkdir(parents=True, exist_ok=True)
    for lang in COPY:
        for w, h in SIZES:
            img = QImage(w, h, QImage.Format.Format_RGB32)
            p = QPainter(img)
            p.scale(w / W, h / H)
            draw(lang, p)
            p.end()
            path = OUT / f"trailer_thumbnail_{lang}_{w}x{h}.png"
            img.save(str(path), "PNG")
            print(f"{path.relative_to(ROOT)}  ({path.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
