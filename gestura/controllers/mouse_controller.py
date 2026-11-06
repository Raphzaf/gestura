"""Mouse actions on top of an InputBackend."""

from __future__ import annotations

from ..config.settings import CursorSettings
from .backends import InputBackend


class MouseController:
    # Keep our own cursor 1 px away from the exact screen corners so it can
    # never trip PyAutoGUI's fail-safe; only a *physical* mouse moved into a
    # corner does that, which is the intended emergency gesture.
    EDGE_INSET = 1

    def __init__(self, backend: InputBackend, settings: CursorSettings) -> None:
        self.backend = backend
        self.settings = settings
        self._last: tuple[int, int] | None = None
        self._scroll_rem = [0.0, 0.0]
        self._size: tuple[int, int] | None = None

    def screen_size(self) -> tuple[int, int]:
        if self._size is None:
            self._size = self.backend.screen_size()
        return self._size

    def invalidate_screen(self) -> None:
        self._size = None

    def to_pixels(self, u: float, v: float) -> tuple[int, int]:
        w, h = self.screen_size()
        i = self.EDGE_INSET
        x = int(round(u * (w - 1)))
        y = int(round(v * (h - 1)))
        return min(w - 1 - i, max(i, x)), min(h - 1 - i, max(i, y))

    def move_normalized(self, u: float, v: float) -> bool:
        """Move the cursor; returns False when inside the dead zone."""
        x, y = self.to_pixels(u, v)
        if self._last is not None:
            dz = self.settings.dead_zone_px
            if abs(x - self._last[0]) <= dz and abs(y - self._last[1]) <= dz:
                return False
        self.backend.move_to(x, y)
        self._last = (x, y)
        return True

    def left_click(self) -> None:
        self.backend.click("left", 1)

    def right_click(self) -> None:
        self.backend.click("right", 1)

    def middle_click(self) -> None:
        self.backend.click("middle", 1)

    def double_click(self) -> None:
        self.backend.click("left", 2)

    def scroll(self, dx: float, dy: float) -> None:
        """dx/dy in wheel notches (may be fractional)."""
        if self.backend.fractional_scroll:
            if dy:
                self.backend.scroll(dy)
            if dx:
                self.backend.hscroll(dx)
            return
        # Integer-only backends: accumulate the fractional part between frames.
        for axis, val in ((1, dy), (0, dx)):
            if not val:
                continue
            self._scroll_rem[axis] += val
            whole = int(self._scroll_rem[axis])
            if whole:
                self._scroll_rem[axis] -= whole
                (self.backend.scroll if axis == 1 else self.backend.hscroll)(whole)

    def reset(self) -> None:
        self._last = None
        self._scroll_rem = [0.0, 0.0]
