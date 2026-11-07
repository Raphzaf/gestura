"""Hand gesture engine: TrackingFrame stream -> GestureEvents.

Design rules
------------
* No gesture fires from a single frame: poses are debounced, pinches need
  `pinch_min_frames`, holds need time, swipes need distance within a window.
* Hysteresis on every threshold (pinch closes below `pinch_on_ratio`, opens
  above `pinch_off_ratio`).
* Losing the hand resets all transient state so nothing stays "pressed".
* A fist is a clutch: while held, the hand produces no events at all.
* The engine only *describes* gestures. It never touches the OS.

Interaction model
-----------------
POINT (index extended)            -> hand.cursor (continuous, smoothed)
thumb+index pinch                 -> hand.pinch (count=1, or 2 for a quick second pinch)
thumb+middle pinch                -> hand.middle_pinch
TWO (index+middle extended) move  -> hand.scroll (continuous, dx/dy in notches)
THREE (index+middle+ring) up/down -> hand.volume_up / hand.volume_down (one event per step)
OPEN palm, fast horizontal move   -> hand.swipe_left / hand.swipe_right
OPEN palm held still              -> hand.palm_hold
FIST                              -> clutch (nothing)

A double click is produced by two single clicks within the OS double-click
interval, exactly like a physical mouse. The second quick pinch is labelled
"Double click" (count=2) for feedback, but executes as one more click.
"""

from __future__ import annotations

import enum
from collections import deque
from dataclasses import dataclass, field, replace

from ..config.settings import CursorSettings, HandGesture, HandGestureSettings, TrackingSettings
from ..core.types import GestureEvent, HandObservation, TrackingFrame
from .filters import OneEuro2D
from .gesture_state import Cooldown, Debounced, HoldTimer
from .hand_features import HandFeatures, Pose, compute

# Guards measured on sample photos (see docs/GESTURES.md):
MIN_INDEX_REACH_FOR_PINCH = 0.55  # a fist has index reach ~0.49
MIN_MIDDLE_REACH_FOR_PINCH = 0.60  # pointing with thumb on middle has ~0.46


class PinchPhase(str, enum.Enum):
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"


class _Pinch:
    def __init__(self) -> None:
        self.phase = PinchPhase.OPEN
        self.frames = 0

    def update(self, close_cond: bool, open_cond: bool, min_frames: int) -> bool:
        """Returns True on the frame the pinch becomes CLOSED."""
        if self.phase == PinchPhase.CLOSED:
            if open_cond:
                self.phase, self.frames = PinchPhase.OPEN, 0
            return False
        if close_cond:
            self.frames += 1
            self.phase = PinchPhase.CLOSING
            if self.frames >= min_frames:
                self.phase = PinchPhase.CLOSED
                return True
        else:
            self.phase, self.frames = PinchPhase.OPEN, 0
        return False

    @property
    def engaged(self) -> bool:
        return self.phase != PinchPhase.OPEN

    def reset(self) -> None:
        self.phase, self.frames = PinchPhase.OPEN, 0


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
    mode: str = "idle"  # idle | cursor | scroll | volume | palm | clutch
    cursor_frame: tuple[float, float] | None = None  # smoothed anchor, frame coords
    cursor_screen: tuple[float, float] | None = None  # 0..1 screen coords
    frozen: bool = False
    left_pinch: str = "open"
    right_pinch: str = "open"
    palm_progress: float = 0.0
    last_events: list[str] = field(default_factory=list)


