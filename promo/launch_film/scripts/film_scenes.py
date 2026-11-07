# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Gestura launch film: scenes. Every beat is timed from the voice-over cues."""

from __future__ import annotations

import math

import numpy as np
from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QRadialGradient

from film_core import *  # noqa: F401,F403

# --------------------------------------------------------------- timeline
S1, S2, S3, S4, S5, S6, S7 = 0.0, 5.8, 12.6, 23.8, 32.6, 40.5, 45.6
XFADE = 0.5

# Scene 3 beats
T_MOVE0, T_MOVE1 = cue("s3a") + 0.1, cue("s3b") - 0.15
T_CLICK = cue("s3b") + 0.55
T_SCROLL0, T_SCROLL1 = cue("s3c") + 0.05, cue("s3d") + 0.1
T_PALM0 = cue("s3d") + 0.35
T_PAUSED = T_PALM0 + 0.45 + 1.2
# Scene 4 beats (head)
T_TURN_R = 27.15
T_FIRE_R = T_TURN_R + 0.62
T_TURN_L = 28.95
T_FIRE_L = T_TURN_L + 0.62
T_NOD1 = 30.35
T_FIRE_N1 = T_NOD1 + 0.32
T_NOD2 = 31.05
T_FIRE_N2 = T_NOD2 + 0.32
# Scene 5 typing: (key label, char appended or action)
TYPE_SEQ = [("⇧", "shift"), ("p", "P"), ("a", "a"), ("s", "s"), ("t", "t"), ("a", "a"), ("a", "a"), ("⌫", "back"),
            ("Space", " "), ("f", "f"), ("o", "o"), ("r", "r"), ("Space", " "), ("2", "2"), ("Enter", "enter")]
T_TYPE0 = 34.75
T_KEY = 0.355
KEY_TIMES = [T_TYPE0 + i * T_KEY + 0.2 for i in range(len(TYPE_SEQ))]  # moment of each pinch
# Scene 6 dashboard toggles
T_TOGGLES = (cue("s6c") + 0.15, cue("s6c") + 0.55, cue("s6c") + 0.95)


def events():
    """Sound-design cue list: (time, kind)."""
    ev = [(t, "whoosh") for t in (S2 - 0.25, S3 - 0.2, S4 - 0.2, S5 - 0.2, S6 - 0.2, S7 - 0.25)]
    ev += [(S2 + 0.25, "chime_soft"), (8.85, "camera_on")]
    ev += [(10.85 + i * 0.045, "tick_soft") for i in range(0, 21, 3)]
    ev += [(T_CLICK, "click"), (T_PAUSED, "pause")]
    ev += [(T_SCROLL0 + 0.15 + i * 0.12, "scroll_tick") for i in range(12)]
    ev += [(T_FIRE_R, "swish"), (T_FIRE_L, "swish"), (T_FIRE_N1, "confirm_prompt"), (T_FIRE_N2, "confirm")]
    ev += [(S5 + 0.15, "keyboard_in")]
    ev += [(t, "enter" if TYPE_SEQ[i][1] == "enter" else "key") for i, t in enumerate(KEY_TIMES)]
    ev += [(S6 + i * 0.6, "cut") for i in range(1, 5)]
    ev += [(t, "toggle") for t in T_TOGGLES]
    ev += [(S7 + 0.3, "sonic_logo")]
    return sorted(ev)


# ------------------------------------------------------------ backgrounds
def background(p, t, glow=1.0):
    p.fillRect(QRectF(0, 0, W, H), BG)
    g = QRadialGradient(QPointF(W * 0.5, H * 0.08), W * 0.75)
    g.setColorAt(0, rgba(QColor("#182033"), 0.85 * glow))
    g.setColorAt(0.55, rgba(QColor("#11131A"), 0.6 * glow))
    g.setColorAt(1, rgba(BG, 0))
    p.fillRect(QRectF(0, 0, W, H), QBrush(g))
    g2 = QRadialGradient(QPointF(W * 0.88, H * 0.95), W * 0.45)
    g2.setColorAt(0, rgba(VIOLET, 0.10 * glow))
    g2.setColorAt(1, rgba(VIOLET, 0))
    p.fillRect(QRectF(0, 0, W, H), QBrush(g2))


def brand_corner(p, alpha=1.0):
    p.save()
    p.setOpacity(alpha)
    logo_mark(p, 74, 62, 46)
    text(p, "Gestura", 104, 62, 22, 650, TEXT, display=True)
    p.restore()


# ----------------------------------------------------------- webcam panel
def webcam_frame(p, r: QRectF, t, alpha=1.0, fps="30 FPS · 24 ms", status="Camera on", status_col=GREEN):
    """Dark room backdrop inside a rounded webcam panel; returns after setting a clip."""
    rrect(p, r, 22, fill=QColor("#0D0E13"), pen=LINE, pen_w=1.5)
    p.save()
    clip = QPainterPath()
    clip.addRoundedRect(r, 22, 22)
    p.setClipPath(clip)
    g = QLinearGradient(r.topLeft(), r.bottomLeft())
    g.setColorAt(0, QColor("#191B24"))
    g.setColorAt(1, QColor("#0E0F15"))
    p.fillRect(r, QBrush(g))
    # soft room light: lamp bokeh + window glow
    for (fx, fy, rad, col, a) in ((0.86, 0.18, 0.22, AMBER, 0.10), (0.08, 0.35, 0.35, BLUE, 0.08),
                                  (0.7, 0.9, 0.3, VIOLET, 0.06)):
        rg = QRadialGradient(QPointF(r.x() + r.width() * fx, r.y() + r.height() * fy), r.width() * rad)
        rg.setColorAt(0, rgba(col, a))
        rg.setColorAt(1, rgba(col, 0))
        p.fillRect(r, QBrush(rg))
    return clip


def webcam_hud(p, r: QRectF, alpha=1.0, fps="30 FPS · 24 ms", status="Camera on", status_col=GREEN, label=None):
    p.restore()  # clip from webcam_frame
    chip(p, r.x() + 22, r.y() + 32, status, status_col, alpha, size=15)
    w = text_width(fps, 15, 600) + 28
    rr = QRectF(r.right() - 22 - w, r.y() + 32 - 16.5, w, 33)
    rrect(p, rr, 16.5, fill=rgba(PANEL2, 0.9 * alpha), pen=rgba(LINE, alpha))
    text(p, fps, rr.x() + 14, r.y() + 32, 15, 600, MUTED, alpha=alpha)
    if label:
        chip(p, r.center().x(), r.bottom() - 34, label[0], label[1], alpha, size=18, align="center")


