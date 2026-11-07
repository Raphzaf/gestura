# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Gestura launch film: shared drawing core (design grid 1920x1080, rendered at SCALE x)."""

from __future__ import annotations

import json
import math
import os
from functools import lru_cache

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QFont, QFontMetricsF, QImage, QLinearGradient, QPainter, QPainterPath,
                           QPen, QPolygonF, QRadialGradient)

W, H = 1920, 1080
FPS = 24
DUR = 50.0
VDIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CUES = json.load(open(os.path.join(VDIR, "work", "cues.json")))

# ----------------------------------------------------------------- palette
BG = QColor("#0A0B0F")
BG2 = QColor("#12141B")
PANEL = QColor("#14161E")
PANEL2 = QColor("#1B1E28")
LINE = QColor("#262A36")
TEXT = QColor("#F4F5F8")
MUTED = QColor("#8C93A5")
BLUE = QColor("#3D8BFF")
BLUE_L = QColor("#7DB4FF")
VIOLET = QColor("#8B5CF6")
VIOLET_L = QColor("#B79CFF")
GREEN = QColor("#4ADE9B")
AMBER = QColor("#FFB454")


def rgba(c: QColor, a: float) -> QColor:
    q = QColor(c)
    q.setAlphaF(max(0.0, min(1.0, a)))
    return q


def cue(cid: str) -> float:
    return CUES[cid]["start"]


def cue_end(cid: str) -> float:
    return CUES[cid]["end"]


# ------------------------------------------------------------------ easing
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def seg(t, a, b):
    """Progress 0..1 of t across [a, b]."""
    if b <= a:
        return 1.0 if t >= b else 0.0
    return clamp((t - a) / (b - a))


def ease_out(x):
    return 1 - (1 - x) ** 3


def ease_in_out(x):
    return 4 * x ** 3 if x < 0.5 else 1 - (-2 * x + 2) ** 3 / 2


def ease_out_back(x, s=1.4):
    x -= 1
    return 1 + (s + 1) * x ** 3 + s * x ** 2


def lerp(a, b, x):
    return a + (b - a) * x


def lerp_pt(p, q, x):
    return (lerp(p[0], q[0], x), lerp(p[1], q[1], x))


def window(t, a, b, fade=0.35):
    """1 inside [a,b] with fades at both ends."""
    return ease_out(seg(t, a, a + fade)) * (1 - ease_in_out(seg(t, b - fade, b)))


# ------------------------------------------------------------------- fonts
@lru_cache(maxsize=None)
def font(size: float, weight: int = 500, display: bool = False, spacing: float = 0.0) -> QFont:
    f = QFont("Inter Display" if display else "Inter")
    f.setPixelSize(max(1, int(round(size))))
    f.setWeight(QFont.Weight(weight))
    f.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    if spacing:
        f.setLetterSpacing(QFont.SpacingType.PercentageSpacing, 100 + spacing)
    return f


def text(p: QPainter, s: str, x, y, size=24, weight=500, color=TEXT, align="left", display=False,
         alpha=1.0, spacing=0.0, rise=0.0):
    """Draw text with baseline-independent vertical centring at y. `rise` offsets for entrances."""
    f = font(size, weight, display, spacing)
    p.setFont(f)
    fm = QFontMetricsF(f)
    w = fm.horizontalAdvance(s)
    if align == "center":
        x -= w / 2
    elif align == "right":
        x -= w
    p.setPen(rgba(color, color.alphaF() * alpha))
    p.drawText(QPointF(x, y + (fm.ascent() - fm.descent()) / 2 + rise), s)
    return w


def text_width(s, size, weight=500, display=False, spacing=0.0):
    return QFontMetricsF(font(size, weight, display, spacing)).horizontalAdvance(s)


