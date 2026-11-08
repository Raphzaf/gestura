# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Builds the main window and the auxiliary windows, and wires them to the app."""

from __future__ import annotations

from PySide6.QtCore import QPoint
from PySide6.QtGui import QGuiApplication

from ..controllers.virtual_keyboard_controller import VirtualKeyboardController
from ..core.safety_manager import EngineState


def build_main_window(app):
    from ..ui.calibration.wizard import CalibrationWizard
    from ..ui.keyboard.keyboard_page import KeyboardPage
    from ..ui.keyboard.keyboard_window import KeyboardWindow
    from ..ui.main_window import MainWindow
    from ..ui.widgets.dwell_indicator import DwellIndicator
    from ..ui.widgets.feedback_overlay import FeedbackOverlay

    s = app.settings
    vk = VirtualKeyboardController(
        app.keyboard,
        can_send=lambda: app.safety.state != EngineState.EMERGENCY and not app.safety.test_mode)
    kw = KeyboardWindow(vk, s.keyboard.layout, s.keyboard.scale, s.keyboard.opacity)
    kpage = KeyboardPage(app, kw)
    window = MainWindow(app, extra_pages=[("keyboard", "Virtual Keyboard", kpage)])
    window.keyboard_window = kw
    overlay = FeedbackOverlay(s.interface.overlay_position)
    window.overlay = overlay
    dwell = DwellIndicator()
    window.dwell_indicator = dwell

    def on_telemetry(t) -> None:
        if app.settings.modes.face_mouse and t.face.visible:
            dwell.set_state(t.face.dwell_progress, t.face.scroll_mode)
        elif dwell.isVisible():
            dwell.hide()

    app.tracking.telemetry.connect(on_telemetry)
    app.tracking.running_changed.connect(lambda running: None if running else dwell.hide())

    # ---- keyboard visibility / persistence
    def place_keyboard() -> None:
        k = app.settings.keyboard
        if k.pos_x >= 0 and k.pos_y >= 0 and QGuiApplication.screenAt(QPoint(k.pos_x + 20, k.pos_y + 20)):
            kw.move(k.pos_x, k.pos_y)
        else:
            kw.dock("bottom")

    def on_settings(new) -> None:
        kw.set_layout(new.keyboard.layout)
        if abs(kw.scale - new.keyboard.scale) > 1e-3:
            kw.set_scale(new.keyboard.scale)
        kw.setWindowOpacity(new.keyboard.opacity)
        overlay.position = new.interface.overlay_position
        if new.modes.keyboard and not kw.isVisible():
            kw.show_keyboard()
            place_keyboard()
        elif not new.modes.keyboard and kw.isVisible():
            kw.hide()

    def save_kb(field: str, value) -> None:
        ns = app.settings.copy_deep()
        setattr(ns.keyboard, field, value)
        app.update_settings(ns)

    def save_pos(x: int, y: int) -> None:
        ns = app.settings.copy_deep()
        ns.keyboard.pos_x, ns.keyboard.pos_y = max(0, x), max(0, y)
        app.update_settings(ns)

    app.settings_changed.connect(on_settings)
    app.keyboard_toggle_requested.connect(lambda: app.set_mode("keyboard", not app.settings.modes.keyboard))
    kw.closed.connect(lambda: app.set_mode("keyboard", False))
    kw.geometry_changed.connect(save_pos)
    kw.layout_changed.connect(lambda name: save_kb("layout", name))
    kw.scale_changed.connect(lambda v: save_kb("scale", v))
    if s.modes.keyboard:
        kw.show_keyboard()
        place_keyboard()

    # ---- feedback overlay
    def flash(text: str, kind: str = "info") -> None:
        if app.settings.interface.show_overlay:
            overlay.flash(text, kind)

    def on_command(rec) -> None:
        if rec.command == "app.toggle_pause":
            return  # announced by the state change
        if rec.executed:
            flash(rec.label, "ok")
        elif rec.simulated:
            flash(f"{rec.label} · test mode", "info")
        elif "confirm" in rec.reason:
            flash(f"Repeat to confirm: {rec.label}", "warn")
        elif rec.reason not in ("engine stopped",):
            flash(f"{rec.label}: {rec.reason}", "warn")

    last_state = {"v": app.safety.state}

    def resume_hint() -> str:
        cfg = app.settings
        hints = []
        if cfg.modes.mouse and cfg.mappings.hand.get("hand.palm_hold") == "app.toggle_pause":
            hints.append("hold an open palm")
        if cfg.modes.face_mouse and cfg.mappings.face.get("eye.closed_hold") == "app.toggle_pause":
            hints.append("close your eyes for 2 s")
        return " or ".join(hints) or "press Resume"

    def on_state() -> None:
        st = app.safety.state
        if st != last_state["v"]:
            if st == EngineState.PAUSED:
                flash(f"Gestura paused — {resume_hint()} to resume", "warn")
            elif st == EngineState.ACTIVE and last_state["v"] == EngineState.PAUSED:
                flash("Gestura resumed", "ok")
            elif st == EngineState.EMERGENCY:
                flash("EMERGENCY STOP — all control halted", "danger")
            last_state["v"] = st

    app.tracking.command.connect(on_command)
    app.state_changed.connect(on_state)

    # ---- calibration
    def calibrate() -> None:
        CalibrationWizard(app, window).exec()

    window.dashboard.calibrate_requested.connect(calibrate)

    def calibrate_eyes() -> None:
        from ..ui.calibration.gaze_calibration import GazeCalibration

        if getattr(window, "eye_calibration", None) is not None and window.eye_calibration.isVisible():
            return
        cal = GazeCalibration(app)
        window.eye_calibration = cal

        def done(saved: bool) -> None:
            if saved:
                flash("Eye calibration saved", "ok")
            window.eye_calibration = None

        cal.done.connect(done)
        cal.start()

    window.dashboard.eye_calibrate_requested.connect(calibrate_eyes)

    original_close = window.closeEvent

    def close_all(event) -> None:
        kw.close()
        overlay.close()
        dwell.close()
        original_close(event)

    window.closeEvent = close_all
    return window