# ----------------------------------------------------------------- person
def draw_bust(p, cx, cy, s, yaw=0.0, pitch=0.0, mesh=1.0, mesh_points=1.0, alpha=1.0, arrow=0.0):
    """Head-and-shoulders silhouette with canonical face mesh overlay. s = px per cm."""
    p.save()
    p.setOpacity(alpha)
    # shoulders / torso
    sh = QPainterPath()
    base_y = cy + 21 * s
    sh.moveTo(QPointF(cx - 34 * s, cy + 60 * s))
    sh.cubicTo(QPointF(cx - 33 * s, base_y + 4 * s), QPointF(cx - 22 * s, base_y - 3 * s), QPointF(cx - 7 * s, base_y - 5 * s))
    sh.lineTo(QPointF(cx + 7 * s, base_y - 5 * s))
    sh.cubicTo(QPointF(cx + 22 * s, base_y - 3 * s), QPointF(cx + 33 * s, base_y + 4 * s), QPointF(cx + 34 * s, cy + 60 * s))
    sh.closeSubpath()
    g = QLinearGradient(QPointF(cx - 34 * s, 0), QPointF(cx + 34 * s, 0))
    g.setColorAt(0, QColor("#1A1E2A"))
    g.setColorAt(0.5, QColor("#232837"))
    g.setColorAt(1, QColor("#171A24"))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(g))
    p.drawPath(sh)
    # neck
    ng = QLinearGradient(QPointF(cx - 6 * s, 0), QPointF(cx + 6 * s, 0))
    ng.setColorAt(0, QColor("#2A2427"))
    ng.setColorAt(0.5, QColor("#3A3134"))
    ng.setColorAt(1, QColor("#262124"))
    p.setBrush(QBrush(ng))
    p.drawRoundedRect(QRectF(cx - 6.2 * s + yaw * 0.04 * s, cy + 6 * s, 12.4 * s, 13 * s), 4 * s, 4 * s)
    # head silhouette from the projected mesh
    pts, depth = project_face(cx, cy, s, yaw, pitch)
    oval = pts[FACE_OVAL]
    centre = oval.mean(0)
    head = QPainterPath()
    big = centre + (oval - centre) * 1.10
    head.moveTo(QPointF(*big[0]))
    for q in big[1:]:
        head.lineTo(QPointF(*q))
    head.closeSubpath()
    hg = QRadialGradient(QPointF(centre[0] - yaw * 0.12 * s, centre[1] - 2 * s), 13 * s)
    hg.setColorAt(0, QColor("#4A3E3D"))
    hg.setColorAt(1, QColor("#2A2427"))
    p.setBrush(QBrush(hg))
    p.drawPath(head)
    # hair cap (behind forehead)
    hair = QPainterPath()
    top = pts[10]
    hair.addEllipse(QPointF(top[0] - yaw * 0.08 * s, top[1] + 2.2 * s - pitch * 0.05 * s), 9.6 * s, 6.0 * s)
    p.setBrush(QColor("#17141A"))
    p.drawPath(hair.subtracted(QPainterPath()))
    # rim light from the monitor
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.setPen(QPen(rgba(BLUE_L, 0.25), 2.2))
    p.drawPath(head)
    p.restore()
    # ---- mesh overlay
    if mesh > 0:
        visible = depth > -1.0
        pen = QPen(rgba(BLUE, 0.18 * mesh * alpha), 0.8)
        p.setPen(pen)
        for a, b in FACE_EDGES:
            if visible[a] and visible[b]:
                p.drawLine(QPointF(*pts[a]), QPointF(*pts[b]))
        pen = QPen(rgba(BLUE_L, 0.75 * mesh * alpha), 1.6)
        p.setPen(pen)
        for contour in (FACE_OVAL, LEFT_EYE, RIGHT_EYE, LIPS):
            for i in range(len(contour)):
                a, b = contour[i], contour[(i + 1) % len(contour)]
                p.drawLine(QPointF(*pts[a]), QPointF(*pts[b]))
    if mesh_points > 0:
        p.setPen(Qt.PenStyle.NoPen)
        n = int(len(pts) * clamp(mesh_points))
        order = np.argsort(pts[:, 1])  # reveal top to bottom
        p.setBrush(rgba(QColor("#FFFFFF"), 0.75 * alpha))
        for i in order[:n]:
            if depth[i] > -1.0:
                p.drawEllipse(QPointF(*pts[i]), 1.25, 1.25)
    if arrow > 0:
        d = head_dir(yaw, pitch)
        nose = pts[NOSE_TIP]
        tip = nose + np.array([d[0], -d[1]]) * 22 * s * arrow
        pen = QPen(rgba(VIOLET_L, alpha * arrow), 4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawLine(QPointF(*nose), QPointF(*tip))
        glow_dot(p, *tip, 22, VIOLET, arrow * alpha)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(rgba(VIOLET_L, alpha * arrow))
        p.drawEllipse(QPointF(*tip), 6, 6)
    return pts


# ---------------------------------------------------------------- browser
def browser(p, r: QRectF, url="recipes.example/creamy-tomato-pasta", alpha=1.0):
    rrect(p, r, 14, fill=QColor("#F5F6F8"), pen=QColor("#2A2E3A"), pen_w=1)
    bar = QRectF(r.x(), r.y(), r.width(), 46)
    path = QPainterPath()
    path.addRoundedRect(bar.adjusted(0, 0, 0, 14), 14, 14)
    p.save()
    p.setClipRect(bar)
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor("#E6E8ED"))
    p.drawPath(path)
    p.restore()
    for i, c in enumerate(("#FF6B6B", "#FFC15E", "#4ADE80")):
        p.setBrush(QColor(c))
        p.drawEllipse(QPointF(r.x() + 20 + i * 18, r.y() + 23), 5.5, 5.5)
    for i, ch in enumerate(("‹", "›")):
        text(p, ch, r.x() + 84 + i * 26, r.y() + 22, 24, 500, QColor("#5A6070"))
    pill = QRectF(r.x() + 150, r.y() + 9, r.width() - 300, 28)
    rrect(p, pill, 14, fill=QColor("#FFFFFF"))
    text(p, url, pill.x() + 16, pill.center().y(), 14, 500, QColor("#5A6070"))
    content = QRectF(r.x(), r.y() + 46, r.width(), r.height() - 46)
    p.save()
    clip = QPainterPath()
    clip.addRoundedRect(content, 14, 14)
    clip.addRect(content.adjusted(0, 0, 0, -20))
    p.setClipRect(content)
    return content


def browser_end(p):
    p.restore()


INK = QColor("#14161E")
INK2 = QColor("#5A6070")
INK3 = QColor("#D9DCE3")


def text_lines(p, x, y, w, n, gap=20, last=0.6, color=INK3, h=9):
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(color)
    for i in range(n):
        ww = w * (last if i == n - 1 else (0.97 - 0.05 * (i % 3)))
        p.drawRoundedRect(QRectF(x, y + i * gap, ww, h), h / 2, h / 2)


def food_image(p, r: QRectF, hue=0):
    g = QLinearGradient(r.topLeft(), r.bottomRight())
    cols = [("#E0593B", "#F2A541"), ("#7BAE5B", "#E8D46A"), ("#E6B655", "#F1E3B8")][hue % 3]
    g.setColorAt(0, QColor(cols[0]))
    g.setColorAt(1, QColor(cols[1]))
    rrect(p, r, 12, fill=QBrush(g))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(255, 255, 255, 60))
    p.drawEllipse(r.center(), r.height() * 0.32, r.height() * 0.32)
    p.setBrush(QColor(255, 255, 255, 40))
    p.drawEllipse(r.center() + QPointF(r.width() * 0.08, -r.height() * 0.05), r.height() * 0.18, r.height() * 0.18)