def headline(p, s, x, y, t, t0, size=64, align="center", color=TEXT, out_t=None, weight=600):
    """Word-by-word rise-in headline."""
    if t < t0:
        return
    words = s.split(" ")
    gap = text_width(" ", size, weight, True)
    widths = [text_width(w_, size, weight, True) for w_ in words]
    total = sum(widths) + gap * (len(words) - 1)
    cx = x - total / 2 if align == "center" else x
    fade_out = 1.0 if out_t is None else 1 - ease_in_out(seg(t, out_t, out_t + 0.4))
    for i, (w_, ww) in enumerate(zip(words, widths)):
        k = ease_out(seg(t, t0 + i * 0.09, t0 + i * 0.09 + 0.55))
        if k > 0:
            text(p, w_, cx, y, size, weight, color, display=True, alpha=k * fade_out, rise=(1 - k) * 18)
        cx += ww + gap


# -------------------------------------------------------------- primitives
def rrect(p, r: QRectF, radius, fill=None, pen=None, pen_w=1.0):
    p.setPen(Qt.PenStyle.NoPen if pen is None else QPen(pen, pen_w))
    p.setBrush(Qt.BrushStyle.NoBrush if fill is None else (fill if isinstance(fill, QBrush) else QBrush(fill)))
    p.drawRoundedRect(r, radius, radius)


def glow_dot(p, x, y, r, color, strength=1.0):
    g = QRadialGradient(QPointF(x, y), r)
    g.setColorAt(0.0, rgba(color, 0.55 * strength))
    g.setColorAt(0.35, rgba(color, 0.22 * strength))
    g.setColorAt(1.0, rgba(color, 0.0))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(g))
    p.drawEllipse(QPointF(x, y), r, r)


def chip(p, x, y, label, color=BLUE, alpha=1.0, size=17, dot=True, align="left", fill=None):
    pad = 14
    w = text_width(label, size, 600) + pad * 2 + (18 if dot else 0)
    h = size + 18
    if align == "center":
        x -= w / 2
    r = QRectF(x, y - h / 2, w, h)
    rrect(p, r, h / 2, fill=rgba(fill or PANEL2, 0.92 * alpha), pen=rgba(color, 0.55 * alpha), pen_w=1.2)
    tx = x + pad
    if dot:
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(rgba(color, alpha))
        p.drawEllipse(QPointF(tx + 4, y), 4.5, 4.5)
        tx += 18
    text(p, label, tx, y, size, 600, TEXT, alpha=alpha)
    return r


def cursor_arrow(p, x, y, scale=1.0, alpha=1.0, pressed=0.0):
    s = scale * (1 - 0.12 * pressed)
    pts = [(0, 0), (0, 26), (6.5, 20), (11, 30), (15, 28.5), (10.7, 18.8), (19, 18.8)]
    poly = QPolygonF([QPointF(x + px * s, y + py * s) for px, py in pts])
    p.setPen(QPen(rgba(QColor("#0A0B0F"), alpha), 1.6 * s))
    p.setBrush(rgba(QColor("#FFFFFF"), alpha))
    p.drawPolygon(poly)


def ripple(p, x, y, k, color=VIOLET):
    """Click ripple, k = 0..1."""
    if k <= 0 or k >= 1:
        return
    r = 8 + 46 * ease_out(k)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(rgba(color, 0.9 * (1 - k)), 3 * (1 - k) + 1))
    p.drawEllipse(QPointF(x, y), r, r)
    glow_dot(p, x, y, 26, color, 1 - k)


def brand_gradient(x0, y0, x1, y1) -> QLinearGradient:
    g = QLinearGradient(QPointF(x0, y0), QPointF(x1, y1))
    g.setColorAt(0, BLUE)
    g.setColorAt(1, VIOLET)
    return g


