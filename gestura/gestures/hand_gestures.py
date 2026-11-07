"""Hand gesture engine: TrackingFrame stream -> GestureEvents.

Design rules
------------
* No gesture fires from a single frame: poses are debounced, pinches need
  `pinch_min_frames`, holds need time, swipes need distance within a window.
* Hysteresis on every threshold (pinch closes below `pinch_on_ratio`, opens
  above `pinch_off_ratio`).
* Losing the hand resets all transient state so nothing stays "pressed"; a
  drag in progress is always ended with a drop event.
* A fist is a clutch: while held, the hand produces no events at all.
* The engine only *describes* gestures. It never touches the OS.

Interaction model
-----------------
POINT (index extended)              -> hand.cursor (continuous, smoothed)
thumb+index pinch, released         -> hand.pinch (count=1, or 2 for a quick second pinch)
thumb+index pinch held              -> hand.drag_start, cursor follows, release -> hand.drag_end
thumb+middle pinch                  -> hand.middle_pinch
TWO (index+middle) move             -> hand.scroll (continuous, dx/dy in notches)
THREE (index+middle+ring) up/down   -> hand.volume_up / hand.volume_down (one event per step)
THREE, fast horizontal swipe        -> hand.three_swipe_left / hand.three_swipe_right
OPEN palm, fast horizontal move     -> hand.swipe_left / hand.swipe_right
OPEN palm held still                -> hand.palm_hold
two OPEN hands, spread / bring in   -> hand.zoom_in / hand.zoom_out (one event per step)
FIST                                -> clutch (nothing)

With drag enabled, a click fires when the pinch *opens* (so a held pinch can
become a drag instead). A double click is two clicks within the OS
double-click interval, exactly like a physical mouse; the second quick one is
labelled "Double click" (count=2) for feedback.
"""

from __future__ import annotations

import enum
from collections import deque
from dataclasses import dataclass, field, replace

from ..config.settings import CursorSettings, HandGesture, HandGestureSettings, TrackingSettings
from ..core.types import GestureEvent, HandObservation, TrackingFrame
from .filters import OneEuro2D, OneEuroFilter
from .gesture_state import Cooldown, Debounced, HoldTimer
from .hand_features import HandFeatures, Pose, compute

# Guards measured on sample photos (see docs/GESTURES.md):
MIN_INDEX_REACH_FOR_PINCH = 0.55  # a fist has index reach ~0.49
MIN_MIDDLE_REACH_FOR_PINCH = 0.60  # pointing with thumb on middle has ~0.46
ZOOM_AFTERGLOW_S = 1.0  # single-palm gestures stay off this long after a two-hand zoom


class PinchPhase(str, enum.Enum):
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"


class _Pinch:
    def __init__(self) -> None:
        self.phase = PinchPhase.OPEN
        self.frames = 0

    def update(self, close_cond: bool, open_cond: bool, min_frames: int) -> str | None:
        """Returns "closed" on the frame the pinch closes, "opened" when a closed pinch opens."""
        if self.phase == PinchPhase.CLOSED:
            if open_cond:
                self.phase, self.frames = PinchPhase.OPEN, 0
                return "opened"
            return None
        if close_cond:
            self.frames += 1
            self.phase = PinchPhase.CLOSING
            if self.frames >= min_frames:
                self.phase = PinchPhase.CLOSED
                return "closed"
        else:
            self.phase, self.frames = PinchPhase.OPEN, 0
        return None

    @property
    def engaged(self) -> bool:
        return self.phase != PinchPhase.OPEN

    def reset(self) -> None:
        self.phase, self.frames = PinchPhase.OPEN, 0


class _Steps:
    """Turns accumulated motion into whole steps, capped per frame, without backlog."""

    def __init__(self) -> None:
        self.acc = 0.0

    def feed(self, amount: float, cap: int) -> int:
        self.acc += amount
        n = 0
        while self.acc >= 1 and n < cap:
            self.acc -= 1
            n += 1
        while self.acc <= -1 and -n < cap:
            self.acc += 1
            n -= 1
        self.acc = max(-0.999, min(0.999, self.acc))
        return n

    def reset(self) -> None:
        self.acc = 0.0


@dataclass(slots=True)
class HandState:
    """Snapshot for the UI (Gesture Studio, Dashboard)."""

    visible: bool = False
    hand_index: int | None = None
    handedness: str = ""
    score: float = 0.0
    pose: Pose = Pose.NONE
    raw_pose: Pose = Pose.NONE
    features: HandFeatures | None = None
    mode: str = "idle"  # idle | cursor | drag | scroll | volume | zoom | palm | clutch
    cursor_frame: tuple[float, float] | None = None  # smoothed anchor, frame coords
    cursor_screen: tuple[float, float] | None = None  # 0..1 screen coords
    frozen: bool = False
    left_pinch: str = "open"
    right_pinch: str = "open"
    palm_progress: float = 0.0
    dragging: bool = False
    last_events: list[str] = field(default_factory=list)


