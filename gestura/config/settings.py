# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
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
    volume_steps: float = Field(30.0, ge=5.0, le=100.0, title="Volume steps per hand height (three fingers)")
    volume_max_steps_per_frame: int = Field(3, ge=1, le=10, title="Max volume steps per frame")
    two_hand_mouse: bool = Field(False, title="Two-hand mouse: control hand moves, other hand clicks")
    drag_enabled: bool = Field(True, title="Pinch and hold to drag (clicks fire on release)")
    drag_hold_ms: int = Field(450, ge=200, le=1500, title="Hold pinch this long to start a drag (ms)")
    zoom_enabled: bool = Field(True, title="Two open hands: spread / bring together to zoom")
    zoom_steps: float = Field(12.0, ge=2.0, le=60.0, title="Zoom steps per frame-width of hand movement")
    zoom_max_steps_per_frame: int = Field(2, ge=1, le=10, title="Max zoom steps per frame")
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


class FaceMouseSettings(_Section):
    """Hands-free mouse: eye tracking, head pointer, winks, blinks, face expressions."""

    pointer: Literal["hybrid", "gaze", "head"] = Field(
        "hybrid", title="Pointer (hybrid = eyes jump, head refines; eyes need calibration)")
    # Head pointer
    head_range_yaw_deg: float = Field(14.0, ge=4.0, le=40.0, title="Head pointer: turn this far to reach the side (deg)")
    head_range_pitch_deg: float = Field(10.0, ge=3.0, le=30.0, title="Head pointer: tilt this far to reach top / bottom (deg)")
    head_smoothing_min_cutoff: float = Field(0.8, ge=0.05, le=10.0, title="Head pointer smoothing (lower = smoother)")
    head_smoothing_beta: float = Field(4.0, ge=0.0, le=30.0, title="Head pointer responsiveness to fast moves")
    # Eye (gaze) pointer
    gaze_smoothing_min_cutoff: float = Field(0.35, ge=0.05, le=5.0, title="Eye pointer smoothing (lower = smoother)")
    gaze_smoothing_beta: float = Field(1.5, ge=0.0, le=20.0, title="Eye pointer responsiveness to fast moves")
    gaze_fixation_radius: float = Field(0.035, ge=0.0, le=0.2, title="Eye pointer ignores movements smaller than (screen fraction)")
    screen_half_angle_deg: float = Field(22.0, ge=8.0, le=45.0, title="Half the screen width seen from your eyes (deg)")
    hybrid_jump_distance: float = Field(0.15, ge=0.05, le=0.5, title="Hybrid: look this far from the pointer to move it there (screen fraction)")
    hybrid_jump_ms: int = Field(250, ge=50, le=2000, title="Hybrid: look there this long (ms)")
    hybrid_head_gain: float = Field(0.6, ge=0.1, le=3.0, title="Hybrid: head fine-tuning speed")
    # Eyes
    eye_close_ratio: float = Field(0.55, ge=0.2, le=0.9, title="Eye counts as closed below this fraction of its open size")
    eye_open_ratio: float = Field(0.75, ge=0.3, le=1.0, title="Eye counts as open again above this fraction")
    wink_other_eye_ratio: float = Field(0.65, ge=0.3, le=1.0, title="Wink: the other eye must stay open above this fraction")
    wink_min_ms: int = Field(150, ge=50, le=1000, title="Wink: keep one eye closed at least (ms)")
    long_wink_ms: int = Field(800, ge=300, le=3000, title="Long wink: keep one eye closed (ms)")
    long_blink_ms: int = Field(600, ge=300, le=3000, title="Long blink: both eyes closed at least (ms)")
    double_blink_min_ms: int = Field(180, ge=80, le=600, title="Double blink: each blink at least (ms)")
    double_blink_window_ms: int = Field(700, ge=200, le=2000, title="Double blink: second blink within (ms)")
    eyes_closed_hold_ms: int = Field(2000, ge=800, le=10000, title="Eyes closed hold (ms)")
    freeze_on_blink: bool = Field(True, title="Freeze the pointer while an eye closes")
    # Face expressions
    mouth_open_ratio: float = Field(0.35, ge=0.1, le=1.0, title="Mouth open: lip gap / mouth width above")
    smile_ratio: float = Field(1.12, ge=1.02, le=1.6, title="Smile: mouth wider than neutral by")
    brow_raise_ratio: float = Field(1.18, ge=1.05, le=1.8, title="Eyebrows raised: higher than neutral by")
    expression_hold_ms: int = Field(300, ge=50, le=3000, title="Hold an expression (ms)")
    action_cooldown_ms: int = Field(500, ge=0, le=5000, title="Pause between eye / face actions (ms)")
    # Dwell click and scroll mode
    dwell_click: bool = Field(False, title="Dwell click: keep the pointer still to click")
    dwell_ms: int = Field(1000, ge=300, le=5000, title="Dwell time (ms)")
    dwell_radius: float = Field(0.025, ge=0.005, le=0.15, title="Dwell: pointer stays within (screen fraction)")
    scroll_speed: float = Field(15.0, ge=1.0, le=100.0, title="Scroll mode speed (notches per second)")
    scroll_dead_zone: float = Field(0.05, ge=0.0, le=0.25, title="Scroll mode dead zone (screen fraction)")
    # Eye calibration (written by the calibration screen)
    gaze_model: list[float] = Field(default_factory=list, title="Eye calibration data")
    gaze_error: float = Field(0.0, ge=0.0, le=10.0, title="Measured eye pointer error (screen heights)")


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