# ------------------------------------------------------------------- logo
def logo_mark(p, cx, cy, size, t_rel=10.0):
    """Gestura mark: tracking arc + index-finger landmark chain. t_rel animates the build (0..1.4 s)."""
    s = size / 256.0
    def P(x, y):
        return QPointF(cx + (x - 128) * s, cy + (y - 128) * s)
    a = ease_in_out(seg(t_rel, 0.0, 0.8))
    if a > 0:
        path = QPainterPath()
        r = 80 * s
        rect = QRectF(cx + (128 - 128) * s - r, cy + (170 - 128) * s - r, 2 * r, 2 * r)
        # arc from (60,170) sweeping to (196,86) around centre (128,170)
        path.arcMoveTo(rect, 180)
        path.arcTo(rect, 180, -122 * a)
        pen = QPen(QBrush(brand_gradient(cx - 80 * s, cy + 40 * s, cx + 70 * s, cy - 40 * s)), 14 * s)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawPath(path)
    joints = [(104, 196), (120, 150), (140, 112), (156, 82)]
    branch = (156, 154)
    b = ease_out(seg(t_rel, 0.35, 1.1))
    if b > 0:
        pen = QPen(rgba(TEXT, b), 10 * s)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        n = b * 3
        for i in range(3):
            k = clamp(n - i)
            if k > 0:
                a0, a1 = joints[i], joints[i + 1]
                p.drawLine(P(*a0), P(*lerp_pt(a0, a1, k)))
        if b > 0.5:
            k = seg(b, 0.5, 1.0)
            p.drawLine(P(*joints[1]), P(*lerp_pt(joints[1], branch, k)))
        p.setPen(Qt.PenStyle.NoPen)
        for i, j in enumerate(joints[:3] + [branch]):
            k = ease_out_back(seg(t_rel, 0.4 + i * 0.12, 0.75 + i * 0.12))
            if k > 0:
                p.setBrush(rgba(QColor("#FFFFFF"), clamp(k)))
                p.drawEllipse(P(*j), 11 * s * k, 11 * s * k)
    k = ease_out_back(seg(t_rel, 0.85, 1.3))
    if k > 0:
        tip = P(*joints[3])
        glow_dot(p, tip.x(), tip.y(), 40 * s * k, VIOLET, 0.9)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(brand_gradient(tip.x() - 17 * s, tip.y() + 17 * s, tip.x() + 17 * s, tip.y() - 17 * s)))
        p.drawEllipse(tip, 17 * s * k, 17 * s * k)


def wordmark(p, x, y, size, t_rel=10.0, align="center", alpha=1.0):
    s = "GESTURA"
    spacing = 32
    total = text_width(s, size, 700, True, spacing)
    cx = x - total / 2 if align == "center" else x
    for i, ch in enumerate(s):
        k = ease_out(seg(t_rel, i * 0.05, i * 0.05 + 0.6))
        w = text_width(ch, size, 700, True, spacing)
        if k > 0:
            text(p, ch, cx, y, size, 700, TEXT, display=True, alpha=k * alpha, spacing=spacing, rise=(1 - k) * 10)
        cx += w


# -------------------------------------------------------------- hand model
# Same articulated topology as Gestura's test hand (MediaPipe 21-landmark order).
MCP = {"index": (-0.025, 0.085), "middle": (0.0, 0.090), "ring": (0.020, 0.085), "pinky": (0.038, 0.075)}
SEGS = {"index": (0.040, 0.025, 0.021), "middle": (0.045, 0.028, 0.022), "ring": (0.042, 0.026, 0.021),
        "pinky": (0.032, 0.020, 0.018)}
