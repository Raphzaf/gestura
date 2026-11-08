# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura. Gestura is free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Hands-free mouse: eyes, head and face expressions -> GestureEvents.

Pointer (``FaceMouseSettings.pointer``)
    head    the head works like a joystick-free pointer: yaw/pitch relative to the
            neutral pose map onto the screen (absolute, smoothed).
    gaze    the calibrated gaze model (see ``gaze.py``) places the pointer where
            the user looks; small movements inside a fixation radius are ignored.
    hybrid  gaze for big jumps, head for precision ("MAGIC pointing", Zhai et al.
            1999): looking far from the pointer for ``hybrid_jump_ms`` warps it to
            the gaze point; otherwise small head movements move it from there.
    gaze and hybrid fall back to head until the eyes are calibrated.

Eye actions (per eye, openness = EAR / that eye's own open baseline)
    wink left / right        one eye closed ``wink_min_ms``..``long_wink_ms`` while
                             the other stays open; fires when the eye reopens
    long wink left / right   one eye held closed ``long_wink_ms``; fires at once
    long blink               both eyes closed ``long_blink_ms``..hold; fires on reopen
    double blink             two deliberate blinks (each >= ``double_blink_min_ms``)
    eyes closed hold         both eyes closed ``eyes_closed_hold_ms``; fires at once
Natural blinks (both eyes, ~100–400 ms) trigger nothing: winks need one eye open,
long blinks need more time than a natural blink lasts.

Face expressions (relative to a rolling neutral, so no calibration is needed)
    mouth open, smile, eyebrows raised — each held ``expression_hold_ms``.

Also: dwell click (pointer kept still), scroll mode (head/eyes up-down scroll
instead of moving the pointer), pointer freeze while an eye closes (closing lids
drag the iris landmarks down, which would otherwise move the pointer just before
a wink-click).
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field

import numpy as np

from ..config.settings import FaceGesture, FaceMouseSettings, HeadGestureSettings
from ..core.types import GestureEvent, TrackingFrame
from .face_features import FaceFeatures, extract
from .filters import OneEuro2D
from .gaze import GazeModel

_LABELS = {
    FaceGesture.WINK_LEFT: "Left wink",
    FaceGesture.WINK_RIGHT: "Right wink",
    FaceGesture.LONG_WINK_LEFT: "Long left wink",
    FaceGesture.LONG_WINK_RIGHT: "Long right wink",
    FaceGesture.LONG_BLINK: "Long blink",
    FaceGesture.DOUBLE_BLINK: "Double blink",
    FaceGesture.EYES_CLOSED: "Eyes closed",
    FaceGesture.MOUTH_OPEN: "Mouth open",
    FaceGesture.SMILE: "Smile",
    FaceGesture.BROWS_RAISED: "Eyebrows raised",
    FaceGesture.DWELL: "Dwell",
}

DEFAULT_EAR = 0.27  # open-eye EAR used until a personal baseline is learned
MIN_BASELINE_SAMPLES = 20


class RollingStat:
    """Percentile of the last ``size`` samples (the neutral / open reference)."""

    def __init__(self, size: int, q: float, default: float) -> None:
        self.q, self.default = q, default
        self._v: deque[float] = deque(maxlen=size)

    def add(self, x: float) -> None:
        if math.isfinite(x):
            self._v.append(x)

    @property
    def ready(self) -> bool:
        return len(self._v) >= MIN_BASELINE_SAMPLES

    def value(self) -> float:
        if not self.ready:
            return self.default
        return float(np.percentile(np.fromiter(self._v, dtype=float), self.q))

    def reset(self) -> None:
        self._v.clear()


@dataclass(slots=True)
class FaceState:
    visible: bool = False
    pointer: str = ""  # effective pointer source: head | gaze | hybrid
    calibrated: bool = False
    left_open: float = 1.0  # openness relative to the eye's open baseline
    right_open: float = 1.0
    left_closed: bool = False
    right_closed: bool = False
    mouth: float = 0.0
    smile: float = 1.0  # relative to neutral
    brows: float = 1.0  # relative to neutral
    cursor: tuple[float, float] | None = None
    gaze: tuple[float, float] | None = None  # raw gaze estimate (before stabilization)
    frozen: bool = False
    dwell_progress: float = 0.0
    scroll_mode: bool = False
    features: tuple[float, float, float] | None = None  # (h, v, ear) for calibration
    yaw: float = 0.0  # absolute smoothed head angles (deg), for calibration
    pitch: float = 0.0
    eyes: tuple[tuple[float, float], tuple[float, float]] | None = None  # eye centres (frame)
    activity: str = ""  # what the eyes are doing right now ("Left eye closing…")
    progress: float = 0.0  # 0..1 toward the pending eye action
    paused_by_hand: bool = False


@dataclass(slots=True)
class _Eye:
    baseline: RollingStat = field(default_factory=lambda: RollingStat(240, 85, DEFAULT_EAR))
    closed: bool = False

    def update(self, ear: float, s: FaceMouseSettings) -> float:
        openness = ear / max(1e-6, self.baseline.value())
        if not self.closed and openness < s.eye_close_ratio:
            self.closed = True
        elif self.closed and openness > s.eye_open_ratio:
            self.closed = False
        self.baseline.add(ear)
        return openness


class FaceGestureEngine:
    def __init__(self, settings: FaceMouseSettings, head: HeadGestureSettings, mirrored: bool = True) -> None:
        self._head_filter = OneEuro2D()
        self._gaze_filter = OneEuro2D()
        self.recenter_offset = (0.0, 0.0)
        self.scroll_mode = False
        self.state = FaceState()
        self.mirrored = mirrored
        self._init_runtime()
        self.configure(settings, head, mirrored)

    # ----------------------------------------------------------- configuration
    def configure(self, settings: FaceMouseSettings, head: HeadGestureSettings, mirrored: bool = True) -> None:
        self.s, self.head = settings, head
        self.mirrored = mirrored
        self._head_filter.configure(settings.head_smoothing_min_cutoff, settings.head_smoothing_beta)
        self._gaze_filter.configure(settings.gaze_smoothing_min_cutoff, settings.gaze_smoothing_beta)
        self.model = GazeModel.from_list(settings.gaze_model)

    def _init_runtime(self) -> None:
        self._left, self._right = _Eye(), _Eye()
        self._smile = RollingStat(300, 50, 1.0)
        self._brows = RollingStat(300, 50, 1.0)
        self._both_since: float | None = None
        self._both_hold_fired = False
        self._wink_side: str | None = None
        self._wink_since = 0.0
        self._wink_long_fired = False
        self._last_deliberate_blink = float("-inf")
        self._cooldown_until = float("-inf")
        self._expr_since: dict[str, float | None] = {"mouth": None, "smile": None, "brows": None}
        self._expr_armed = {"mouth": True, "smile": True, "brows": True}
        self._history: deque[tuple[float, float, float]] = deque(maxlen=30)  # (t, u, v) emitted cursor
        self._frozen_at: tuple[float, float] | None = None
        self._settle_until = float("-inf")
        self._held_gaze: tuple[float, float] | None = None
        self._cursor: tuple[float, float] | None = None
        self._anchor: tuple[float, float] | None = None
        self._head_ref: tuple[float, float] | None = None
        self._jump_since: float | None = None
        self._dwell_anchor: tuple[float, float] | None = None
        self._dwell_since = 0.0
        self._dwell_armed = False
        self._scroll_ref: tuple[float, float] | None = None
        self._last_t: float | None = None
        self._head_pose: tuple[float, float] | None = None  # smoothed absolute yaw, pitch

    def reset(self) -> None:
        """Face lost / engine stopped: forget transient state, keep learned baselines."""
        left_b, right_b = self._left.baseline, self._right.baseline
        smile, brows = self._smile, self._brows
        self._init_runtime()
        self._left.baseline, self._right.baseline = left_b, right_b
        self._smile, self._brows = smile, brows
        self._head_filter.reset()
        self._gaze_filter.reset()
        self.scroll_mode = False
        self.state = FaceState()

    # ------------------------------------------------------------- commands
    @property
    def calibrated(self) -> bool:
        return self.model is not None

    @property
    def effective_pointer(self) -> str:
        p = self.s.pointer
        return "head" if p in ("gaze", "hybrid") and not self.calibrated else p

    @property
    def uses_head(self) -> bool:
        """True when head movement drives the pointer (head gestures must stay quiet)."""
        return self.effective_pointer in ("head", "hybrid")

    def toggle_scroll_mode(self) -> None:
        self.scroll_mode = not self.scroll_mode
        self._scroll_ref = None

    def recenter(self) -> None:
        """Make the current head pose the pointer's centre (fixes slow drift)."""
        if self._head_pose is not None:
            hy = self.head
            self.recenter_offset = (self._head_pose[0] - hy.neutral_yaw, self._head_pose[1] - hy.neutral_pitch)
        if self.effective_pointer == "hybrid" and self.state.gaze is not None:
            self._anchor = self._cursor = self.state.gaze
            self._head_ref = self._head_pose

    # ------------------------------------------------------------------ main
    def update(self, tf: TrackingFrame) -> list[GestureEvent]:
        now = tf.timestamp
        face = tf.face
        feats = extract(face.landmarks, tf.width, tf.height, self.mirrored) if face is not None else None
        if feats is None or face is None or face.pose is None:
            if self.state.visible:
                self.reset()
            return []
        dt = 1 / 30 if self._last_t is None else min(0.2, max(1e-3, now - self._last_t))
        self._last_t = now
        s = self.s
        events: list[GestureEvent] = []

        # ---- head pose (smoothed, absolute)
        hy, hp = self._head_filter(face.pose.yaw, face.pose.pitch, now)
        self._head_pose = (hy, hp)

        # ---- eyes
        lo = self._left.update(feats.left.ear, s)
        ro = self._right.update(feats.right.ear, s)
        events += self._eye_events(now, lo, ro)

        # ---- expressions
        events += self._expressions(now, feats)

        # ---- pointer
        target, gaze_pt = self._pointer(now, feats, hy, hp)
        closing_below = (s.eye_close_ratio + s.eye_open_ratio) / 2
        any_closing = lo < closing_below or ro < closing_below
        if s.freeze_on_blink and any_closing:
            if self._frozen_at is None:
                self._frozen_at = self._position_before(now - 0.12)
            self._settle_until = now + 0.15
        elif self._frozen_at is not None and now >= self._settle_until:
            self._frozen_at = None
            self._gaze_filter.reset()  # do not glide from the blink artefact
        frozen = self._frozen_at is not None

        cursor_out: tuple[float, float] | None = None
        if self.scroll_mode:
            # Scroll with the head when it drives the pointer: steadier than gaze jumps.
            source = self._head_point(hy, hp) if self.effective_pointer in ("head", "hybrid") else target
            events += self._scroll(source, dt)
        elif not frozen and target is not None:
            cursor_out = (min(1.0, max(0.0, target[0])), min(1.0, max(0.0, target[1])))
            events.append(GestureEvent(FaceGesture.CURSOR.value, now, {"x": cursor_out[0], "y": cursor_out[1]},
                                       "Eye/head pointer", continuous=True))
            self._history.append((now, *cursor_out))

        shown = cursor_out or (self._frozen_at if frozen else (self._history[-1][1:] if self._history else None))
        events += self._dwell(now, shown, frozen)

        self.state = FaceState(
            visible=True, pointer=self.effective_pointer, calibrated=self.calibrated,
            left_open=lo, right_open=ro, left_closed=self._left.closed, right_closed=self._right.closed,
            mouth=feats.mouth_open, smile=feats.smile / max(1e-6, self._smile.value()),
            brows=feats.brows / max(1e-6, self._brows.value()),
            cursor=shown, gaze=gaze_pt, frozen=frozen,
            dwell_progress=self._dwell_progress(now), scroll_mode=self.scroll_mode,
            features=(feats.gaze_h, feats.gaze_v, feats.ear), yaw=hy, pitch=hp,
            eyes=(feats.left.center, feats.right.center),
            activity=self._activity(now), progress=self._progress(now),
        )
        return events

    # ------------------------------------------------------------- eye events
    def _fire(self, events: list[GestureEvent], g: FaceGesture, now: float) -> None:
        if now < self._cooldown_until:
            return
        events.append(GestureEvent(g.value, now, {}, _LABELS[g]))
        self._cooldown_until = now + self.s.action_cooldown_ms / 1000

    def _eye_events(self, now: float, lo: float, ro: float) -> list[GestureEvent]:
        s = self.s
        ev: list[GestureEvent] = []
        lc, rc = self._left.closed, self._right.closed

        # Both eyes: blinks, long blink, eyes-closed hold
        if lc and rc:
            if self._both_since is None:
                self._both_since = now
                self._wink_side = None  # a wink that turns into a blink is cancelled
            held = now - self._both_since
            if not self._both_hold_fired and held >= s.eyes_closed_hold_ms / 1000:
                self._both_hold_fired = True
                self._fire(ev, FaceGesture.EYES_CLOSED, now)
        elif self._both_since is not None:
            held = now - self._both_since
            if not self._both_hold_fired:
                if held >= s.long_blink_ms / 1000:
                    self._fire(ev, FaceGesture.LONG_BLINK, now)
                elif held >= s.double_blink_min_ms / 1000:
                    if now - self._last_deliberate_blink <= s.double_blink_window_ms / 1000:
                        self._fire(ev, FaceGesture.DOUBLE_BLINK, now)
                        self._last_deliberate_blink = float("-inf")
                    else:
                        self._last_deliberate_blink = now
            self._both_since = None
            self._both_hold_fired = False
            self._wink_side = None
            return ev

        # One eye: winks. To start, the other eye must be clearly open; once started,
        # the wink continues as long as the other eye does not close (people often
        # squint the other eye a little while winking).
        side = None
        if self._wink_side is None:
            if lc and not rc and ro >= s.wink_other_eye_ratio:
                side = "left"
            elif rc and not lc and lo >= s.wink_other_eye_ratio:
                side = "right"
        elif (self._wink_side == "left" and lc and not rc) or (self._wink_side == "right" and rc and not lc):
            side = self._wink_side
        if side is not None:
            if self._wink_side != side:
                self._wink_side, self._wink_since, self._wink_long_fired = side, now, False
            held = now - self._wink_since
            if not self._wink_long_fired and held >= s.long_wink_ms / 1000:
                self._wink_long_fired = True
                self._fire(ev, FaceGesture.LONG_WINK_LEFT if side == "left" else FaceGesture.LONG_WINK_RIGHT, now)
        elif self._wink_side is not None:
            held = now - self._wink_since
            reopened = not lc and not rc
            if reopened and not self._wink_long_fired and s.wink_min_ms / 1000 <= held < s.long_wink_ms / 1000:
                self._fire(ev, FaceGesture.WINK_LEFT if self._wink_side == "left" else FaceGesture.WINK_RIGHT, now)
            self._wink_side = None
        return ev

    def _activity(self, now: float) -> str:
        if self._both_since is not None:
            return "Both eyes closed"
        if self._wink_side is not None:
            return f"{self._wink_side.capitalize()} eye closed"
        return ""

    def _progress(self, now: float) -> float:
        s = self.s
        if self._both_since is not None:
            return min(1.0, (now - self._both_since) / (s.long_blink_ms / 1000))
        if self._wink_side is not None:
            return min(1.0, (now - self._wink_since) / (s.long_wink_ms / 1000))
        return 0.0

    # ------------------------------------------------------------ expressions
    def _expressions(self, now: float, f: FaceFeatures) -> list[GestureEvent]:
        s = self.s
        ev: list[GestureEvent] = []
        smile_base, brow_base = self._smile.value(), self._brows.value()
        ready = self._smile.ready and self._brows.ready
        values = {
            "mouth": (f.mouth_open, s.mouth_open_ratio, s.mouth_open_ratio * 0.7, FaceGesture.MOUTH_OPEN),
            "smile": (f.smile / smile_base if ready else 1.0, s.smile_ratio,
                      1 + (s.smile_ratio - 1) / 2, FaceGesture.SMILE),
            "brows": (f.brows / brow_base if ready else 1.0, s.brow_raise_ratio,
                      1 + (s.brow_raise_ratio - 1) / 2, FaceGesture.BROWS_RAISED),
        }
        for key, (value, on, off, gesture) in values.items():
            if value >= on:
                if self._expr_since[key] is None:
                    self._expr_since[key] = now
                if self._expr_armed[key] and now - self._expr_since[key] >= s.expression_hold_ms / 1000:
                    self._expr_armed[key] = False
                    self._fire(ev, gesture, now)
            else:
                self._expr_since[key] = None
                if value <= off:
                    self._expr_armed[key] = True
        # Neutral references learn only from neutral-looking frames.
        if f.mouth_open < s.mouth_open_ratio * 0.7:
            self._smile.add(f.smile)
            self._brows.add(f.brows)
        return ev

    # ---------------------------------------------------------------- pointer
    def _head_point(self, yaw: float, pitch: float) -> tuple[float, float]:
        hd, s = self.head, self.s
        y = yaw - hd.neutral_yaw - self.recenter_offset[0]
        p = pitch - hd.neutral_pitch - self.recenter_offset[1]
        if hd.invert_yaw:
            y = -y
        if hd.invert_pitch:
            p = -p
        return 0.5 + 0.5 * y / s.head_range_yaw_deg, 0.5 + 0.5 * p / s.head_range_pitch_deg

    def _pointer(self, now: float, f: FaceFeatures, yaw: float,
                 pitch: float) -> tuple[tuple[float, float] | None, tuple[float, float] | None]:
        s = self.s
        gaze_pt = None
        eyes_open = not self._left.closed and not self._right.closed
        if self.model is not None and eyes_open:
            raw = self.model.predict((f.gaze_h, f.gaze_v, f.ear), yaw, pitch, s.screen_half_angle_deg)
            gaze_pt = self._gaze_filter(raw[0], raw[1], now)
        mode = self.effective_pointer
        if mode == "head":
            return self._head_point(yaw, pitch), gaze_pt
        if mode == "gaze":
            if gaze_pt is None:
                return self._held_gaze, gaze_pt
            if self._held_gaze is None or math.dist(gaze_pt, self._held_gaze) > s.gaze_fixation_radius:
                self._held_gaze = gaze_pt
            return self._held_gaze, gaze_pt
        # hybrid
        if self._anchor is None or self._head_ref is None:
            if gaze_pt is None:
                return None, gaze_pt
            self._anchor, self._head_ref = gaze_pt, (yaw, pitch)
        if gaze_pt is not None and self._cursor is not None and \
                math.dist(gaze_pt, self._cursor) > s.hybrid_jump_distance:
            if self._jump_since is None:
                self._jump_since = now
            if now - self._jump_since >= s.hybrid_jump_ms / 1000:
                self._anchor, self._head_ref, self._jump_since = gaze_pt, (yaw, pitch), None
        else:
            self._jump_since = None
        dy, dp = yaw - self._head_ref[0], pitch - self._head_ref[1]
        if self.head.invert_yaw:
            dy = -dy
        if self.head.invert_pitch:
            dp = -dp
        g = s.hybrid_head_gain
        self._cursor = (self._anchor[0] + g * 0.5 * dy / s.head_range_yaw_deg,
                        self._anchor[1] + g * 0.5 * dp / s.head_range_pitch_deg)
        # Keep the anchor on screen so turning back is immediate after hitting an edge.
        cu, cv = min(1.0, max(0.0, self._cursor[0])), min(1.0, max(0.0, self._cursor[1]))
        if (cu, cv) != self._cursor:
            self._anchor = (self._anchor[0] + cu - self._cursor[0], self._anchor[1] + cv - self._cursor[1])
            self._cursor = (cu, cv)
        return self._cursor, gaze_pt

    def _position_before(self, t: float) -> tuple[float, float] | None:
        best = None
        for ts, u, v in self._history:
            if ts <= t:
                best = (u, v)
        if best is None and self._history:
            best = self._history[0][1:]
        return best

    # ----------------------------------------------------------- dwell / scroll
    def _dwell(self, now: float, cursor: tuple[float, float] | None, frozen: bool) -> list[GestureEvent]:
        s = self.s
        if not s.dwell_click or cursor is None or self.scroll_mode or frozen:
            if not s.dwell_click or self.scroll_mode:
                self._dwell_armed = False
                self._dwell_anchor = None
            return []
        if self._dwell_anchor is None or math.dist(cursor, self._dwell_anchor) > s.dwell_radius:
            self._dwell_anchor, self._dwell_since, self._dwell_armed = cursor, now, True
            return []
        if self._dwell_armed and now - self._dwell_since >= s.dwell_ms / 1000:
            self._dwell_armed = False  # move away to re-arm: no repeated clicks while resting
            ev: list[GestureEvent] = []
            self._fire(ev, FaceGesture.DWELL, now)
            if not ev:
                self._dwell_armed = True  # in cooldown: try again a little later
                self._dwell_since = now
            return ev
        return []

    def _dwell_progress(self, now: float) -> float:
        if not self.s.dwell_click or not self._dwell_armed or self._dwell_anchor is None:
            return 0.0
        return min(1.0, (now - self._dwell_since) / (self.s.dwell_ms / 1000))

    def _scroll(self, target: tuple[float, float] | None, dt: float) -> list[GestureEvent]:
        s = self.s
        if target is None:
            return []
        if self._scroll_ref is None:
            self._scroll_ref = target
            return []
        out = []
        dx_out = dy_out = 0.0
        for axis in (0, 1):
            d = target[axis] - self._scroll_ref[axis]
            if abs(d) <= s.scroll_dead_zone:
                continue
            strength = min(1.0, (abs(d) - s.scroll_dead_zone) / max(1e-6, 0.3 - s.scroll_dead_zone))
            notches = math.copysign(strength * s.scroll_speed * dt, d)
            if axis == 1:
                dy_out = -notches  # look / turn down -> content scrolls down (wheel negative)
            else:
                dx_out = notches
        if dx_out or dy_out:
            out.append(GestureEvent(FaceGesture.SCROLL.value, self._last_t or 0.0,
                                    {"dx": dx_out, "dy": dy_out}, "Eye/head scroll", continuous=True))
        return out
