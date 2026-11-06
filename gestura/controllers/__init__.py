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
    r("browser.back", lambda e: nav.back())
    r("browser.forward", lambda e: nav.forward())
    r("browser.next_tab", lambda e: nav.next_tab())
    r("browser.prev_tab", lambda e: nav.prev_tab())
    r("browser.page_down", lambda e: nav.page_down())
    r("browser.page_up", lambda e: nav.page_up())
    r("system.alt_tab", lambda e: nav.switch_window())
    for cmd, key in (("key.enter", "enter"), ("key.escape", "esc"), ("key.tab", "tab"),
                     ("key.space", "space"), ("key.arrow_left", "left"), ("key.arrow_right", "right"),
                     ("key.arrow_up", "up"), ("key.arrow_down", "down")):
        r(cmd, lambda e, k=key: keyboard.press(k))
    for cmd, action in (app_actions or {}).items():
        r(cmd, lambda e, a=action: a())
