"""Head gesture engine: head pose stream -> GestureEvents.

To keep ordinary head movement from triggering actions, a gesture fires only if
ALL of the following hold:

1. The engine is *armed*: the head has rested inside the neutral zone
   (|angle| < rearm_ratio x threshold on every axis) for `rearm_ms`.
   After any gesture — and after the face is lost — the engine disarms, so
   the head must come back to neutral before anything else can fire.
2. One axis clearly dominates: its normalized deflection is >= 1 and at least
   `dominance_ratio` times the next largest (rejects diagonal/look-around motion).
3. That deflection persists for `min_duration_ms`.
4. The cooldown since the previous gesture has elapsed.

Angles are relative to the calibrated neutral pose.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config.settings import HeadGesture, HeadGestureSettings
from ..core.types import GestureEvent, HeadPose, TrackingFrame
from .gesture_state import Cooldown, HoldTimer

_LABELS = {
    HeadGesture.TURN_LEFT: "Head turn left",
    HeadGesture.TURN_RIGHT: "Head turn right",
    HeadGesture.NOD_DOWN: "Nod down",
    HeadGesture.TILT_UP: "Tilt up",
    HeadGesture.ROLL_LEFT: "Head tilt left",
    HeadGesture.ROLL_RIGHT: "Head tilt right",
}


@dataclass(slots=True)
class HeadState:
    visible: bool = False
    yaw: float = 0.0  # relative to neutral, degrees (after inversion settings)
    pitch: float = 0.0
    roll: float = 0.0
    raw: HeadPose | None = None  # absolute, smoothed
    armed: bool = False
    candidate: str = ""
    progress: float = 0.0  # 0..1 toward firing the candidate
    neutral_progress: float = 0.0  # 0..1 toward re-arming
    cooling: bool = False


class HeadGestureEngine:
    def __init__(self, settings: HeadGestureSettings) -> None:
        self._smoothed: HeadPose | None = None
        self._hold = HoldTimer()
        self._neutral = HoldTimer()
        self._cooldown = Cooldown(0.9)
        self._candidate: HeadGesture | None = None
        self._armed = False
        self.state = HeadState()
        self.configure(settings)

    def configure(self, settings: HeadGestureSettings) -> None:
        self.s = settings
        self._cooldown.seconds = settings.cooldown_ms / 1000

    def reset(self) -> None:
        self._smoothed = None
        self._hold.reset()
        self._neutral.reset()
        self._candidate = None
        self._armed = False
        self.state = HeadState()

    def relative(self, pose: HeadPose) -> tuple[float, float, float]:
        s = self.s
        yaw = pose.yaw - s.neutral_yaw
        pitch = pose.pitch - s.neutral_pitch
        roll = pose.roll - s.neutral_roll
        if s.invert_yaw:
            yaw, roll = -yaw, -roll
        if s.invert_pitch:
            pitch = -pitch
        return yaw, pitch, roll

    def _classify(self, yaw: float, pitch: float, roll: float) -> tuple[HeadGesture | None, float, float]:
        """Returns (dominant gesture or None, its normalized magnitude, max magnitude)."""
        s = self.s
        n_yaw = abs(yaw) / s.yaw_threshold_deg
        n_pitch = abs(pitch) / (s.pitch_down_threshold_deg if pitch > 0 else s.pitch_up_threshold_deg)
        n_roll = abs(roll) / s.roll_threshold_deg
        ranked = sorted(((n_yaw, "yaw"), (n_pitch, "pitch"), (n_roll, "roll")), reverse=True)
        (top, axis), (second, _) = ranked[0], ranked[1]
        if top < 1.0 or top < s.dominance_ratio * second:
            return None, top, top
        if axis == "yaw":
            g = HeadGesture.TURN_RIGHT if yaw > 0 else HeadGesture.TURN_LEFT
        elif axis == "pitch":
            g = HeadGesture.NOD_DOWN if pitch > 0 else HeadGesture.TILT_UP
        else:
            g = HeadGesture.ROLL_RIGHT if roll > 0 else HeadGesture.ROLL_LEFT
        return g, top, top

    def update(self, tf: TrackingFrame) -> list[GestureEvent]:
        now = tf.timestamp
        pose = tf.face.pose if tf.face is not None else None
        if pose is None:
            if self.state.visible:
                self.reset()  # disarm: must see neutral again after re-acquiring
            return []

        a = self.s.smoothing
        if self._smoothed is None:
            self._smoothed = HeadPose(pose.yaw, pose.pitch, pose.roll)
        else:
            sm = self._smoothed
            self._smoothed = HeadPose(a * sm.yaw + (1 - a) * pose.yaw,
                                      a * sm.pitch + (1 - a) * pose.pitch,
                                      a * sm.roll + (1 - a) * pose.roll)
        yaw, pitch, roll = self.relative(self._smoothed)
        s = self.s

        # Neutral zone / re-arming
        in_neutral = (abs(yaw) < s.rearm_ratio * s.yaw_threshold_deg
                      and abs(pitch) < s.rearm_ratio * min(s.pitch_down_threshold_deg, s.pitch_up_threshold_deg)
                      and abs(roll) < s.rearm_ratio * s.roll_threshold_deg)
        neutral_for = self._neutral.update(in_neutral, now)
        if not self._armed and neutral_for >= s.rearm_ms / 1000 and self._cooldown.ready(now):
            self._armed = True

        events: list[GestureEvent] = []
        gesture, _, _ = self._classify(yaw, pitch, roll)
        if gesture != self._candidate:
            self._candidate = gesture
            self._hold.reset()
        held = self._hold.update(gesture is not None, now)
        need = s.min_duration_ms / 1000
        progress = 0.0
        if gesture is not None and self._armed:
            progress = 1.0 if need <= 0 else min(1.0, held / need)
            if held >= need and self._cooldown.ready(now):
                events.append(GestureEvent(gesture.value, now,
                                           {"yaw": yaw, "pitch": pitch, "roll": roll},
                                           _LABELS[gesture]))
                self._armed = False
                self._cooldown.trigger(now)
                self._neutral.reset()

        self.state = HeadState(
            visible=True, yaw=yaw, pitch=pitch, roll=roll, raw=self._smoothed,
            armed=self._armed, candidate=_LABELS[gesture] if gesture else "",
            progress=progress,
            neutral_progress=1.0 if self._armed else (
                min(1.0, neutral_for / (s.rearm_ms / 1000)) if s.rearm_ms else 1.0),
            cooling=not self._cooldown.ready(now),
        )
        return events
