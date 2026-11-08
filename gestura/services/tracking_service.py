# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Background tracking pipeline and its Qt-facing service.

Threading model
---------------
* `TrackingWorker` (a QThread) owns the camera, the MediaPipe models and the
  gesture engines. Per frame it: captures -> runs inference -> updates gesture
  engines -> hands gesture events to the CommandEngine (which executes OS input
  on this same worker thread, so cursor latency does not depend on the UI).
* The GUI thread only receives (a) at most one pending preview image at a time
  and (b) a ~15 Hz telemetry snapshot, via queued Qt signals. If the UI falls
  behind, frames are dropped rather than queued.
* Settings changes are handed over by reference swap and applied at the top of
  the next loop iteration.
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field

import numpy as np
from PySide6.QtCore import QObject, QThread, Signal
from PySide6.QtGui import QImage

from ..config.settings import Settings
from ..core.command_engine import CommandEngine, CommandRecord
from ..core.event_bus import COMMAND_BLOCKED, COMMAND_EXECUTED, GESTURE, EventBus
from ..core.safety_manager import SafetyManager
from ..core.types import GestureEvent
from ..gestures.face_gestures import FaceGestureEngine, FaceState
from ..gestures.hand_gestures import HandGestureEngine, HandState
from ..gestures.head_gestures import HeadGestureEngine, HeadState

log = logging.getLogger(__name__)


@dataclass(slots=True)
class Telemetry:
    fps: float = 0.0
    latency_ms: float = 0.0
    hand_ms: float = 0.0
    face_ms: float = 0.0
    source: str = ""
    frame_size: tuple[int, int] = (0, 0)
    hand: HandState = field(default_factory=HandState)
    head: HeadState = field(default_factory=HeadState)
    face: FaceState = field(default_factory=FaceState)
    face_visible: bool = False
    hands_visible: int = 0


class CameraStatus:
    OFF = "off"
    STARTING = "starting"
    ON = "on"
    LOST = "lost"
    ERROR = "error"


def to_qimage(bgr: np.ndarray, max_width: int = 960) -> QImage:
    import cv2

    h, w = bgr.shape[:2]
    if w > max_width:
        bgr = cv2.resize(bgr, (max_width, int(h * max_width / w)), interpolation=cv2.INTER_AREA)
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
    h, w = rgb.shape[:2]
    return QImage(rgb.data, w, h, 3 * w, QImage.Format.Format_RGB888).copy()