class HandGestureEngine:
    def __init__(self, hand: HandGestureSettings, cursor: CursorSettings, tracking: TrackingSettings) -> None:
        self._cursor_filter = OneEuro2D()
        self._scroll_filter = OneEuro2D(min_cutoff=3.0, beta=0.0)
        self._three_filter = OneEuro2D(min_cutoff=3.0, beta=0.0)
        self._zoom_filter = OneEuroFilter(min_cutoff=3.0, beta=0.0)
        self._prev_three: tuple[float, float] | None = None
        self._prev_zoom: float | None = None
        self._volume_steps = _Steps()
        self._zoom_steps = _Steps()
        self._pose = Debounced(Pose.NONE, 3)
        self._zoom_pose = Debounced(False, 3)
        self._left = _Pinch()
        self._right = _Pinch()
        self._click_cd = Cooldown(0.1)
        self._right_cd = Cooldown(0.6)
        self._pause_cd = Cooldown(2.0)
        self._swipe_cd = Cooldown(1.0)
        self._palm = HoldTimer()
        self._palm_latched = False
        self._palm_hist: deque[tuple[float, float, float]] = deque()  # (t, x, y)
        self._three_hist: deque[tuple[float, float, float]] = deque()
        self._last_click_t = float("-inf")
        self._click_count = 0
        self._pinch_closed_at: float | None = None  # pending click (drag enabled)
        self._dragging = False
        self._zoom_until = float("-inf")
        self._last_seen = float("-inf")
        self._prev_scroll: tuple[float, float] | None = None
        self._cursor_active = False
        self._handedness: str | None = None
        self.state = HandState()
        self.configure(hand, cursor, tracking)

    # ----------------------------------------------------------------- config
    def configure(self, hand: HandGestureSettings, cursor: CursorSettings, tracking: TrackingSettings) -> None:
        self.hs, self.cs, self.ts = hand, cursor, tracking
        self._pose.min_frames = hand.pose_min_frames
        self._zoom_pose.min_frames = hand.pose_min_frames
        self._click_cd.seconds = hand.click_cooldown_ms / 1000
        self._right_cd.seconds = hand.right_click_cooldown_ms / 1000
        self._pause_cd.seconds = hand.pause_cooldown_ms / 1000
        self._swipe_cd.seconds = hand.swipe_cooldown_ms / 1000
        self._cursor_filter.configure(cursor.smoothing_min_cutoff, cursor.smoothing_beta)

    def reset(self) -> None:
        self._cursor_filter.reset()
        self._scroll_filter.reset()
        self._three_filter.reset()
        self._zoom_filter.reset()
        self._prev_three = None
        self._prev_zoom = None
        self._volume_steps.reset()
        self._zoom_steps.reset()
        self._pose.reset(Pose.NONE)
        self._zoom_pose.reset(False)
        self._left.reset()
        self._right.reset()
        self._palm.reset()
        self._palm_latched = False
        self._palm_hist.clear()
        self._three_hist.clear()
        self._pinch_closed_at = None
        self._dragging = False
        self._prev_scroll = None
        self._cursor_active = False
        self._handedness = None
        self.state = HandState()

    # ---------------------------------------------------------------- helpers
    def select_hand(self, hands: list[HandObservation]) -> int | None:
        if not hands:
            return None
        pref = self.ts.dominant_hand
        candidates = list(range(len(hands)))
        if pref != "any":
            want = pref.capitalize()
            candidates = [i for i in candidates if hands[i].handedness == want]
            if not candidates:
                return None
        # Stick with the hand we were already following when both are visible.
        if self._handedness is not None:
            for i in candidates:
                if hands[i].handedness == self._handedness:
                    return i
        return max(candidates, key=lambda i: hands[i].score)

    def map_to_screen(self, x: float, y: float) -> tuple[float, float]:
        c = self.cs
        u = (x - c.region_left) / max(1e-6, c.region_right - c.region_left)
        v = (y - c.region_top) / max(1e-6, c.region_bottom - c.region_top)
        u = 0.5 + (u - 0.5) * c.speed
        v = 0.5 + (v - 0.5) * c.speed
        return min(1.0, max(0.0, u)), min(1.0, max(0.0, v))

    def _end_drag(self, now: float, events: list[GestureEvent]) -> None:
        if self._dragging:
            self._dragging = False
            events.append(GestureEvent(HandGesture.DRAG_END.value, now, {}, "Drop"))

    def _click(self, now: float, events: list[GestureEvent]) -> None:
        if not self._click_cd.ready(now):
            return
        self._click_cd.trigger(now)
        quick = (now - self._last_click_t) <= self.hs.double_click_window_ms / 1000
        self._click_count = 2 if quick and self._click_count == 1 else 1
        self._last_click_t = now
        events.append(GestureEvent(HandGesture.PINCH.value, now, {"count": self._click_count},
                                   "Double click" if self._click_count == 2 else "Left click"))

    # ----------------------------------------------------------------- update
    def update(self, tf: TrackingFrame) -> list[GestureEvent]:
        now = tf.timestamp
        events: list[GestureEvent] = []

        zoom = self._update_zoom(tf, now, events)
        if zoom is not None:
            return events

        idx = self.select_hand(tf.hands)
        if idx is None:
            if now - self._last_seen > self.hs.lost_reset_ms / 1000:
                self._end_drag(now, events)  # never leave the button pressed
                if self.state.visible or self._cursor_active or self._left.engaged:
                    self.reset()
            # New snapshot (never mutate one the UI thread may be reading).
            self.state = replace(self.state, visible=False, mode="idle", last_events=[e.label for e in events],
                                 cursor_frame=None, cursor_screen=None, dragging=self._dragging)
            return events

        self._last_seen = now
        hand = tf.hands[idx]
        self._handedness = hand.handedness
        f = compute(hand)
        hs = self.hs

        # ---- pinch candidates (with fist / resting-thumb guards)
        left_close = (f.thumb_index < hs.pinch_on_ratio
                      and f.thumb_middle >= hs.pinch_separation * f.thumb_index
                      and f.reach[0] >= MIN_INDEX_REACH_FOR_PINCH)
        left_open = f.thumb_index > hs.pinch_off_ratio
        right_close = (f.thumb_middle < hs.pinch_on_ratio
                       and f.thumb_index >= hs.pinch_separation * f.thumb_middle
                       and f.reach[1] >= MIN_MIDDLE_REACH_FOR_PINCH)
        right_open = f.thumb_middle > hs.pinch_off_ratio
        pinching = (self._left.engaged or self._right.engaged or left_close or right_close)

        # ---- stable pose (frozen while a pinch is forming: pinching bends the index)
        if not pinching:
            self._pose.update(f.pose)
        pose = self._pose.value
        clutch = pose == Pose.FIST

        left_ev = self._left.update(left_close, left_open, hs.pinch_min_frames)
        right_ev = self._right.update(right_close, right_open, hs.pinch_min_frames)

        # ---- left pinch: click, or hold to drag
        if left_ev == "closed" and not clutch:
            if hs.drag_enabled:
                self._pinch_closed_at = now  # decide on release (click) or after the hold (drag)
            else:
                self._click(now, events)
        if (self._pinch_closed_at is not None and not self._dragging
                and self._left.phase == PinchPhase.CLOSED
                and now - self._pinch_closed_at >= hs.drag_hold_ms / 1000):
            self._pinch_closed_at = None
            self._dragging = True
            events.append(GestureEvent(HandGesture.DRAG_START.value, now, {}, "Drag"))
        if left_ev == "opened":
            if self._dragging:
                self._end_drag(now, events)
                self._last_click_t = now  # brief freeze so the drop lands where released
                self._click_count = 0
            elif self._pinch_closed_at is not None:
                self._pinch_closed_at = None
                if not clutch:
                    self._click(now, events)
        if right_ev == "closed" and not clutch and not self._dragging and self._right_cd.ready(now):
            self._right_cd.trigger(now)
            self._last_click_t = now
            self._click_count = 0
            events.append(GestureEvent(HandGesture.MIDDLE_PINCH.value, now, {}, "Right click"))

        # ---- cursor (also moves while dragging)
        mode = "idle"
        frozen = False
        cursor_frame = cursor_screen = None
        if clutch and not self._dragging:
            mode = "clutch"
        elif pose == Pose.POINT or self._dragging or (pinching and self._cursor_active):
            mode = "drag" if self._dragging else "cursor"
            anchor = f.index_tip if self.cs.anchor == "index_tip" else f.index_mcp
            if not self._cursor_active:
                self._cursor_filter.reset()
            freeze_ratio = self.cs.freeze_ratio
            frozen = self.cs.freeze_on_pinch and not self._dragging and (
                pinching
                or (f.thumb_index < freeze_ratio and f.thumb_middle >= hs.pinch_separation * f.thumb_index)
                or (now - self._last_click_t) < self.cs.post_click_freeze_ms / 1000
            )
            if not frozen:
                sx, sy = self._cursor_filter(anchor[0], anchor[1], now)
                cursor_frame = (sx, sy)
                cursor_screen = self.map_to_screen(sx, sy)
                events.append(GestureEvent(HandGesture.CURSOR.value, now,
                                           {"x": cursor_screen[0], "y": cursor_screen[1]},
                                           "Cursor", continuous=True))
            else:
                cursor_frame = self.state.cursor_frame
                cursor_screen = self.state.cursor_screen
            self._cursor_active = True
        else:
            self._cursor_active = False

        # ---- scroll
        if pose == Pose.TWO and not clutch and not pinching:
            mode = "scroll"
            sx, sy = self._scroll_filter(f.two_tip[0], f.two_tip[1], now)
            if self._prev_scroll is not None:
                dx, dy = sx - self._prev_scroll[0], sy - self._prev_scroll[1]
                sign = -1.0 if hs.scroll_invert else 1.0
                out_dx = out_dy = 0.0
                # Only the dominant axis scrolls, to avoid diagonal noise.
                if abs(dy) >= abs(dx) and abs(dy) > hs.scroll_dead_zone:
                    out_dy = -dy * hs.scroll_speed * sign  # hand up -> scroll up (+)
                elif abs(dx) > abs(dy) and abs(dx) > hs.scroll_dead_zone:
                    out_dx = dx * hs.scroll_speed * sign  # hand right -> scroll right (+)
                if out_dx or out_dy:
                    events.append(GestureEvent(HandGesture.SCROLL.value, now,
                                               {"dx": out_dx, "dy": out_dy}, "Scroll", continuous=True))
            self._prev_scroll = (sx, sy)
        else:
            self._prev_scroll = None
            self._scroll_filter.reset()

        # ---- three fingers: vertical = volume steps, fast horizontal swipe = window snap
        if pose == Pose.THREE and not clutch and not pinching:
            mode = "volume"
            tx, ty = self._three_filter(f.two_tip[0], f.two_tip[1], now)
            self._three_hist.append((now, f.two_tip[0], f.two_tip[1]))
            while self._three_hist and now - self._three_hist[0][0] > hs.swipe_window_ms / 1000:
                self._three_hist.popleft()
            swipe = self._detect_swipe(self._three_hist, now, HandGesture.THREE_SWIPE_LEFT,
                                       HandGesture.THREE_SWIPE_RIGHT, "Three-finger swipe")
            if swipe:
                events.append(swipe)
                self._three_hist.clear()
                self._volume_steps.reset()
            elif self._prev_three is not None:
                dx, dy = tx - self._prev_three[0], ty - self._prev_three[1]
                if abs(dy) > hs.scroll_dead_zone and abs(dy) >= abs(dx):  # vertical only
                    n = self._volume_steps.feed(-dy * hs.volume_steps, hs.volume_max_steps_per_frame)
                    for _ in range(abs(n)):
                        g, label = ((HandGesture.VOLUME_UP, "Volume up") if n > 0
                                    else (HandGesture.VOLUME_DOWN, "Volume down"))
                        events.append(GestureEvent(g.value, now, {}, label))
            self._prev_three = (tx, ty)
        else:
            self._prev_three = None
            self._volume_steps.reset()
            self._three_filter.reset()
            self._three_hist.clear()

        # ---- open palm: swipe and hold (off briefly after a two-hand zoom)
        palm_progress = 0.0
        raw_open = f.pose == Pose.OPEN
        if raw_open and not pinching and now >= self._zoom_until:
            if mode == "idle":
                mode = "palm"
            px, py = f.palm_center
            self._palm_hist.append((now, px, py))
            window = hs.swipe_window_ms / 1000
            while self._palm_hist and now - self._palm_hist[0][0] > window:
                self._palm_hist.popleft()
            swipe = self._detect_swipe(self._palm_hist, now, HandGesture.SWIPE_LEFT, HandGesture.SWIPE_RIGHT,
                                       "Swipe")
            if swipe:
                events.append(swipe)
                self._palm.reset()
                self._palm_hist.clear()
            speed = self._palm_speed()
            still = speed is not None and speed < hs.palm_still_speed
            held = self._palm.update(pose == Pose.OPEN and still, now)
            palm_progress = min(1.0, held / (hs.palm_hold_ms / 1000))
            if palm_progress >= 1.0 and not self._palm_latched and self._pause_cd.ready(now):
                self._pause_cd.trigger(now)
                self._palm_latched = True
                events.append(GestureEvent(HandGesture.PALM_HOLD.value, now, {}, "Palm hold: pause / resume"))
        else:
            self._palm.reset()
            self._palm_hist.clear()
            self._palm_latched = False

        self.state = HandState(
            visible=True, hand_index=idx, handedness=hand.handedness, score=hand.score,
            pose=pose, raw_pose=f.pose, features=f, mode=mode,
            cursor_frame=cursor_frame, cursor_screen=cursor_screen, frozen=frozen,
            left_pinch=self._left.phase.value, right_pinch=self._right.phase.value,
            palm_progress=palm_progress if not self._palm_latched else 1.0,
            dragging=self._dragging,
            last_events=[e.label for e in events if not e.continuous],
        )
        return events

    # ------------------------------------------------------------- two hands
    def _update_zoom(self, tf: TrackingFrame, now: float, events: list[GestureEvent]):
        """Two open hands: spreading them zooms in, bringing them together zooms out.

        Returns None when not zooming (the single-hand pipeline then runs).
        """
        hs = self.hs
        both_open = False
        feats: list[HandFeatures] = []
        if hs.zoom_enabled and len(tf.hands) >= 2 and not self._dragging:
            top2 = sorted(range(len(tf.hands)), key=lambda i: tf.hands[i].score, reverse=True)[:2]
            feats = [compute(tf.hands[i]) for i in top2]
            both_open = all(fe.pose == Pose.OPEN for fe in feats)
        self._zoom_pose.update(both_open)
        if not (self._zoom_pose.value and len(feats) == 2):
            if self._prev_zoom is not None:  # leaving zoom mode
                self._prev_zoom = None
                self._zoom_filter.reset()
                self._zoom_steps.reset()
                self._zoom_pose.reset(False)
            return None
        (ax, ay), (bx, by) = feats[0].palm_center, feats[1].palm_center
        d = self._zoom_filter(((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5, now)
        if self._prev_zoom is not None:
            dd = d - self._prev_zoom
            if abs(dd) > hs.scroll_dead_zone:
                n = self._zoom_steps.feed(dd * hs.zoom_steps, hs.zoom_max_steps_per_frame)
                for _ in range(abs(n)):
                    g, label = (HandGesture.ZOOM_IN, "Zoom in") if n > 0 else (HandGesture.ZOOM_OUT, "Zoom out")
                    events.append(GestureEvent(g.value, now, {}, label))
        self._prev_zoom = d
        # Single-hand gestures that use an open palm are suspended while zooming and shortly after.
        self._zoom_until = now + ZOOM_AFTERGLOW_S
        self._palm.reset()
        self._palm_hist.clear()
        self._palm_latched = False
        self._cursor_active = False
        self._last_seen = now
        self.state = HandState(visible=True, hand_index=None, handedness="Both", score=min(
            h.score for h in tf.hands[:2]), pose=Pose.OPEN, raw_pose=Pose.OPEN, features=feats[0], mode="zoom",
            last_events=[e.label for e in events])
        return True

    # --------------------------------------------------------------- helpers
    def _palm_speed(self) -> float | None:
        """Palm speed over the last ~150 ms, in frame-widths per second."""
        if len(self._palm_hist) < 2:
            return None
        t1, x1, y1 = self._palm_hist[-1]
        for t0, x0, y0 in reversed(self._palm_hist):
            if t1 - t0 >= 0.15:
                break
        if t1 - t0 <= 0:
            return None
        return ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5 / (t1 - t0)

    def _detect_swipe(self, hist, now: float, left: HandGesture, right: HandGesture, label: str):
        if len(hist) < 3 or not self._swipe_cd.ready(now):
            return None
        xs = [x for _, x, _ in hist]
        ys = [y for _, _, y in hist]
        dx = xs[-1] - xs[0]
        dy = max(ys) - min(ys)
        if abs(dx) < self.hs.swipe_min_distance or dy > abs(dx) * 0.6:
            return None
        # Require mostly monotonic motion (rejects shaking / waving).
        steps = [b - a for a, b in zip(xs, xs[1:])]
        agree = sum(1 for s in steps if s * dx > 0) / max(1, len(steps))
        if agree < 0.7:
            return None
        self._swipe_cd.trigger(now)
        if dx > 0:
            return GestureEvent(right.value, now, {"distance": dx}, f"{label} right")
        return GestureEvent(left.value, now, {"distance": -dx}, f"{label} left")
