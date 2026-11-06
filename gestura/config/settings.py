"""Validated application settings.

This module is the single source of truth for every tunable value in Gestura.
`config/default_settings.json` is generated from these defaults
(``python -m gestura.config.settings``) and a test asserts the two never drift.

Every numeric field carries bounds and a human-readable title so the Settings
screen can be generated from the model instead of being hand-maintained.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class _Section(BaseModel):
    model_config = ConfigDict(extra="ignore", validate_assignment=True)


class CameraSettings(_Section):
    index: int = Field(0, ge=0, le=9, title="Camera index")
    width: int = Field(640, ge=160, le=1920, title="Capture width (px)")
    height: int = Field(480, ge=120, le=1080, title="Capture height (px)")
    fps: int = Field(30, ge=5, le=60, title="Requested FPS")
    mirror: bool = Field(True, title="Mirror preview (selfie view)")
    backend: Literal["auto", "dshow", "msmf", "any"] = Field(
        "auto", title="Capture backend (Windows)"
    )


class TrackingSettings(_Section):
    hands_enabled: bool = Field(True, title="Hand tracking")
    face_enabled: bool = Field(True, title="Face / head tracking")
    num_hands: int = Field(2, ge=1, le=2, title="Max hands")
    dominant_hand: Literal["right", "left", "any"] = Field("right", title="Control hand")
    min_hand_detection_confidence: float = Field(0.6, ge=0.1, le=0.95, title="Hand detection confidence")
    min_hand_presence_confidence: float = Field(0.5, ge=0.1, le=0.95, title="Hand presence confidence")
    min_tracking_confidence: float = Field(0.5, ge=0.1, le=0.95, title="Tracking confidence")
    min_face_detection_confidence: float = Field(0.5, ge=0.1, le=0.95, title="Face detection confidence")
    parallel_inference: bool = Field(True, title="Run hand and face models in parallel")


class CursorSettings(_Section):
    anchor: Literal["index_tip", "index_mcp"] = Field("index_tip", title="Cursor anchor point")
    # Region of the (mirrored) camera image mapped onto the whole screen, normalized 0..1.
    region_left: float = Field(0.18, ge=0.0, le=0.45, title="Active region left")
    region_right: float = Field(0.82, ge=0.55, le=1.0, title="Active region right")
    region_top: float = Field(0.12, ge=0.0, le=0.45, title="Active region top")
    region_bottom: float = Field(0.70, ge=0.55, le=1.0, title="Active region bottom")
    speed: float = Field(1.0, ge=0.3, le=3.0, title="Cursor speed")
    smoothing_min_cutoff: float = Field(1.0, ge=0.05, le=10.0, title="Smoothing (lower = smoother)")
    smoothing_beta: float = Field(5.0, ge=0.0, le=30.0, title="Responsiveness to fast moves")
    dead_zone_px: int = Field(2, ge=0, le=30, title="Dead zone (px)")
    freeze_on_pinch: bool = Field(True, title="Freeze cursor while pinching")
    freeze_ratio: float = Field(0.40, ge=0.1, le=1.0, title="Freeze when pinch ratio below")
    post_click_freeze_ms: int = Field(150, ge=0, le=1000, title="Freeze after click (ms)")


class HandGestureSettings(_Section):
    pose_min_frames: int = Field(3, ge=1, le=15, title="Frames for a stable pose")
    pinch_on_ratio: float = Field(0.25, ge=0.05, le=0.8, title="Pinch closes below ratio")
    pinch_off_ratio: float = Field(0.38, ge=0.1, le=1.0, title="Pinch opens above ratio")
    pinch_separation: float = Field(1.4, ge=1.0, le=3.0, title="Pinched finger must be this much closer than the next")
    pinch_min_frames: int = Field(2, ge=1, le=10, title="Frames to confirm pinch")
    click_cooldown_ms: int = Field(120, ge=0, le=2000, title="Click cooldown (ms)")
    double_click_window_ms: int = Field(450, ge=150, le=1500, title="Double-click window (ms)")
    right_click_cooldown_ms: int = Field(600, ge=0, le=3000, title="Right-click cooldown (ms)")
    palm_hold_ms: int = Field(1200, ge=300, le=5000, title="Open palm hold to pause (ms)")
    palm_still_speed: float = Field(0.35, ge=0.05, le=2.0, title="Palm must move slower than (screen/s)")
    pause_cooldown_ms: int = Field(2000, ge=500, le=10000, title="Pause toggle cooldown (ms)")
    scroll_speed: float = Field(25.0, ge=1.0, le=200.0, title="Scroll speed (notches per hand height)")
    scroll_dead_zone: float = Field(0.004, ge=0.0, le=0.05, title="Scroll dead zone (per frame)")
    scroll_invert: bool = Field(False, title="Invert scroll direction")
    swipe_min_distance: float = Field(0.22, ge=0.05, le=0.8, title="Swipe min distance (frame width)")
    swipe_window_ms: int = Field(350, ge=100, le=1500, title="Swipe max duration (ms)")
    swipe_cooldown_ms: int = Field(1000, ge=200, le=5000, title="Swipe cooldown (ms)")
    lost_reset_ms: int = Field(250, ge=50, le=3000, title="Reset gestures after hand lost (ms)")


class HeadGestureSettings(_Section):
    yaw_threshold_deg: float = Field(18.0, ge=5.0, le=60.0, title="Turn threshold (deg)")
    pitch_down_threshold_deg: float = Field(13.0, ge=4.0, le=45.0, title="Nod down threshold (deg)")
    pitch_up_threshold_deg: float = Field(13.0, ge=4.0, le=45.0, title="Tilt up threshold (deg)")
    roll_threshold_deg: float = Field(20.0, ge=5.0, le=60.0, title="Side tilt threshold (deg)")
    min_duration_ms: int = Field(220, ge=0, le=2000, title="Hold beyond threshold (ms)")
    cooldown_ms: int = Field(900, ge=0, le=5000, title="Cooldown after gesture (ms)")
    rearm_ratio: float = Field(0.4, ge=0.1, le=0.9, title="Neutral zone (fraction of threshold)")
    rearm_ms: int = Field(150, ge=0, le=2000, title="Time in neutral to re-arm (ms)")
    dominance_ratio: float = Field(1.5, ge=1.0, le=4.0, title="Axis dominance ratio")
    smoothing: float = Field(0.5, ge=0.0, le=0.95, title="Angle smoothing (0 = none)")
    invert_yaw: bool = Field(False, title="Invert left/right")
    invert_pitch: bool = Field(False, title="Invert up/down")
    # Calibrated neutral pose (degrees)
    neutral_yaw: float = Field(0.0, ge=-90, le=90, title="Neutral yaw")
    neutral_pitch: float = Field(0.0, ge=-90, le=90, title="Neutral pitch")
    neutral_roll: float = Field(0.0, ge=-90, le=90, title="Neutral roll")
    calibrated: bool = Field(False, title="Neutral pose calibrated")


class SafetySettings(_Section):
    start_in_test_mode: bool = Field(True, title="Start in test mode (no real actions)")
    confirm_sensitive: bool = Field(True, title="Repeat gesture to confirm sensitive actions")
    confirm_window_ms: int = Field(2500, ge=500, le=10000, title="Confirmation window (ms)")
    pyautogui_failsafe: bool = Field(True, title="Physical mouse to a corner = emergency stop")
    global_hotkey: bool = Field(True, title="Ctrl+Alt+Shift+G emergency hotkey (Windows)")


class KeyboardSettings(_Section):
    layout: Literal["azerty", "qwerty"] = Field("azerty", title="Layout")
    scale: float = Field(1.0, ge=0.6, le=2.0, title="Size")
    opacity: float = Field(0.95, ge=0.4, le=1.0, title="Opacity")
    pos_x: int = Field(-1, ge=-1, le=20000, title="Position X (-1 = auto)")
    pos_y: int = Field(-1, ge=-1, le=20000, title="Position Y (-1 = auto)")


class StartupSettings(_Section):
    auto_start_tracking: bool = Field(False, title="Start camera when Gestura opens")
    start_minimized: bool = Field(False, title="Start minimized")
    open_page: Literal["dashboard", "studio"] = Field("dashboard", title="First page")


class Modes(_Section):
    mouse: bool = Field(True, title="Mouse mode (hand)")
    navigation: bool = Field(False, title="Navigation mode (head)")
    keyboard: bool = Field(False, title="Keyboard mode")


class HandGesture(str, Enum):
    """Discrete or continuous hand gestures that can be mapped to commands."""

    CURSOR = "hand.cursor"
    PINCH = "hand.pinch"
    MIDDLE_PINCH = "hand.middle_pinch"
    SCROLL = "hand.scroll"
    SWIPE_LEFT = "hand.swipe_left"
    SWIPE_RIGHT = "hand.swipe_right"
    PALM_HOLD = "hand.palm_hold"


class HeadGesture(str, Enum):
    TURN_LEFT = "head.turn_left"
    TURN_RIGHT = "head.turn_right"
    NOD_DOWN = "head.nod_down"
    TILT_UP = "head.tilt_up"
    ROLL_LEFT = "head.roll_left"
    ROLL_RIGHT = "head.roll_right"


DEFAULT_HAND_MAPPINGS: dict[str, str] = {
    HandGesture.CURSOR.value: "mouse.move",
    HandGesture.PINCH.value: "mouse.left_click",
    HandGesture.MIDDLE_PINCH.value: "mouse.right_click",
    HandGesture.SCROLL.value: "mouse.scroll",
    HandGesture.SWIPE_LEFT.value: "browser.prev_tab",
    HandGesture.SWIPE_RIGHT.value: "browser.next_tab",
    HandGesture.PALM_HOLD.value: "app.toggle_pause",
}

DEFAULT_HEAD_MAPPINGS: dict[str, str] = {
    HeadGesture.TURN_LEFT.value: "browser.back",
    HeadGesture.TURN_RIGHT.value: "browser.forward",
    HeadGesture.NOD_DOWN.value: "key.enter",
    HeadGesture.TILT_UP.value: "key.escape",
    HeadGesture.ROLL_LEFT.value: "none",
    HeadGesture.ROLL_RIGHT.value: "none",
}


class MappingSettings(_Section):
    hand: dict[str, str] = Field(default_factory=lambda: dict(DEFAULT_HAND_MAPPINGS))
    head: dict[str, str] = Field(default_factory=lambda: dict(DEFAULT_HEAD_MAPPINGS))

    @field_validator("hand")
    @classmethod
    def _complete_hand(cls, v: dict[str, str]) -> dict[str, str]:
        merged = dict(DEFAULT_HAND_MAPPINGS)
        merged.update({k: val for k, val in v.items() if k in DEFAULT_HAND_MAPPINGS})
        return merged

    @field_validator("head")
    @classmethod
    def _complete_head(cls, v: dict[str, str]) -> dict[str, str]:
        merged = dict(DEFAULT_HEAD_MAPPINGS)
        merged.update({k: val for k, val in v.items() if k in DEFAULT_HEAD_MAPPINGS})
        return merged


class Settings(_Section):
    schema_version: int = 1
    camera: CameraSettings = Field(default_factory=CameraSettings)
    tracking: TrackingSettings = Field(default_factory=TrackingSettings)
    cursor: CursorSettings = Field(default_factory=CursorSettings)
    hand: HandGestureSettings = Field(default_factory=HandGestureSettings)
    head: HeadGestureSettings = Field(default_factory=HeadGestureSettings)
    safety: SafetySettings = Field(default_factory=SafetySettings)
    keyboard: KeyboardSettings = Field(default_factory=KeyboardSettings)
    startup: StartupSettings = Field(default_factory=StartupSettings)
    modes: Modes = Field(default_factory=Modes)
    mappings: MappingSettings = Field(default_factory=MappingSettings)

    @model_validator(mode="after")
    def _check_hysteresis(self) -> "Settings":
        if self.hand.pinch_off_ratio <= self.hand.pinch_on_ratio:
            raise ValueError("hand.pinch_off_ratio must be greater than hand.pinch_on_ratio")
        return self

    def copy_deep(self) -> "Settings":
        return self.model_copy(deep=True)


def default_settings_json() -> str:
    return Settings().model_dump_json(indent=2) + "\n"


if __name__ == "__main__":  # pragma: no cover - maintenance helper
    from pathlib import Path

    out = Path(__file__).with_name("default_settings.json")
    out.write_text(default_settings_json(), encoding="utf-8")
    print(f"wrote {out}")