BASE = {"index": 5, "middle": 9, "ring": 13, "pinky": 17}
WIDTH = {"index": 0.0185, "middle": 0.019, "ring": 0.0178, "pinky": 0.0155, "thumb": 0.021}
FINGERS = ("index", "middle", "ring", "pinky")
CURL = (72.0, 98.0, 68.0)
STRAIGHT = (0.0, 0.0, 0.0)
POSES = {
    "open": {"curl": {f: (4.0, 6.0, 4.0) for f in FINGERS}, "thumb": "out", "spread": 1.0},
    "relax": {"curl": {"index": (14, 22, 14), "middle": (18, 28, 18), "ring": (22, 30, 20), "pinky": (26, 34, 22)},
              "thumb": "relax", "spread": 0.35},
    "point": {"curl": {"index": STRAIGHT, "middle": CURL, "ring": CURL, "pinky": CURL}, "thumb": "tuck", "spread": 0.2},
    "pinch": {"curl": {"index": (28, 38, 22), "middle": CURL, "ring": CURL, "pinky": CURL}, "thumb": "pinch",
              "spread": 0.2},
    "two": {"curl": {"index": STRAIGHT, "middle": STRAIGHT, "ring": CURL, "pinky": CURL}, "thumb": "tuck_ring",
            "spread": 0.45},
    "fist": {"curl": {f: CURL for f in FINGERS}, "thumb": "tuck", "spread": 0.0},
    "hold": {"curl": {"index": (55, 70, 40), "middle": (60, 75, 45), "ring": (62, 78, 46), "pinky": (64, 80, 46)},
             "thumb": "grip", "spread": 0.1},
}
SPREAD_DEG = {"index": 6.0, "middle": 0.0, "ring": -5.0, "pinky": -11.0}


def _finger_chain(name, curl, spread):
    x, y = MCP[name]
    p = np.array([x, y, 0.0])
    pts = [p.copy()]
    ang = 0.0
    sp = math.radians(SPREAD_DEG[name] * spread)
    for seg_len, c in zip(SEGS[name], curl):
        ang += math.radians(c)
        # curl rotates the bone from +y toward +z (toward the camera: palm faces the viewer)
        d = np.array([-math.sin(sp) * math.cos(ang), math.cos(sp) * math.cos(ang), math.sin(ang)])
        p = p + d * seg_len
        pts.append(p.copy())
    return pts


def hand_world(pose_a: str, pose_b: str = None, k: float = 0.0) -> np.ndarray:
    """21x3 landmarks, blending pose_a -> pose_b by k."""
    A = POSES[pose_a]
    B = POSES[pose_b or pose_a]
    w = np.zeros((21, 3))
    spread = lerp(A["spread"], B["spread"], k)
    for f in FINGERS:
        curl = tuple(lerp(a, b, k) for a, b in zip(A["curl"][f], B["curl"][f]))
        for j, pt in enumerate(_finger_chain(f, curl, spread)):
            w[BASE[f] + j] = pt
    cmc = np.array([-0.022, 0.022, 0.006])

    def thumb_tip(mode):
        if mode == "out":
            return np.array([-0.078, 0.084, 0.012])
        if mode == "relax":
            return np.array([-0.070, 0.072, 0.030])
        if mode == "tuck":
            return (w[10] + w[11]) / 2 + np.array([0.0, 0.0, 0.012])
        if mode == "tuck_ring":
            return (w[14] + w[15]) / 2 + np.array([0.0, 0.0, 0.012])
        if mode == "pinch":
            return w[8] + np.array([-0.004, -0.002, 0.006])
        if mode == "grip":
            return (w[7] + w[11]) / 2 + np.array([-0.01, -0.012, 0.02])
        raise ValueError(mode)

    tip = thumb_tip(A["thumb"]) * (1 - k) + thumb_tip(B["thumb"]) * k
    out = np.array([-1.0, 0.15, 0.45])
    out /= np.linalg.norm(out)
    d = tip - cmc
    w[1] = cmc
    w[2] = cmc + d * 0.36 + out * 0.012
    w[3] = cmc + d * 0.68 + out * 0.008
    w[4] = tip
    return w


HAND_CONNECTIONS = [(0, 1), (1, 2), (2, 3), (3, 4), (0, 5), (5, 6), (6, 7), (7, 8), (5, 9), (9, 10), (10, 11),
                    (11, 12), (9, 13), (13, 14), (14, 15), (15, 16), (13, 17), (0, 17), (17, 18), (18, 19), (19, 20)]