class InterfaceSettings(_Section):
    show_overlay: bool = Field(True, title="Show gesture feedback overlay")
    overlay_position: Literal["top", "bottom"] = Field("top", title="Overlay position")


class StartupSettings(_Section):
    launch_at_login: bool = Field(False, title="Launch Gestura when I sign in (Windows)")
    auto_start_tracking: bool = Field(False, title="Start camera when Gestura opens")
    start_minimized: bool = Field(False, title="Start minimized")
    open_page: Literal["dashboard", "studio"] = Field("dashboard", title="First page")


class Modes(_Section):
    mouse: bool = Field(True, title="Mouse mode (hand)")
    navigation: bool = Field(False, title="Navigation mode (head)")
    keyboard: bool = Field(False, title="Keyboard mode")
    face_mouse: bool = Field(False, title="Hands-free mouse (eyes & head)")


class HandGesture(str, Enum):
    """Discrete or continuous hand gestures that can be mapped to commands."""

    CURSOR = "hand.cursor"
    PINCH = "hand.pinch"
    MIDDLE_PINCH = "hand.middle_pinch"
    SCROLL = "hand.scroll"
    SWIPE_LEFT = "hand.swipe_left"
    SWIPE_RIGHT = "hand.swipe_right"
    PALM_HOLD = "hand.palm_hold"
    VOLUME_UP = "hand.volume_up"
    VOLUME_DOWN = "hand.volume_down"
    DRAG_START = "hand.drag_start"
    DRAG_END = "hand.drag_end"
    ZOOM_IN = "hand.zoom_in"
    ZOOM_OUT = "hand.zoom_out"
    THREE_SWIPE_LEFT = "hand.three_swipe_left"
    THREE_SWIPE_RIGHT = "hand.three_swipe_right"


class HeadGesture(str, Enum):
    TURN_LEFT = "head.turn_left"
    TURN_RIGHT = "head.turn_right"
    NOD_DOWN = "head.nod_down"
    TILT_UP = "head.tilt_up"
    ROLL_LEFT = "head.roll_left"
    ROLL_RIGHT = "head.roll_right"


class FaceGesture(str, Enum):
    """Eye, head-pointer and face-expression gestures of the hands-free mouse."""

    CURSOR = "face.cursor"
    SCROLL = "face.scroll"
    WINK_LEFT = "eye.wink_left"
    WINK_RIGHT = "eye.wink_right"
    LONG_WINK_LEFT = "eye.long_wink_left"
    LONG_WINK_RIGHT = "eye.long_wink_right"
    LONG_BLINK = "eye.long_blink"
    DOUBLE_BLINK = "eye.double_blink"
    EYES_CLOSED = "eye.closed_hold"
    MOUTH_OPEN = "face.mouth_open"
    SMILE = "face.smile"
    BROWS_RAISED = "face.brows_raised"
    DWELL = "face.dwell"


