# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""OS-facing controllers. Only the CommandEngine calls into this package."""

from __future__ import annotations

from typing import Callable

from ..core.command_engine import CommandEngine
from .keyboard_controller import KeyboardController
from .mouse_controller import MouseController
from .navigation_controller import NavigationController


def register_executors(
    engine: CommandEngine,
    mouse: MouseController,
    keyboard: KeyboardController,
    nav: NavigationController,
    app_actions: dict[str, Callable[[], None]] | None = None,
) -> None:
    """Bind every command id in the registry to its controller method."""
    r = engine.register
    r("mouse.move", lambda e: mouse.move_normalized(e.data["x"], e.data["y"]))
    r("mouse.left_click", lambda e: mouse.left_click())
    r("mouse.right_click", lambda e: mouse.right_click())
    r("mouse.middle_click", lambda e: mouse.middle_click())
    r("mouse.double_click", lambda e: mouse.double_click())
    r("mouse.scroll", lambda e: mouse.scroll(e.data.get("dx", 0.0), e.data.get("dy", 0.0)))
    r("mouse.drag_start", lambda e: mouse.drag_start())
    r("mouse.drag_end", lambda e: mouse.drag_end())
    r("mouse.drag_toggle", lambda e: mouse.drag_end() if mouse.dragging else mouse.drag_start())

    def zoom(direction: int) -> None:
        # Ctrl + wheel zooms in browsers, PDF/photo viewers, Office and maps on any keyboard layout.
        already = "ctrl" in keyboard.held  # e.g. Ctrl latched on the virtual keyboard
        if not already:
            keyboard.hold("ctrl")
        try:
            mouse.scroll(0.0, float(direction))
        finally:
            if not already:
                keyboard.release("ctrl")

    r("view.zoom_in", lambda e: zoom(+1))
    r("view.zoom_out", lambda e: zoom(-1))
    for cmd, combo in (("window.snap_left", ("win", "left")), ("window.snap_right", ("win", "right")),
                       ("window.maximize", ("win", "up")), ("window.minimize", ("win", "down")),
                       ("window.show_desktop", ("win", "d")), ("window.task_view", ("win", "tab"))):
        r(cmd, lambda e, c=combo: keyboard.hotkey(*c))
    r("browser.back", lambda e: nav.back())
    r("browser.forward", lambda e: nav.forward())
    r("browser.next_tab", lambda e: nav.next_tab())
    r("browser.prev_tab", lambda e: nav.prev_tab())
    r("browser.page_down", lambda e: nav.page_down())
    r("browser.page_up", lambda e: nav.page_up())
    r("system.alt_tab", lambda e: nav.switch_window())
    for cmd, key in (("key.enter", "enter"), ("key.escape", "esc"), ("key.tab", "tab"),
                     ("key.space", "space"), ("key.arrow_left", "left"), ("key.arrow_right", "right"),
                     ("key.arrow_up", "up"), ("key.arrow_down", "down"),
                     ("media.volume_up", "volumeup"), ("media.volume_down", "volumedown"),
                     ("media.mute", "volumemute"), ("media.play_pause", "playpause"),
                     ("media.next_track", "nexttrack"), ("media.prev_track", "prevtrack")):
        r(cmd, lambda e, k=key: keyboard.press(k))
    for cmd, action in (app_actions or {}).items():
        r(cmd, lambda e, a=action: a())