def rot(yaw=0.0, pitch=0.0, roll=0.0):
    y, pch, r = (math.radians(v) for v in (yaw, pitch, roll))
    ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    rx = np.array([[1, 0, 0], [0, math.cos(pch), -math.sin(pch)], [0, math.sin(pch), math.cos(pch)]])
    rz = np.array([[math.cos(r), -math.sin(r), 0], [math.sin(r), math.cos(r), 0], [0, 0, 1]])
    return rz @ ry @ rx


def project_hand(world, cx, cy, scale, roll=0.0, yaw=0.0, pitch=0.0, mirror=False):
    """World (m, y up, z to camera) -> screen pts (N,2) and depth (N,)."""
    pts = world @ rot(yaw, pitch, roll).T
    if mirror:
        pts[:, 0] *= -1
    persp = 1.0 / (1.0 - pts[:, 2] * 1.6)
    sx = cx + pts[:, 0] * scale * persp
    sy = cy - pts[:, 1] * scale * persp
    return np.stack([sx, sy], 1), pts[:, 2], persp


def draw_hand_body(p, pts, depth, persp, scale, skin=QColor("#B08D78"), alpha=1.0, flour=0.0, seed=0):
    """Stylised but anatomically placed hand: forearm, palm, capsule fingers."""
    shade_dark = QColor(skin).darker(150)
    p.setPen(Qt.PenStyle.NoPen)
    wr = pts[0]
    # forearm
    fw = 0.064 * scale
    g = QLinearGradient(QPointF(wr[0] - fw, 0), QPointF(wr[0] + fw, 0))
    g.setColorAt(0, rgba(shade_dark, alpha))
    g.setColorAt(0.5, rgba(skin.darker(115), alpha))
    g.setColorAt(1, rgba(shade_dark, alpha))
    arm = QPainterPath()
    dirv = pts[0] - (pts[5] + pts[17]) / 2
    dirv = dirv / (np.linalg.norm(dirv) + 1e-6)
    perp = np.array([-dirv[1], dirv[0]])
    far = wr + dirv * 0.5 * scale
    for q in (wr + perp * fw * 0.55, far + perp * fw * 0.75, far - perp * fw * 0.75, wr - perp * fw * 0.55):
        (arm.moveTo if arm.elementCount() == 0 else arm.lineTo)(QPointF(*q))
    arm.closeSubpath()
    p.setBrush(QBrush(g))
    p.drawPath(arm)
    # sleeve cuff a little below the wrist
    cuff0 = wr + dirv * 0.075 * scale
    sl = QPainterPath()
    for q in (cuff0 + perp * fw * 0.8, far + perp * fw * 1.05, far - perp * fw * 1.05, cuff0 - perp * fw * 0.8):
        (sl.moveTo if sl.elementCount() == 0 else sl.lineTo)(QPointF(*q))
    sl.closeSubpath()
    sg = QLinearGradient(QPointF(*(cuff0 - perp * fw)), QPointF(*(cuff0 + perp * fw)))
    sg.setColorAt(0, rgba(QColor("#151821"), alpha))
    sg.setColorAt(0.5, rgba(QColor("#2A3040"), alpha))
    sg.setColorAt(1, rgba(QColor("#151821"), alpha))
    p.setBrush(QBrush(sg))
    p.drawPath(sl)
    # palm
    c = (pts[0] + pts[5] + pts[9] + pts[13] + pts[17]) / 5
    palm = [pts[0] + perp * fw * 0.5, pts[1], pts[2] * 0.6 + pts[5] * 0.4, pts[5], pts[9], pts[13], pts[17],
            pts[17] * 0.7 + pts[0] * 0.3 + (pts[17] - c) * 0.18, pts[0] - perp * fw * 0.5]
    rg = QRadialGradient(QPointF(*c), 0.09 * scale)
    rg.setColorAt(0, rgba(skin.lighter(112), alpha))
    rg.setColorAt(1, rgba(skin.darker(118), alpha))
    p.setBrush(QBrush(rg))
    path = QPainterPath()
    path.addPolygon(QPolygonF([QPointF(*q) for q in palm]))
    p.drawPath(path)
    # rounded palm edge
    pen = QPen(rgba(skin.darker(112), alpha), 0.03 * scale)
    pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
    p.setPen(pen)
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawPath(path)
    # fingers, back to front
    chains = {"thumb": [1, 2, 3, 4], "index": [5, 6, 7, 8], "middle": [9, 10, 11, 12], "ring": [13, 14, 15, 16],
              "pinky": [17, 18, 19, 20]}
    order = sorted(chains.items(), key=lambda kv: depth[kv[1]].mean())
    for name, ch in order:
        for i in range(len(ch) - 1):
            a, b = pts[ch[i]], pts[ch[i + 1]]
            zf = depth[ch[i + 1]]
            col = skin.lighter(int(100 + clamp(zf * 900, -20, 14)))
            width = WIDTH[name] * scale * persp[ch[i + 1]] * (1 - 0.1 * i)
            pen = QPen(rgba(col, alpha), width)
            pen.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(pen)
            p.drawLine(QPointF(*a), QPointF(*b))
        # nail hint
        tip, pre = pts[ch[-1]], pts[ch[-2]]
        d = tip - pre
        n = np.linalg.norm(d) + 1e-6
        nail = tip - d / n * WIDTH[name] * scale * 0.22
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(rgba(skin.lighter(125), 0.35 * alpha))
        p.drawEllipse(QPointF(*nail), WIDTH[name] * scale * 0.22, WIDTH[name] * scale * 0.18)
    if flour > 0:
        rng = np.random.default_rng(seed)
        p.setPen(Qt.PenStyle.NoPen)
        for _ in range(260):
            j = rng.choice([4, 3, 8, 7, 12, 11, 16, 15, 20, 6, 10, 14])
            off = rng.normal(0, 0.006 * scale, 2)
            q = pts[j] + off
            p.setBrush(rgba(QColor("#F6F2EA"), flour * alpha * rng.uniform(0.15, 0.55)))
            r = rng.uniform(0.25, 0.9) * scale / 900
            p.drawEllipse(QPointF(*q), r, r)