DEFAULT_HAND_MAPPINGS: dict[str, str] = {
    HandGesture.CURSOR.value: "mouse.move",
    HandGesture.PINCH.value: "mouse.left_click",
    HandGesture.MIDDLE_PINCH.value: "mouse.right_click",
    HandGesture.SCROLL.value: "mouse.scroll",
    HandGesture.SWIPE_LEFT.value: "browser.prev_tab",
    HandGesture.SWIPE_RIGHT.value: "browser.next_tab",
    HandGesture.PALM_HOLD.value: "app.toggle_pause",
    HandGesture.VOLUME_UP.value: "media.volume_up",
    HandGesture.VOLUME_DOWN.value: "media.volume_down",
    HandGesture.DRAG_START.value: "mouse.drag_start",
    HandGesture.DRAG_END.value: "mouse.drag_end",
    HandGesture.ZOOM_IN.value: "view.zoom_in",
    HandGesture.ZOOM_OUT.value: "view.zoom_out",
    HandGesture.THREE_SWIPE_LEFT.value: "window.snap_left",
    HandGesture.THREE_SWIPE_RIGHT.value: "window.snap_right",
}

DEFAULT_HEAD_MAPPINGS: dict[str, str] = {
    HeadGesture.TURN_LEFT.value: "browser.back",
    HeadGesture.TURN_RIGHT.value: "browser.forward",
    HeadGesture.NOD_DOWN.value: "key.enter",
    HeadGesture.TILT_UP.value: "key.escape",
    HeadGesture.ROLL_LEFT.value: "none",
    HeadGesture.ROLL_RIGHT.value: "none",
}


DEFAULT_FACE_MAPPINGS: dict[str, str] = {
    FaceGesture.CURSOR.value: "mouse.move",
    FaceGesture.SCROLL.value: "mouse.scroll",
    FaceGesture.WINK_LEFT.value: "mouse.left_click",
    FaceGesture.WINK_RIGHT.value: "mouse.right_click",
    FaceGesture.LONG_WINK_LEFT.value: "mouse.drag_toggle",
    FaceGesture.LONG_WINK_RIGHT.value: "face.recenter",
    FaceGesture.LONG_BLINK.value: "mouse.double_click",
    FaceGesture.DOUBLE_BLINK.value: "none",
    FaceGesture.EYES_CLOSED.value: "app.toggle_pause",
    FaceGesture.MOUTH_OPEN.value: "none",
    FaceGesture.SMILE.value: "none",
    FaceGesture.BROWS_RAISED.value: "face.scroll_mode",
    FaceGesture.DWELL.value: "mouse.left_click",
}


class MappingSettings(_Section):
    hand: dict[str, str] = Field(default_factory=lambda: dict(DEFAULT_HAND_MAPPINGS))
    head: dict[str, str] = Field(default_factory=lambda: dict(DEFAULT_HEAD_MAPPINGS))
    face: dict[str, str] = Field(default_factory=lambda: dict(DEFAULT_FACE_MAPPINGS))

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

    @field_validator("face")
    @classmethod
    def _complete_face(cls, v: dict[str, str]) -> dict[str, str]:
        merged = dict(DEFAULT_FACE_MAPPINGS)
        merged.update({k: val for k, val in v.items() if k in DEFAULT_FACE_MAPPINGS})
        return merged


class Settings(_Section):
    schema_version: int = 1
    camera: CameraSettings = Field(default_factory=CameraSettings)
    tracking: TrackingSettings = Field(default_factory=TrackingSettings)
    cursor: CursorSettings = Field(default_factory=CursorSettings)
    hand: HandGestureSettings = Field(default_factory=HandGestureSettings)
    head: HeadGestureSettings = Field(default_factory=HeadGestureSettings)
    face: FaceMouseSettings = Field(default_factory=FaceMouseSettings)
    safety: SafetySettings = Field(default_factory=SafetySettings)
    keyboard: KeyboardSettings = Field(default_factory=KeyboardSettings)
    startup: StartupSettings = Field(default_factory=StartupSettings)
    interface: InterfaceSettings = Field(default_factory=InterfaceSettings)
    modes: Modes = Field(default_factory=Modes)
    mappings: MappingSettings = Field(default_factory=MappingSettings)

    @model_validator(mode="after")
    def _check_hysteresis(self) -> "Settings":
        if self.hand.pinch_off_ratio <= self.hand.pinch_on_ratio:
            raise ValueError("hand.pinch_off_ratio must be greater than hand.pinch_on_ratio")
        if self.face.eye_open_ratio <= self.face.eye_close_ratio:
            raise ValueError("face.eye_open_ratio must be greater than face.eye_close_ratio")
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