def recipe_page(p, c: QRectF, scroll=0.0, saved=0.0, btn_hover=0.0):
    """Long recipe article; returns the 'Save recipe' button rect in screen coords."""
    x0, y = c.x() + 48, c.y() + 34 - scroll
    text(p, "WEEKNIGHT DINNERS", x0, y, 13, 700, BLUE, spacing=8)
    text(p, "Creamy Tomato Pasta", x0, y + 40, 38, 700, INK, display=True)
    text(p, "25 min  ·  Serves 2  ·  Step-by-step", x0, y + 82, 16, 500, INK2)
    btn = QRectF(c.right() - 228, y + 22, 180, 46)
    fill = lerp_color(QColor("#14161E"), QColor("#2E7D5B"), saved)
    rrect(p, btn, 23, fill=fill.lighter(int(100 + 18 * btn_hover)))
    text(p, "Saved ✓" if saved > 0.5 else "Save recipe", btn.center().x(), btn.center().y(), 16, 650,
         QColor("#FFFFFF"), align="center")
    food_image(p, QRectF(x0, y + 116, c.width() - 96, 210), 0)
    yy = y + 360
    for i, (title, n) in enumerate((("Ingredients", 4), ("Step 1 — Boil the pasta", 3), ("Step 2 — Make the sauce", 4),
                                    ("Step 3 — Combine and simmer", 3), ("Step 4 — Serve", 3))):
        text(p, title, x0, yy, 22, 700, INK, display=True)
        text_lines(p, x0, yy + 30, c.width() - 96, n)
        yy += 60 + n * 20 + 24
    return btn


def lerp_color(a: QColor, b: QColor, k: float) -> QColor:
    return QColor(int(lerp(a.red(), b.red(), k)), int(lerp(a.green(), b.green(), k)), int(lerp(a.blue(), b.blue(), k)))


def step_page(p, c: QRectF, step: int):
    x0, y = c.x() + 48, c.y() + 34
    text(p, f"CREAMY TOMATO PASTA  ·  STEP {step} OF 4", x0, y, 13, 700, BLUE, spacing=6)
    titles = {1: "Boil the pasta", 2: "Make the sauce", 3: "Combine and simmer", 4: "Serve"}
    text(p, titles[step], x0, y + 44, 40, 700, INK, display=True)
    food_image(p, QRectF(x0, y + 86, c.width() - 96, 190), step)
    text_lines(p, x0, y + 306, c.width() - 96, 5, gap=24, h=11)
    # step dots
    for i in range(4):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(BLUE if i + 1 == step else INK3)
        p.drawEllipse(QPointF(c.center().x() - 36 + i * 24, c.bottom() - 30), 5, 5)


def screen_frame(p, r: QRectF):
    """A minimal monitor: thin bezel, dark wallpaper."""
    rrect(p, r.adjusted(-10, -10, 10, 10), 26, fill=QColor("#07080B"), pen=LINE, pen_w=1.5)
    g = QLinearGradient(r.topLeft(), r.bottomRight())
    g.setColorAt(0, QColor("#1A2236"))
    g.setColorAt(1, QColor("#221B33"))
    rrect(p, r, 16, fill=QBrush(g))


# =================================================================== SCENE 1
def scene1(p, t):
    background(p, t, glow=0.45)
    zoom = 1.0 + 0.03 * ease_in_out(seg(t, 0, 6))
    p.save()
    p.translate(W / 2, H * 0.45)
    p.scale(zoom, zoom)
    p.translate(-W / 2, -H * 0.45)
    # counter
    g = QLinearGradient(QPointF(0, 800), QPointF(0, H))
    g.setColorAt(0, QColor("#1D1B1E"))
    g.setColorAt(1, QColor("#0F0E11"))
    p.fillRect(QRectF(-100, 800, W + 200, H), QBrush(g))
    # warm kitchen light from the top right
    rg = QRadialGradient(QPointF(W * 0.82, 120), 900)
    rg.setColorAt(0, rgba(AMBER, 0.10))
    rg.setColorAt(1, rgba(AMBER, 0))
    p.fillRect(QRectF(0, 0, W, H), QBrush(rg))
    # laptop
    scr = QRectF(600, 200, 720, 450)
    rrect(p, scr.adjusted(-14, -14, 14, 14), 20, fill=QColor("#0B0C10"), pen=QColor("#2B2F3A"), pen_w=2)
    c = browser(p, scr)
    recipe_page(p, c, scroll=470)
    pulse = 0.5 + 0.5 * math.sin(t * 5.0)
    pill = QRectF(c.center().x() - 78, c.bottom() - 58, 156, 40)
    rrect(p, pill, 20, fill=lerp_color(QColor("#14161E"), BLUE, 0.35 + 0.35 * pulse))
    text(p, "Step 3  ↓", pill.center().x(), pill.center().y(), 16, 650, QColor("#FFFFFF"), align="center")
    browser_end(p)
    base = QPainterPath()
    base.moveTo(QPointF(520, 678))
    base.lineTo(QPointF(1400, 678))
    base.lineTo(QPointF(1470, 742))
    base.lineTo(QPointF(450, 742))
    base.closeSubpath()
    bgr = QLinearGradient(QPointF(0, 678), QPointF(0, 742))
    bgr.setColorAt(0, QColor("#30343F"))
    bgr.setColorAt(1, QColor("#1E2129"))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(bgr))
    p.drawPath(base)
    p.setBrush(QColor("#262A33"))
    p.drawRoundedRect(QRectF(870, 700, 180, 30), 6, 6)  # trackpad
    # drifting flour in the light
    rng = np.random.default_rng(11)
    for i in range(36):
        x = rng.uniform(300, 1700) + 30 * math.sin(t * 0.5 + i)
        y = (rng.uniform(150, 900) - t * rng.uniform(4, 14)) % 900 + 100
        glow_dot(p, x, y, rng.uniform(2, 5), QColor("#F6F2EA"), 0.25)

    # foreground (out of focus): bowl + left hand, reaching right hand
    def fg(q):
        bowl = QPainterPath()
        bowl.moveTo(QPointF(40, 880))
        bowl.cubicTo(QPointF(70, 1150), QPointF(560, 1150), QPointF(590, 880))
        bowl.closeSubpath()
        bg = QLinearGradient(QPointF(40, 0), QPointF(590, 0))
        bg.setColorAt(0, QColor("#AEB3BE"))
        bg.setColorAt(1, QColor("#5E6472"))
        q.setPen(Qt.PenStyle.NoPen)
        q.setBrush(QBrush(bg))
        q.drawPath(bowl)
        q.setBrush(QColor("#E7DCC4"))
        q.drawEllipse(QPointF(315, 882), 275, 38)
        w2 = hand_world("hold")
        pts2, d2, p2 = project_hand(w2, 470, 1180, 2500, roll=-30, yaw=20, pitch=30, mirror=True)
        draw_hand_body(q, pts2, d2, p2, 2500, flour=1.0, seed=7)
        reach = ease_in_out(seg(t, 1.5, 2.6)) * (1 - ease_in_out(seg(t, 3.35, 4.4)))
        k = ease_in_out(seg(t, 1.7, 2.5)) * (1 - ease_in_out(seg(t, 3.5, 4.2)))
        w = hand_world("hold", "point", k * 0.85)
        pts, depth, persp = project_hand(w, lerp(1700, 1330, reach), lerp(1230, 1010, reach), 2500,
                                         roll=lerp(55, 38, reach), yaw=-18, pitch=28)
        draw_hand_body(q, pts, depth, persp, 2500, flour=1.0, seed=3)

    soft_layer(p, QRectF(-80, 560, W + 160, 620), 5.5, fg)
    p.restore()
    headline(p, "Your hands are busy.", W / 2, 100, t, 0.6, size=58, out_t=5.25)