def draw_hand_overlay(p, pts, alpha=1.0, highlight_index=True, pinch=0.0, line_color=BLUE, dim=False):
    """MediaPipe-style landmark overlay: connections + joints, index tip highlighted."""
    lc = rgba(line_color, (0.55 if dim else 0.95) * alpha)
    pen = QPen(lc, 3.0)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    p.setPen(pen)
    for a, b in HAND_CONNECTIONS:
        p.drawLine(QPointF(*pts[a]), QPointF(*pts[b]))
    for i, q in enumerate(pts):
        tip = i in (4, 8, 12, 16, 20)
        r = 5.2 if tip else 4.2
        p.setPen(QPen(lc, 1.6))
        p.setBrush(rgba(QColor("#FFFFFF"), alpha))
        p.drawEllipse(QPointF(*q), r, r)
    if highlight_index:
        glow_dot(p, *pts[8], 30, VIOLET, alpha)
        p.setPen(QPen(rgba(VIOLET_L, alpha), 2.5))
        p.setBrush(rgba(VIOLET, alpha))
        p.drawEllipse(QPointF(*pts[8]), 8, 8)
    if pinch > 0:
        col = rgba(VIOLET_L if pinch >= 1 else AMBER, alpha)
        pen = QPen(col, 2.5, Qt.PenStyle.DashLine if pinch < 1 else Qt.PenStyle.SolidLine)
        p.setPen(pen)
        p.drawLine(QPointF(*pts[4]), QPointF(*pts[8]))


# ---------------------------------------------------------------- face mesh
def _load_face():
    path = os.path.join(VDIR, "dl_face", "canonical_face_model.obj")
    verts, faces = [], []
    for line in open(path):
        if line.startswith("v "):
            verts.append([float(v) for v in line.split()[1:4]])
        elif line.startswith("f "):
            faces.append([int(tok.split("/")[0]) - 1 for tok in line.split()[1:4]])
    return np.array(verts), np.array(faces)