class TrackingWorker(QThread):
    frame_ready = Signal(QImage)
    telemetry = Signal(object)  # Telemetry
    gesture = Signal(object)  # GestureEvent
    camera_status = Signal(str, str)  # status, message

    RECONNECT_S = 2.0
    LOST_AFTER_S = 1.5

    def __init__(self, settings: Settings, commands: CommandEngine, bus: EventBus,
                 source_spec: str | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("gestura-tracking")
        self._settings = settings
        self._pending_settings: Settings | None = None
        self.commands = commands
        self.bus = bus
        self.source_spec = source_spec
        self._stop = threading.Event()
        self._frame_pending = False
        self.preview_enabled = True
        self.overlay_flags = {"hands": True, "face": True, "axes": True, "region": True}
        self.banner = ""
        self.suspended = False  # e.g. eye calibration on screen: recognise, but run no command
        self.hand_engine = HandGestureEngine(settings.hand, settings.cursor, settings.tracking)
        self.head_engine = HeadGestureEngine(settings.head)
        self.face_engine = FaceGestureEngine(settings.face, settings.head, settings.camera.mirror)
        self.processor = None
        self.frames_processed = 0

    # --------------------------------------------------------------- control
    def request_stop(self) -> None:
        self._stop.set()

    def update_settings(self, settings: Settings) -> None:
        self._pending_settings = settings.copy_deep()

    def ack_frame(self) -> None:
        self._frame_pending = False

    # ------------------------------------------------------------------ loop
    def run(self) -> None:  # noqa: C901 - the loop is intentionally linear
        from ..vision.camera_manager import make_source
        from ..vision.drawing import Overlay, annotate
        from ..vision.frame_processor import FrameProcessor

        s = self._settings
        self.camera_status.emit(CameraStatus.STARTING, "Loading models…")
        try:
            self.processor = FrameProcessor(s.tracking, s.camera)
        except Exception as exc:  # noqa: BLE001
            log.exception("failed to load models")
            self.camera_status.emit(CameraStatus.ERROR, f"Could not load tracking models: {exc}")
            return

        source = None
        last_ok = time.monotonic()
        next_retry = 0.0
        fps = 0.0
        last_t = None
        last_tel = 0.0
        try:
            while not self._stop.is_set():
                if self._pending_settings is not None:
                    s, self._pending_settings = self._pending_settings, None
                    camera_changed = s.camera != self._settings.camera
                    self._settings = s
                    self.processor.configure(s.tracking, s.camera)
                    self.hand_engine.configure(s.hand, s.cursor, s.tracking)
                    self.head_engine.configure(s.head)
                    self.face_engine.configure(s.face, s.head, s.camera.mirror)
                    if camera_changed and source is not None and self.source_spec is None:
                        source.release()
                        source = None
                        next_retry = 0.0

                if source is None:
                    if time.monotonic() < next_retry:
                        self._stop.wait(0.05)
                        continue
                    source = make_source(self.source_spec, s.camera)
                    self.camera_status.emit(CameraStatus.STARTING, f"Opening {source.name}…")
                    if not source.open():
                        msg = (f"Could not open {source.name}. Check that it is connected and not used "
                               "by another app, and that camera access is allowed in Windows privacy settings.")
                        self.camera_status.emit(CameraStatus.ERROR, msg)
                        source = None
                        next_retry = time.monotonic() + self.RECONNECT_S
                        continue
                    self.camera_status.emit(CameraStatus.ON, source.name)
                    last_ok = time.monotonic()

                frame = source.read()
                captured = time.monotonic()
                if frame is None:
                    if captured - last_ok > self.LOST_AFTER_S:
                        self.camera_status.emit(CameraStatus.LOST, f"{source.name} stopped sending frames. Reconnecting…")
                        source.release()
                        source = None
                        next_retry = captured + self.RECONNECT_S
                        self._safe_reset()
                    else:
                        self._stop.wait(0.01)
                    continue
                last_ok = captured

                # Skip expensive face inference when nobody needs it.
                need_face = s.tracking.face_enabled and (s.modes.navigation or s.modes.face_mouse
                                                         or self.preview_enabled)
                need_hands = s.tracking.hands_enabled and (s.modes.mouse or s.modes.keyboard or self.preview_enabled)
                if (need_face, need_hands) != (self.processor.tracking.face_enabled, self.processor.tracking.hands_enabled):
                    t = s.tracking.model_copy(update={"face_enabled": need_face, "hands_enabled": need_hands})
                    self.processor.configure(t, s.camera)

                display, tf = self.processor.process(frame, captured)
                self.frames_processed += 1

                hand_events = self.hand_engine.update(tf)
                head_events = self.head_engine.update(tf)
                face_events = self.face_engine.update(tf)
                self._dispatch_all(s, hand_events, head_events, face_events)

                if last_t is not None:
                    inst = 1.0 / max(1e-3, captured - last_t)
                    fps = inst if fps == 0 else 0.9 * fps + 0.1 * inst
                last_t = captured

                if self.preview_enabled and not self._frame_pending:
                    hs = self.hand_engine.state
                    of = self.overlay_flags
                    ov = Overlay(
                        show_hands=of["hands"], show_face=of["face"], show_axes=of["axes"],
                        show_region=of["region"] and (s.modes.mouse or s.modes.keyboard),
                        region=(s.cursor.region_left, s.cursor.region_top, s.cursor.region_right, s.cursor.region_bottom),
                        control_hand=hs.hand_index, click_hand=hs.click_index, cursor=hs.cursor_frame,
                        pinch_active=hs.left_pinch == "closed" or hs.right_pinch == "closed",
                        banner=self.banner,
                        eyes=self._eye_overlay(s) if of["face"] else None,
                    )
                    self._frame_pending = True
                    self.frame_ready.emit(to_qimage(annotate(display, tf, ov)))

                now = time.monotonic()
                if now - last_tel >= 1 / 15:
                    last_tel = now
                    self.telemetry.emit(Telemetry(
                        fps=fps, latency_ms=(now - captured) * 1000, hand_ms=tf.hand_ms, face_ms=tf.face_ms,
                        source=source.name, frame_size=(tf.width, tf.height),
                        hand=self.hand_engine.state, head=self.head_engine.state, face=self.face_engine.state,
                        face_visible=tf.face is not None, hands_visible=len(tf.hands)))
        except Exception as exc:  # noqa: BLE001
            log.exception("tracking loop crashed")
            self.camera_status.emit(CameraStatus.ERROR, f"Tracking stopped after an error: {exc}")
        finally:
            self._safe_reset()
            if source is not None:
                source.release()
            if self.processor is not None:
                self.processor.close()
            self.camera_status.emit(CameraStatus.OFF, "Camera off")

    def _dispatch_all(self, s: Settings, hand_events: list[GestureEvent], head_events: list[GestureEvent],
                      face_events: list[GestureEvent]) -> None:
        dispatch_hand = s.modes.mouse or s.modes.keyboard
        face_on = s.modes.face_mouse
        for ev in hand_events:
            self._dispatch(ev, dispatch_hand)
        # When the head drives the pointer, head turns / nods must not also
        # trigger back / forward / Enter.
        head_free = not (face_on and self.face_engine.uses_head)
        for ev in head_events:
            self._dispatch(ev, s.modes.navigation and head_free)
        # A hand that is actively controlling the mouse has priority over the face
        # pointer; eye and face actions (winks…) stay available.
        hand_busy = dispatch_hand and self.hand_engine.state.mode != "idle"
        self.face_engine.state.paused_by_hand = face_on and hand_busy
        for ev in face_events:
            self._dispatch(ev, face_on and not (hand_busy and ev.continuous))

    def _dispatch(self, ev: GestureEvent, enabled: bool) -> None:
        if not ev.continuous:
            self.gesture.emit(ev)
            self.bus.publish(GESTURE, ev)
        if enabled and not self.suspended:
            self.commands.handle(ev)

    def _eye_overlay(self, s: Settings) -> tuple[bool, bool] | None:
        """Closed state of the (image-left, image-right) eyes, for the preview."""
        fs = self.face_engine.state
        if not fs.visible:
            return None
        if s.camera.mirror:
            return fs.left_closed, fs.right_closed
        return fs.right_closed, fs.left_closed

    def _safe_reset(self) -> None:
        self.hand_engine.reset()
        self.head_engine.reset()
        self.face_engine.reset()


class TrackingService(QObject):
    """Owns the worker lifecycle and re-exposes its signals to the UI."""

    frame_ready = Signal(QImage)
    telemetry = Signal(object)
    gesture = Signal(object)
    command = Signal(object)  # CommandRecord (executed, simulated or blocked)
    camera_status = Signal(str, str)
    running_changed = Signal(bool)

    def __init__(self, settings: Settings, safety: SafetyManager, commands: CommandEngine,
                 bus: EventBus, source_spec: str | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.safety = safety
        self.commands = commands
        self.bus = bus
        self.source_spec = source_spec
        self.worker: TrackingWorker | None = None
        self.status = CameraStatus.OFF
        self.status_message = "Camera off"
        self._preview = True
        self._overlay = {"hands": True, "face": True, "axes": True, "region": True}
        self._suspended = False
        bus.subscribe(COMMAND_EXECUTED, self._on_command)
        bus.subscribe(COMMAND_BLOCKED, self._on_command)

    def _on_command(self, record: CommandRecord) -> None:
        self.command.emit(record)  # emitted from the worker thread -> queued to GUI

    @property
    def running(self) -> bool:
        return self.worker is not None and self.worker.isRunning()

    def start(self) -> None:
        if self.running:
            return
        w = TrackingWorker(self.settings, self.commands, self.bus, self.source_spec)
        w.preview_enabled = self._preview
        w.overlay_flags = dict(self._overlay)
        w.suspended = self._suspended
        w.frame_ready.connect(self._on_frame)
        w.telemetry.connect(self.telemetry)
        w.gesture.connect(self.gesture)
        w.camera_status.connect(self._on_status)
        w.finished.connect(self._on_finished)
        self.worker = w
        w.start()
        self.running_changed.emit(True)

    def stop(self, wait_ms: int = 5000) -> None:
        w = self.worker
        if w is None:
            return
        w.request_stop()
        w.wait(wait_ms)

    def _on_finished(self) -> None:
        self.worker = None
        self.running_changed.emit(False)

    def _on_frame(self, img: QImage) -> None:
        self.frame_ready.emit(img)
        if self.worker is not None:
            self.worker.ack_frame()

    def _on_status(self, status: str, message: str) -> None:
        self.status, self.status_message = status, message
        self.camera_status.emit(status, message)

    def apply_settings(self, settings: Settings) -> None:
        self.settings = settings
        if self.worker is not None:
            self.worker.update_settings(settings)

    def set_preview(self, on: bool) -> None:
        self._preview = on
        if self.worker is not None:
            self.worker.preview_enabled = on

    def set_overlay(self, key: str, on: bool) -> None:
        self._overlay[key] = on
        if self.worker is not None:
            self.worker.overlay_flags[key] = on

    def set_suspended(self, on: bool) -> None:
        """Keep tracking (and telemetry) running but execute no command."""
        self._suspended = on
        if self.worker is not None:
            self.worker.suspended = on

    def face_command(self, name: str) -> None:
        """Runs on the worker thread when triggered by a gesture (CommandEngine)."""
        w = self.worker
        if w is None:
            return
        if name == "scroll_mode":
            w.face_engine.toggle_scroll_mode()
        elif name == "recenter":
            w.face_engine.recenter()

    def set_banner(self, text: str) -> None:
        if self.worker is not None:
            self.worker.banner = text