class HandGestureEngine:
    def __init__(self, hand: HandGestureSettings, cursor: CursorSettings, tracking: TrackingSettings) -> None:
        self._cursor_filter = OneEuro2D()
        self._scroll_filter = OneEuro2D(min_cutoff=3.0, beta=0.0)
        self._volume_filter = OneEuro2D(min_cutoff=3.0, beta=0.0)
        self._prev_volume: float | None = None
        self._volume_acc = 0.0
        self._pose = Debounced(Pose.NONE, 3)
        self._left = _Pinch()
        self._right = _Pinch()
        self._click_cd = Cooldown(0.1)
        self._right_cd = Cooldown(0.6)
        self._pause_cd = Cooldown(2.0)
        self._swipe_cd = Cooldown(1.0)
        self._palm = HoldTimer()
        self._palm_latched = False
        self._palm_hist: deque[tuple[float, float, float]] = deque()  # (t, x, y)
        self._last_click_t = float("-inf")
        self._click_count = 0
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
        self._click_cd.seconds = hand.click_cooldown_ms / 1000
        self._right_cd.seconds = hand.right_click_cooldown_ms / 1000
        self._pause_cd.seconds = hand.pause_cooldown_ms / 1000
        self._swipe_cd.seconds = hand.swipe_cooldown_ms / 1000
        self._cursor_filter.configure(cursor.smoothing_min_cutoff, cursor.smoothing_beta)

    def reset(self) -> None:
        self._cursor_filter.reset()
        self._scroll_filter.reset()
        self._pose.reset(Pose.NONE)
        self._left.reset()
        self._right.reset()
        self._palm.reset()
        self._palm_latched = False
        self._palm_hist.clear()
        self._prev_scroll = None
        self._volume_filter.reset()
        self._prev_volume = None
        self._volume_acc = 0.0
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

    # ----------------------------------------------------------------- update
    def update(self, tf: TrackingFrame) -> list[GestureEvent]:
        now = tf.timestamp
        events: list[GestureEvent] = []
        idx = self.select_hand(tf.hands)

        if idx is None:
            if now - self._last_seen > self.hs.lost_reset_ms / 1000:
                if self.state.visible or self._cursor_active or self._left.engaged:
                    self.reset()
            # New snapshot (never mutate one the UI thread may be reading).
            self.state = replace(self.state, visible=False, mode="idle", last_events=[],
                                 cursor_frame=None, cursor_screen=None)
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

        left_fired = self._left.update(left_close, left_open, hs.pinch_min_frames)
        right_fired = self._right.update(right_close, right_open, hs.pinch_min_frames)

        # ---- clicks
        if left_fired and not clutch and self._click_cd.ready(now):
            self._click_cd.trigger(now)
            quick = (now - self._last_click_t) <= hs.double_click_window_ms / 1000
            self._click_count = 2 if quick and self._click_count == 1 else 1
            self._last_click_t = now
            events.append(GestureEvent(
                HandGesture.PINCH.value, now, {"count": self._click_count},
                "Double click" if self._click_count == 2 else "Left click"))
        if right_fired and not clutch and self._right_cd.ready(now):
            self._right_cd.trigger(now)
            self._last_click_t = now
            self._click_count = 0
            events.append(GestureEvent(HandGesture.MIDDLE_PINCH.value, now, {}, "Right click"))

        # ---- cursor
        mode = "idle"
        frozen = False
        cursor_frame = cursor_screen = None
        if clutch:
            mode = "clutch"
        elif pose == Pose.POINT or (pinching and self._cursor_active):
            mode = "cursor"
            anchor = f.index_tip if self.cs.anchor == "index_tip" else f.index_mcp
            if not self._cursor_active:
                self._cursor_filter.reset()
            freeze_ratio = self.cs.freeze_ratio
            frozen = self.cs.freeze_on_pinch and (
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

        # ---- volume: three fingers, vertical movement; each step is one volume key press
        if pose == Pose.THREE and not clutch and not pinching:
            mode = "volume"
            _, vy = self._volume_filter(f.two_tip[0], f.two_tip[1], now)
            if self._prev_volume is not None:
                dy = vy - self._prev_volume
                if abs(dy) > hs.scroll_dead_zone:
                    self._volume_acc += -dy * hs.volume_steps  # hand up -> louder
                steps = 0
                while self._volume_acc >= 1 and steps < hs.volume_max_steps_per_frame:
                    self._volume_acc -= 1
                    steps += 1
                    events.append(GestureEvent(HandGesture.VOLUME_UP.value, now, {}, "Volume up"))
                while self._volume_acc <= -1 and steps < hs.volume_max_steps_per_frame:
                    self._volume_acc += 1
                    steps += 1
                    events.append(GestureEvent(HandGesture.VOLUME_DOWN.value, now, {}, "Volume down"))
                # Don't bank a long backlog: excess movement beyond the per-frame cap is dropped.
                self._volume_acc = max(-0.999, min(0.999, self._volume_acc))
            self._prev_volume = vy
        else:
            self._prev_volume = None
            self._volume_acc = 0.0
            self._volume_filter.reset()

        # ---- open palm: swipe and hold
        palm_progress = 0.0
        raw_open = f.pose == Pose.OPEN
        if raw_open and not pinching:
            if mode == "idle":
                mode = "palm"
            px, py = f.palm_center
            self._palm_hist.append((now, px, py))
            window = hs.swipe_window_ms / 1000
            while self._palm_hist and now - self._palm_hist[0][0] > window:
                self._palm_hist.popleft()
            swipe = self._detect_swipe(now)
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
            last_events=[e.label for e in events if not e.continuous],
        )
        return events

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

    def _detect_swipe(self, now: float) -> GestureEvent | None:
        if len(self._palm_hist) < 3 or not self._swipe_cd.ready(now):
            return None
        xs = [x for _, x, _ in self._palm_hist]
        ys = [y for _, _, y in self._palm_hist]
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
            return GestureEvent(HandGesture.SWIPE_RIGHT.value, now, {"distance": dx}, "Swipe right")
        return GestureEvent(HandGesture.SWIPE_LEFT.value, now, {"distance": -dx}, "Swipe left")