# =================================================================== SCENE 2
def scene2(p, t):
    background(p, t)
    lt = t - S2
    # logo build and lift
    lift = ease_in_out(seg(t, 7.55, 8.35))
    lx, ly, ls = W / 2, lerp(470, 150, lift), lerp(220, 92, lift)
    logo_mark(p, lx, ly, ls, t_rel=lt - 0.1)
    if lift < 1:
        p.save()
        p.setOpacity(1 - lift)
        headline(p, "Meet Gestura.", W / 2, 680, t, cue("s2a"), size=66)
        p.restore()
    if t >= 7.7:
        headline(p, "Your computer. Your gestures.", W / 2, 262, t, 7.7, size=44, color=TEXT)
    # webcam device + panel
    cam_in = ease_out(seg(t, 8.45, 8.9))
    if cam_in > 0:
        cx, cy = W / 2, 352
        rrect(p, QRectF(cx - 70, cy - 16, 140, 32), 16, fill=rgba(QColor("#1C1F29"), cam_in), pen=rgba(LINE, cam_in))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(rgba(QColor("#05060A"), cam_in))
        p.drawEllipse(QPointF(cx, cy), 10, 10)
        led = seg(t, 8.85, 8.95)
        p.setBrush(rgba(GREEN, led))
        p.drawEllipse(QPointF(cx + 30, cy), 3.5, 3.5)
        if led > 0:
            glow_dot(p, cx + 30, cy, 14, GREEN, led)
    open_k = ease_in_out(seg(t, 8.95, 9.7))
    if open_k > 0:
        pw, ph = lerp(140, 1100, open_k), lerp(10, 600, open_k)
        r = QRectF(W / 2 - pw / 2, 390, pw, ph)
        webcam_frame(p, r, t)
        if open_k > 0.6:
            a = seg(open_k, 0.6, 1)
            mesh_pts = seg(t, 9.8, 10.6)
            draw_bust(p, r.center().x() - 120, r.y() + 250, 9.2, yaw=4 * math.sin(t * 0.8), pitch=-2,
                      mesh=seg(t, 10.3, 10.9), mesh_points=mesh_pts, alpha=a)
            # hand raises into view
            rise = ease_out(seg(t, 9.9, 10.8))
            w = hand_world("relax", "point", ease_in_out(seg(t, 10.4, 11.0)))
            hx, hy = r.center().x() + 240, lerp(r.bottom() + 260, r.y() + 430, rise)
            pts, depth, persp = project_hand(w, hx, hy, 1750, roll=-8, yaw=-10)
            soft_hand(p, pts, depth, persp, 1750, sigma=0.9, alpha=a)
            sk = seg(t, 10.8, 11.5)
            if sk > 0:
                draw_hand_overlay(p, pts, alpha=sk, highlight_index=sk > 0.8)
        webcam_hud(p, r, alpha=open_k, label=None)
        tags = seg(t, 11.3, 11.7)
        if tags > 0:
            chip(p, r.x() + 150, r.bottom() - 34, "Face · tracked", BLUE, tags, size=16)
            chip(p, r.right() - 330, r.bottom() - 34, "Right hand · 99%", VIOLET, tags, size=16)


# =================================================================== SCENE 3
CAM3 = QRectF(80, 230, 860, 620)
SCR3 = QRectF(990, 240, 850, 600)


def _wrist_for_tip(tip):
    """Wrist position that puts the pointing fingertip at `tip` (webcam coords)."""
    pts, _, _ = project_hand(hand_world("point"), 0.0, 0.0, 1650, roll=-6, yaw=-8)
    return tip[0] - pts[8][0], tip[1] - pts[8][1]


def _screen_to_cam(x, y):
    rx0, ry0, rx1, ry1 = CAM3.x() + 180, CAM3.y() + 80, CAM3.x() + 700, CAM3.y() + 360
    u = (x - (SCR3.x() + 40)) / (SCR3.width() - 80)
    v = (y - (SCR3.y() + 60)) / (SCR3.height() - 100)
    return rx0 + u * (rx1 - rx0), ry0 + v * (ry1 - ry0)


SAVE_BTN = (1014 + 802 - 228 + 90, 308 + 34 + 22 + 23)  # centre of "Save recipe" in the scene-3 browser


def _hand_path3(t):
    """Index-finger cursor path: wrist position inside the webcam panel and pose state."""
    start = (CAM3.x() + 300, CAM3.y() + 500)
    end = _wrist_for_tip(_screen_to_cam(*SAVE_BTN))
    k = ease_in_out(seg(t, T_MOVE0, T_MOVE1))
    # gentle S-curve
    x = lerp(start[0], end[0], k) + math.sin(k * math.pi) * -40
    y = lerp(start[1], end[1], k) - math.sin(k * math.pi * 2) * 60
    if t > T_SCROLL0 - 0.6:  # move to the scroll start position
        m = ease_in_out(seg(t, T_SCROLL0 - 0.6, T_SCROLL0))
        x, y = lerp(x, CAM3.x() + 450, m), lerp(y, CAM3.y() + 420, m)
    if t > T_SCROLL0:
        s = seg(t, T_SCROLL0 + 0.1, T_SCROLL1 - 0.25)
        y += 150 * ease_in_out(min(1, s * 1.6)) - 60 * ease_in_out(seg(s, 0.62, 1.0))
    if t > T_PALM0 - 0.2:
        m = ease_in_out(seg(t, T_PALM0 - 0.2, T_PALM0 + 0.35))
        x, y = lerp(x, CAM3.x() + 440, m), lerp(y, CAM3.y() + 470, m)
    return x, y


def _pose3(t):
    pinch_in = ease_in_out(seg(t, T_CLICK - 0.3, T_CLICK - 0.05))
    pinch_out = ease_in_out(seg(t, T_CLICK + 0.18, T_CLICK + 0.45))
    if t < T_CLICK + 0.5:
        return ("point", "pinch", pinch_in * (1 - pinch_out))
    if t < T_SCROLL0 + 0.1:
        return ("point", "two", ease_in_out(seg(t, T_SCROLL0 - 0.55, T_SCROLL0 - 0.05)))
    if t < T_PALM0 + 0.5:
        return ("two", "open", ease_in_out(seg(t, T_PALM0 - 0.15, T_PALM0 + 0.35)))
    return ("open", None, 0.0)


def _cam_to_screen(x, y):
    """Active region of the webcam panel -> screen panel coordinates."""
    rx0, ry0, rx1, ry1 = CAM3.x() + 180, CAM3.y() + 80, CAM3.x() + 700, CAM3.y() + 360
    u, v = clamp((x - rx0) / (rx1 - rx0)), clamp((y - ry0) / (ry1 - ry0))
    return SCR3.x() + 40 + u * (SCR3.width() - 80), SCR3.y() + 60 + v * (SCR3.height() - 100)