FACE_V, FACE_F = _load_face()
FACE_EDGES = sorted({tuple(sorted((f[i], f[(i + 1) % 3]))) for f in FACE_F for i in range(3)})
# MediaPipe face-oval contour indices
FACE_OVAL = [10, 338, 297, 332, 284, 251, 389, 356, 454, 323, 361, 288, 397, 365, 379, 378, 400, 377, 152, 148, 176,
             149, 150, 136, 172, 58, 132, 93, 234, 127, 162, 21, 54, 103, 67, 109]
LEFT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
RIGHT_EYE = [263, 249, 390, 373, 374, 380, 381, 382, 362, 398, 384, 385, 386, 387, 388, 466]
LIPS = [61, 146, 91, 181, 84, 17, 314, 405, 321, 375, 291, 409, 270, 269, 267, 0, 37, 39, 40, 185]
NOSE_TIP = 1


def project_face(cx, cy, scale, yaw=0.0, pitch=0.0, roll=0.0):
    """Canonical mesh (cm) rotated about the head centre. yaw>0 = turned to the viewer's right."""
    v = FACE_V - np.array([0.0, 0.0, -2.0])
    r = rot(yaw, pitch, roll)
    q = v @ r.T
    persp = 1.0 / (1.0 - q[:, 2] / 70.0)
    return np.stack([cx + q[:, 0] * scale * persp, cy - q[:, 1] * scale * persp], 1), q[:, 2]


def head_dir(yaw, pitch):
    r = rot(yaw, pitch, 0)
    return r @ np.array([0.0, 0.0, 1.0])


# ------------------------------------------------------------ soft layers
def soft_layer(p: QPainter, rect: QRectF, sigma: float, draw, opacity: float = 1.0):
    """Paint `draw(painter)` into an offscreen layer covering `rect` (design coords), blur it, composite.

    sigma is in design pixels; the layer is rendered at the painter's device scale.
    """
    import cv2

    tr = p.worldTransform()
    dev = tr.mapRect(rect).toAlignedRect()
    pad = int(sigma * tr.m11() * 3) + 2
    dev.adjust(-pad, -pad, pad, pad)
    if dev.width() <= 0 or dev.height() <= 0:
        return
    img = QImage(dev.width(), dev.height(), QImage.Format.Format_ARGB32_Premultiplied)
    img.fill(0)
    q = QPainter(img)
    q.setRenderHints(QPainter.RenderHint.Antialiasing)
    q.translate(-dev.x(), -dev.y())
    q.setWorldTransform(tr, True)
    draw(q)
    q.end()
    s = sigma * tr.m11()
    if s > 0.3:
        arr = np.frombuffer(img.constBits(), np.uint8).reshape(img.height(), img.bytesPerLine() // 4, 4)
        arr = cv2.GaussianBlur(arr[:, :img.width()].copy(), (0, 0), s)
        img = QImage(arr.data, arr.shape[1], arr.shape[0], arr.strides[0],
                     QImage.Format.Format_ARGB32_Premultiplied).copy()
    p.save()
    p.resetTransform()
    p.setOpacity(p.opacity() * opacity)
    p.drawImage(dev.x(), dev.y(), img)
    p.restore()


def hand_bounds(pts, scale, extra=0.0):
    x0, y0 = pts.min(0)
    x1, y1 = pts.max(0)
    m = 0.05 * scale + extra
    return QRectF(x0 - m, y0 - m, x1 - x0 + 2 * m, y1 - y0 + 2 * m + 0.5 * scale)


def soft_hand(p, pts, depth, persp, scale, sigma=1.0, **kw):
    r = hand_bounds(pts, scale)
    soft_layer(p, r, sigma, lambda q: draw_hand_body(q, pts, depth, persp, scale, **kw))