def scene3_parts(p, t, show_text=True):
    hx, hy = _hand_path3(t)
    a, b, k = _pose3(t)
    w = hand_world(a, b, k)
    pts, depth, persp = project_hand(w, hx, hy, 1650, roll=-6, yaw=-8)
    cursor_mode = t < T_SCROLL0 - 0.5
    paused = t >= T_PAUSED
    # ---- webcam
    status = ("Paused", AMBER) if paused else ("Camera on", GREEN)
    webcam_frame(p, CAM3, t)
    if cursor_mode:
        rx0, ry0, rx1, ry1 = CAM3.x() + 180, CAM3.y() + 80, CAM3.x() + 700, CAM3.y() + 360
        p.setPen(QPen(rgba(MUTED, 0.35), 1.2, Qt.PenStyle.DashLine))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(rx0, ry0, rx1 - rx0, ry1 - ry0), 10, 10)
    soft_hand(p, pts, depth, persp, 1650, sigma=0.9)
    pinch_state = 0.0
    if a == "point" and b == "pinch":
        pinch_state = 1.0 if k > 0.85 else (0.5 if k > 0.3 else 0.0)
    draw_hand_overlay(p, pts, alpha=1.0, highlight_index=not paused and t < T_PALM0, pinch=pinch_state,
                      dim=paused)
    if t >= T_PALM0 + 0.45:  # palm-hold progress ring
        c = (pts[0] + pts[9]) / 2
        prog = seg(t, T_PALM0 + 0.45, T_PAUSED)
        p.setPen(QPen(rgba(LINE, 0.9), 6))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QPointF(*c), 120, 120)
        pen = QPen(AMBER if prog < 1 else GREEN, 6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawArc(QRectF(c[0] - 120, c[1] - 120, 240, 240), 90 * 16, int(-360 * 16 * prog))
    if t < T_CLICK - 0.3:
        label = ("Index finger  →  Cursor", BLUE)
    elif t < T_SCROLL0 - 0.3:
        label = ("Thumb + index pinch  →  Click", VIOLET)
    elif t < T_PALM0:
        label = ("Two fingers up / down  →  Scroll", BLUE)
    elif not paused:
        label = ("Open palm held  →  Pause", AMBER)
    else:
        label = ("Gesture control paused", AMBER)
    webcam_hud(p, CAM3, status=status[0], status_col=status[1], label=label)
    # ---- screen
    screen_frame(p, SCR3)
    br = QRectF(SCR3.x() + 24, SCR3.y() + 22, SCR3.width() - 48, SCR3.height() - 44)
    c = browser(p, br)
    scroll = 0.0
    if t > T_SCROLL0:
        s = seg(t, T_SCROLL0 + 0.1, T_SCROLL1 - 0.25)
        scroll = 420 * ease_in_out(min(1, s * 1.6)) - 170 * ease_in_out(seg(s, 0.62, 1.0))
    saved = seg(t, T_CLICK, T_CLICK + 0.25)
    # cursor position from the index fingertip
    cx, cy = _cam_to_screen(*pts[8])
    if t > T_CLICK - 0.32 and t < T_SCROLL0 - 0.5:
        cx, cy = _cam_to_screen(*_frozen_tip3())  # freeze during the pinch, like the real engine
    btn = recipe_page(p, c, scroll=scroll, saved=saved, btn_hover=1.0 if t > T_CLICK - 0.6 else 0.0)
    browser_end(p)
    if t < T_SCROLL0 + 0.2:
        ripple(p, cx, cy, seg(t, T_CLICK, T_CLICK + 0.5))
        cursor_arrow(p, cx, cy, 1.45, alpha=1 - seg(t, T_SCROLL0 - 0.3, T_SCROLL0 + 0.1),
                     pressed=1.0 if abs(t - T_CLICK) < 0.12 else 0.0)
    if t > T_SCROLL0 and t < T_PALM0:
        # scroll indicator
        a_ = window(t, T_SCROLL0, T_PALM0, 0.2)
        chip(p, SCR3.right() - 120, SCR3.y() + 110, "Scrolling", BLUE, a_, size=15, align="center")
    if paused:
        k = ease_out(seg(t, T_PAUSED, T_PAUSED + 0.3))
        chip(p, SCR3.center().x(), SCR3.y() + 118, "Gestura paused — hold open palm to resume", AMBER, k, size=17,
             align="center", fill=QColor("#0E1016"))
    if show_text:
        p.setOpacity(1.0)
        if t >= cue("s3a"):
            _move_pinch_scroll(p, t)


_TIP_CACHE = {}


def _frozen_tip3():
    if "tip" not in _TIP_CACHE:
        hx, hy = _hand_path3(T_CLICK - 0.32)
        a, b, k = _pose3(T_CLICK - 0.32)
        pts, _, _ = project_hand(hand_world(a, b, k), hx, hy, 1650, roll=-6, yaw=-8)
        _TIP_CACHE["tip"] = tuple(pts[8])
    return _TIP_CACHE["tip"]


def _move_pinch_scroll(p, t):
    words = [("Move.", cue("s3a")), ("Pinch.", cue("s3b")), ("Scroll.", cue("s3c"))]
    size = 56
    gap = 26
    widths = [text_width(w_, size, 600, True) for w_, _ in words]
    x = W / 2 - (sum(widths) + gap * 2) / 2
    active = 0 if t < cue("s3b") else 1 if t < cue("s3c") else 2 if t < cue("s3d") else -1
    for i, ((w_, t0), ww) in enumerate(zip(words, widths)):
        k = ease_out(seg(t, t0, t0 + 0.45))
        if k > 0:
            col = TEXT if (i == active or active == -1) else MUTED
            text(p, w_, x, 128, size, 600, col, display=True, alpha=k, rise=(1 - k) * 16)
        x += ww + gap


def scene3(p, t):
    background(p, t)
    brand_corner(p)
    scene3_parts(p, t)


# =================================================================== SCENE 4
CAM4 = QRectF(80, 230, 860, 620)
SCR4 = QRectF(990, 240, 850, 600)


def head_angles(t):
    """(yaw, pitch) of the user's head, degrees."""
    def bump(t0, hold, amp, rise=0.35, fall=0.4):
        return amp * ease_in_out(seg(t, t0, t0 + rise)) * (1 - ease_in_out(seg(t, t0 + rise + hold, t0 + rise + hold + fall)))
    yaw = bump(T_TURN_R, 0.45, 26) + bump(T_TURN_L, 0.45, -26) + 3 * math.sin(t * 0.9) * 0.4
    pitch = bump(T_NOD1, 0.05, 17, 0.22, 0.28) + bump(T_NOD2, 0.05, 17, 0.22, 0.28)
    return yaw, pitch


def scene4_parts(p, t, show_text=True):
    yaw, pitch = head_angles(t)
    webcam_frame(p, CAM4, t)
    draw_bust(p, CAM4.center().x(), CAM4.y() + 290, 11.5, yaw=yaw, pitch=pitch, mesh=1.0, mesh_points=1.0,
              arrow=seg(t, S4 + 0.6, S4 + 1.1))
    # angle meters
    mx = CAM4.x() + 40
    my = CAM4.bottom() - 120
    for i, (name, val, thr, rng) in enumerate((("Yaw", yaw, 18, 40), ("Pitch", pitch, 13, 30))):
        y = my + i * 34
        text(p, f"{name} {val:+.0f}°", mx, y, 15, 600, MUTED)
        bx, bw = mx + 110, 220
        rrect(p, QRectF(bx, y - 4, bw, 8), 4, fill=PANEL2)
        mid = bx + bw / 2
        x1 = mid + clamp(val / rng, -1, 1) * bw / 2
        active = abs(val) >= thr
        rrect(p, QRectF(min(mid, x1), y - 4, abs(x1 - mid), 8), 4, fill=VIOLET if active else BLUE)
        p.setPen(QPen(rgba(TEXT, 0.8), 1.5))
        for s_ in (-1, 1):
            xx = mid + s_ * thr / rng * bw / 2
            p.drawLine(QPointF(xx, y - 8), QPointF(xx, y + 8))
    fired = [(T_FIRE_R, "Turn right  →  Next page", VIOLET), (T_FIRE_L, "Turn left  →  Previous page", VIOLET),
             (T_FIRE_N1, "Nod  →  Repeat to confirm", AMBER), (T_FIRE_N2, "Nod again  →  Confirmed", GREEN)]
    label = ("Head tracking · armed", BLUE)
    for tf, txt, col in fired:
        if t >= tf:
            label = (txt, col)
    webcam_hud(p, CAM4, fps="30 FPS · 22 ms", status="Face tracked", status_col=BLUE, label=label)
    # ---- browser with step pages
    screen_frame(p, SCR4)
    br = QRectF(SCR4.x() + 24, SCR4.y() + 22, SCR4.width() - 48, SCR4.height() - 44)
    c = browser(p, br, url="recipes.example/creamy-tomato-pasta/steps")
    page_pos = 2 + ease_in_out(seg(t, T_FIRE_R, T_FIRE_R + 0.45)) - ease_in_out(seg(t, T_FIRE_L, T_FIRE_L + 0.45))
    base = math.floor(page_pos)
    frac = page_pos - base
    for step, off in ((base, -frac), (base + 1, 1 - frac)):
        if 1 <= step <= 4 and -1 < off < 1:
            p.save()
            p.translate(off * c.width(), 0)
            step_page(p, c, step)
            p.restore()
    # confirmation dialog for nod
    d_in = ease_out(seg(t, T_FIRE_N1, T_FIRE_N1 + 0.25))
    if d_in > 0:
        p.fillRect(c, rgba(QColor("#0A0B0F"), 0.35 * d_in))
        dr = QRectF(c.center().x() - 210, c.center().y() - 90, 420, 180)
        rrect(p, dr, 16, fill=rgba(QColor("#FFFFFF"), d_in))
        done = seg(t, T_FIRE_N2, T_FIRE_N2 + 0.2)
        text(p, "Mark step 2 as done?" if done < 0.5 else "Step 2 done ✓", dr.x() + 28, dr.y() + 46, 22, 700,
             INK, display=True, alpha=d_in)
        b1 = QRectF(dr.right() - 300, dr.bottom() - 70, 120, 44)
        b2 = QRectF(dr.right() - 164, dr.bottom() - 70, 136, 44)
        rrect(p, b1, 22, fill=rgba(QColor("#EEF0F4"), d_in))
        text(p, "Cancel", b1.center().x(), b1.center().y(), 15, 600, INK2, align="center", alpha=d_in)
        conf = lerp_color(BLUE, QColor("#2E9D6B"), done)
        rrect(p, b2, 22, fill=rgba(conf, d_in))
        text(p, "Confirm ⏎", b2.center().x(), b2.center().y(), 15, 650, QColor("#FFFFFF"), align="center", alpha=d_in)
        ripple(p, b2.center().x(), b2.center().y(), seg(t, T_FIRE_N2, T_FIRE_N2 + 0.5), GREEN)
    browser_end(p)
    # overlay toast (Gestura feedback overlay)
    for tf, txt, col in ((T_FIRE_R, "Next page", VIOLET), (T_FIRE_L, "Previous page", VIOLET),
                         (T_FIRE_N1, "Repeat to confirm: Enter", AMBER), (T_FIRE_N2, "Enter", GREEN)):
        k = window(t, tf, tf + 0.85, 0.15)
        if k > 0:
            chip(p, SCR4.center().x(), SCR4.y() + 118, txt, col, k, size=17, align="center", fill=QColor("#0E1016"))
    if show_text:
        headline(p, "Navigate with your head.", W / 2, 128, t, cue("s4a"), size=56)


def scene4(p, t):
    background(p, t)
    brand_corner(p)
    scene4_parts(p, t)


# =================================================================== SCENE 5
KB_ROWS = [
    [("Esc", 1.2), *[(c, 1) for c in "1234567890"], ("⌫", 1.8)],
    [("Tab", 1.4), *[(c, 1) for c in "qwertyuiop"], ("Enter", 1.6)],
    [("Caps", 1.7), *[(c, 1) for c in "asdfghjkl"], ("'", 1), ("", 0.01)],
    [("⇧", 2.0), *[(c, 1) for c in "zxcvbnm"], (",", 1), (".", 1), ("⇧ ", 1.9)],
    [("Ctrl", 1.4), ("Win", 1.2), ("Alt", 1.2), ("Space", 6.2), ("←", 1), ("→", 1)],
]
KB = QRectF(390, 640, 1140, 360)


def keyboard_layout(r: QRectF):
    keys = {}
    rows = len(KB_ROWS)
    pad, gap = 18, 8
    top = r.y() + 52
    kh = (r.height() - 52 - pad - gap * (rows - 1)) / rows
    for ri, row in enumerate(KB_ROWS):
        total = sum(w_ for _, w_ in row)
        unit = (r.width() - pad * 2 - gap * (len(row) - 1)) / total
        x = r.x() + pad
        for lab, w_ in row:
            kw = unit * w_
            if lab:
                keys.setdefault(lab, QRectF(x, top + ri * (kh + gap), kw, kh))
            x += kw + gap
    return keys


KEYS = keyboard_layout(KB)


def draw_keyboard(p, r: QRectF, alpha, pressed: dict, shift=False, highlights=None, typed=""):
    rrect(p, r, 18, fill=rgba(PANEL, 0.97 * alpha), pen=rgba(LINE, alpha), pen_w=1.5)
    text(p, "⠿  Gestura keyboard", r.right() - 22, r.y() + 28, 15, 600, MUTED, align="right", alpha=alpha)
    text(p, typed[-28:], r.x() + 22, r.y() + 28, 16, 600, TEXT, alpha=alpha)
    for lab, kr in keyboard_layout(r).items():
        k = pressed.get(lab, 0.0)
        hl = (highlights or {}).get(lab, 0.0)
        fill = lerp_color(PANEL2, BLUE, k)
        rrect(p, kr, 9, fill=rgba(fill, alpha), pen=rgba(lerp_color(LINE, VIOLET_L, max(k, hl)), alpha),
              pen_w=1.2 + 1.5 * hl)
        shown = lab.strip()
        if len(shown) == 1 and shown.isalpha():
            shown = shown.upper() if shift else shown
        if lab == "⇧" and shift:
            fill2 = rgba(VIOLET, 0.35 * alpha)
            rrect(p, kr, 9, fill=fill2)
        text(p, shown, kr.center().x(), kr.center().y(), 20 if len(shown) == 1 else 15, 600,
             lerp_color(TEXT, QColor("#04121A"), k), align="center", alpha=alpha)


def typing_state(t):
    """Returns typed text, shift flag, current key target index and per-key press strength."""
    typed = ""
    shift = False
    pressed = {}
    for i, ((lab, act), kt) in enumerate(zip(TYPE_SEQ, KEY_TIMES)):
        if t >= kt:
            if act == "shift":
                shift = True
            elif act == "back":
                typed = typed[:-1]
            elif act == "enter":
                pass
            else:
                typed += act if not (shift and act.isalpha()) else act.upper()
                if act.isalpha():
                    shift = False
        d = t - kt
        if -0.02 <= d < 0.25:
            pressed[lab] = max(pressed.get(lab, 0), 1 - d / 0.25)
    return typed, shift, pressed


def cursor_on_keys(t):
    """Cursor glides key to key, arriving just before each pinch."""
    centres = [KEYS[lab].center() for lab, _ in TYPE_SEQ]
    start = QPointF(KB.center().x() + 120, KB.y() - 80)
    prev = start
    for i, kt in enumerate(KEY_TIMES):
        arrive = kt - 0.06
        leave = KEY_TIMES[i - 1] + 0.08 if i else T_TYPE0 - 0.3
        if t < arrive:
            k = ease_in_out(seg(t, leave, arrive))
            return QPointF(lerp(prev.x(), centres[i].x(), k), lerp(prev.y(), centres[i].y(), k)), i
        prev = centres[i]
    return prev, len(TYPE_SEQ) - 1


def scene5_parts(p, t, show_text=True):
    sr = QRectF(250, 200, 1420, 820)
    screen_frame(p, sr)
    br = QRectF(sr.x() + 40, sr.y() + 30, sr.width() - 80, 440)
    c = browser(p, br, url="recipes.example/search")
    text(p, "Find a recipe", c.x() + 60, c.y() + 50, 30, 700, INK, display=True)
    field = QRectF(c.x() + 60, c.y() + 90, c.width() - 120, 64)
    typed, shift, pressed = typing_state(t)
    entered = t >= KEY_TIMES[-1]
    rrect(p, field, 32, fill=QColor("#FFFFFF"), pen=BLUE, pen_w=2.5)
    text(p, "⌕", field.x() + 24, field.center().y(), 26, 500, INK2)
    shown = typed if typed else ""
    tw = text(p, shown, field.x() + 64, field.center().y(), 24, 500, INK) if shown else 0
    if not shown:
        text(p, "Search recipes…", field.x() + 64, field.center().y(), 24, 500, QColor("#9AA0AE"))
    if not entered and (t * 2) % 1 < 0.6:
        p.fillRect(QRectF(field.x() + 66 + tw, field.center().y() - 15, 2.5, 30), INK)
    if entered:
        k = ease_out(seg(t, KEY_TIMES[-1], KEY_TIMES[-1] + 0.4))
        for i in range(3):
            card = QRectF(c.x() + 60 + i * ((c.width() - 120) / 3), c.y() + 180 + (1 - k) * 20, (c.width() - 160) / 3, 170)
            p.setOpacity(k)
            food_image(p, QRectF(card.x(), card.y(), card.width(), 110), i)
            text(p, ("Creamy Tomato Pasta", "Pesto Pasta for 2", "Lemon Pasta")[i], card.x(), card.y() + 134, 17, 650, INK)
            p.setOpacity(1)
    browser_end(p)
    # keyboard
    kin = ease_out(seg(t, S5 + 0.1, S5 + 0.6))
    p.save()
    p.translate(0, (1 - kin) * 120)
    hl = {}
    calls = [("Esc", "Escape", 33.2), ("5", "Numbers", 33.45), ("Space", "Space", 33.7), ("⌫", "Backspace", 33.95),
             ("Enter", "Enter", 34.2), ("⇧", "Shift", 34.45)]
    for lab, _, t0 in calls:
        hl[lab] = window(t, t0, t0 + 0.75, 0.15)
    draw_keyboard(p, KB, kin, pressed, shift, hl, typed)
    for ci, (lab, name, t0) in enumerate(calls):
        k = hl[lab]
        if k > 0:
            kr = KEYS[lab]
            ly = KB.y() - 30 - (ci % 2) * 36
            p.setPen(QPen(rgba(VIOLET_L, 0.7 * k), 1.5))
            p.drawLine(QPointF(kr.center().x(), ly + 14), QPointF(kr.center().x(), kr.y() + 2))
            chip(p, kr.center().x(), ly, name, VIOLET, k, size=15, dot=False, align="center")
    p.restore()
    # cursor + pinch flash
    if t >= T_TYPE0 - 0.3 and kin >= 1:
        pos, idx = cursor_on_keys(t)
        pinch = any(abs(t - kt) < 0.1 for kt in KEY_TIMES)
        for kt in KEY_TIMES:
            ripple(p, pos.x(), pos.y(), seg(t, kt, kt + 0.35))
        cursor_arrow(p, pos.x(), pos.y(), 1.4, pressed=1.0 if pinch else 0.0)
    # mini webcam inset (top-right): hand pinching in rhythm
    inset = QRectF(1580, 60, 300, 210)
    ia = ease_out(seg(t, S5 + 0.3, S5 + 0.7))
    if ia > 0:
        p.setOpacity(ia)
        webcam_frame(p, inset, t)
        nearest = min(KEY_TIMES, key=lambda kt: abs(t - kt))
        pk = math.exp(-((t - nearest) / 0.09) ** 2) if t > T_TYPE0 - 0.2 else 0.0
        w = hand_world("point", "pinch", pk)
        pts, d, pp = project_hand(w, inset.center().x() + 10, inset.bottom() + 40, 1050, roll=-6, yaw=-8)
        soft_hand(p, pts, d, pp, 1050, sigma=0.7)
        draw_hand_overlay(p, pts, pinch=1.0 if pk > 0.8 else 0.0)
        webcam_hud(p, inset, fps="30 FPS", status="Pinch = key", status_col=VIOLET)
        p.setOpacity(1)
    if show_text:
        headline(p, "Type without touching.", W / 2 - 160, 118, t, cue("s5"), size=56)


def scene5(p, t):
    background(p, t)
    brand_corner(p)
    scene5_parts(p, t)


# =================================================================== SCENE 6
MONTAGE = [(14.6, scene3_parts), (T_CLICK + 0.05, scene3_parts), (18.4, scene3_parts), (T_FIRE_R + 0.3, scene4_parts),
           (37.3, scene5_parts)]


def dashboard(p, r: QRectF, t):
    rrect(p, r, 18, fill=QColor("#0E1014"), pen=LINE, pen_w=1.5)
    side = QRectF(r.x(), r.y(), 250, r.height())
    p.save()
    clip = QPainterPath()
    clip.addRoundedRect(r, 18, 18)
    p.setClipPath(clip)
    p.fillRect(side, QColor("#161920"))
    p.restore()
    logo_mark(p, side.x() + 40, side.y() + 48, 40)
    text(p, "Gestura", side.x() + 68, side.y() + 48, 22, 700, TEXT, display=True)
    for i, item in enumerate(("Dashboard", "Gesture Studio", "Virtual Keyboard", "Settings")):
        y = side.y() + 120 + i * 50
        if i == 0:
            rrect(p, QRectF(side.x() + 14, y - 20, side.width() - 28, 40), 10, fill=PANEL2)
            p.fillRect(QRectF(side.x() + 14, y - 20, 3, 40), BLUE)
        text(p, item, side.x() + 34, y, 16, 600, TEXT if i == 0 else MUTED)
    x0 = side.right() + 32
    text(p, "Dashboard", x0, r.y() + 48, 24, 650, TEXT, display=True)
    chip(p, r.right() - 470, r.y() + 48, "Camera on", GREEN, size=14)
    chip(p, r.right() - 330, r.y() + 48, "Active", GREEN, size=14)
    er = QRectF(r.right() - 210, r.y() + 30, 182, 38)
    rrect(p, er, 10, fill=QColor("#FF5A5F"))
    text(p, "■  EMERGENCY STOP", er.center().x(), er.center().y(), 13, 800, QColor("#FFFFFF"), align="center")
    # status cards
    cw = (r.right() - x0 - 32 - 3 * 18) / 4
    for i, (title, val, col) in enumerate((("CAMERA", "On · 30 FPS", GREEN), ("HAND TRACKING", "Right hand · 99%", GREEN),
                                           ("HEAD TRACKING", "Face · armed", GREEN), ("CURRENT GESTURE", "Pinch → Click", BLUE))):
        cr = QRectF(x0 + i * (cw + 18), r.y() + 96, cw, 110)
        rrect(p, cr, 14, fill=PANEL, pen=LINE)
        text(p, title, cr.x() + 18, cr.y() + 28, 12, 700, MUTED, spacing=8)
        text(p, val, cr.x() + 18, cr.y() + 70, 19, 650, TEXT if i < 3 else BLUE_L)
    # modes
    mr = QRectF(x0, r.y() + 230, r.right() - x0 - 32, r.bottom() - r.y() - 260)
    rrect(p, mr, 14, fill=PANEL, pen=LINE)
    text(p, "OPERATING MODES", mr.x() + 22, mr.y() + 30, 12, 700, MUTED, spacing=8)
    modes = (("Mouse Control", "Index finger moves the cursor · pinch clicks · two fingers scroll", BLUE),
             ("Navigation", "Turn your head for back / forward · nod to confirm", VIOLET),
             ("Virtual Keyboard", "Floating keyboard · select keys with the hand cursor", BLUE_L))
    for i, (name, desc, col) in enumerate(modes):
        y = mr.y() + 78 + i * 74
        on = ease_out(seg(t, T_TOGGLES[i], T_TOGGLES[i] + 0.2))
        text(p, name, mr.x() + 22, y, 21, 650, TEXT)
        text(p, desc, mr.x() + 22, y + 26, 14, 500, MUTED)
        sw = QRectF(mr.right() - 86, y - 6, 58, 30)
        rrect(p, sw, 15, fill=lerp_color(PANEL2, col, on))
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#FFFFFF"))
        p.drawEllipse(QPointF(lerp(sw.x() + 15, sw.right() - 15, on), sw.center().y()), 11, 11)
        if 0 < on < 1 or seg(t, T_TOGGLES[i], T_TOGGLES[i] + 0.5) < 1:
            glow_dot(p, sw.center().x(), sw.center().y(), 50, col, window(t, T_TOGGLES[i], T_TOGGLES[i] + 0.6, 0.1))


_CLIP_IMG = {}


def scene6(p, t, render_clip=None):
    background(p, t)
    i = int((t - S6) / 0.6)
    if t < S6 + 3.0 and i < len(MONTAGE):
        ct, fn = MONTAGE[i]
        local = ct + (t - S6 - i * 0.6) * 0.8
        k = seg(t, S6 + i * 0.6, S6 + i * 0.6 + 0.6)
        zoom = 1.04 + 0.05 * k
        p.save()
        p.translate(W / 2, H / 2 + 40)
        p.scale(zoom * 0.86, zoom * 0.86)
        p.translate(-W / 2, -H / 2)
        fn(p, local, show_text=False)
        p.restore()
        p.fillRect(QRectF(0, 0, W, 210), QBrush(_top_fade()))
    dash_k = ease_in_out(seg(t, S6 + 2.95, S6 + 3.45))
    if dash_k > 0:
        p.save()
        p.setOpacity(dash_k)
        r = QRectF(260, 260, 1400, 560)
        p.translate(0, (1 - dash_k) * 40)
        dashboard(p, r, t)
        p.restore()
    headline(p, "One webcam. Multiple ways to interact.", W / 2, 118, t, cue("s6a"), size=54)
    brand_corner(p)


def _top_fade():
    g = QLinearGradient(QPointF(0, 0), QPointF(0, 210))
    g.setColorAt(0, rgba(BG, 1))
    g.setColorAt(0.7, rgba(BG, 0.85))
    g.setColorAt(1, rgba(BG, 0))
    return g


# =================================================================== SCENE 7
def scene7(p, t):
    background(p, t, glow=0.8)
    lt = t - S7
    logo_mark(p, W / 2, 420, 230, t_rel=lt)
    wordmark(p, W / 2, 640, 74, t_rel=t - cue("s7a"))
    k = ease_out(seg(t, cue("s7b"), cue("s7b") + 0.6))
    if k > 0:
        text(p, "Control your computer. Without touching it.", W / 2, 728, 30, 500, MUTED, align="center",
             display=True, alpha=k, rise=(1 - k) * 10)
    end = seg(t, 49.55, 50.0)
    if end > 0:
        p.fillRect(QRectF(0, 0, W, H), rgba(QColor("#000000"), end))


SCENES = [(S1, S2, scene1), (S2, S3, scene2), (S3, S4, scene3), (S4, S5, scene4), (S5, S6, scene5), (S6, S7, scene6),
          (S7, DUR + 1, scene7)]


def draw_frame(img: QImage, t: float, scale: float):
    """Render global time t into img. Scene changes dip briefly through the background."""
    p = QPainter(img)
    p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing |
                     QPainter.RenderHint.SmoothPixmapTransform)
    p.scale(scale, scale)
    idx = max(i for i, (a, _, _) in enumerate(SCENES) if t >= a - XFADE / 2) if t >= 0 else 0
    a = SCENES[idx][0]
    k = seg(t, a - XFADE / 2, a + XFADE / 2) if idx > 0 else 1.0
    if k < 0.5:  # end of the previous scene, darkening
        SCENES[idx - 1][2](p, t)
        dim = ease_in_out(k * 2)
    else:
        SCENES[idx][2](p, t)
        dim = 1 - ease_in_out((k - 0.5) * 2) if idx > 0 else 0.0
    if dim > 0:
        p.resetTransform()
        p.fillRect(QRectF(0, 0, img.width(), img.height()), rgba(BG, dim))
    p.end()
