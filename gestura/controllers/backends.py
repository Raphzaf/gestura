"""OS input backends.

`PyAutoGuiBackend` is the real implementation (with Win32 overrides);
`RecordingBackend` records calls and is used by tests and test mode tooling.
"""

from __future__ import annotations

import logging
import sys
import threading
from typing import Protocol

from ..core.safety_manager import FailSafeTriggered

log = logging.getLogger(__name__)


def _disable_mouseinfo_if_unusable() -> None:
    """PyAutoGUI imports `mouseinfo`, which needs tkinter and calls sys.exit()
    (Linux) or raises (Windows) without it. Gestura never uses mouseinfo, so
    when tkinter is missing we make the import fail cleanly; PyAutoGUI already
    handles ImportError for it."""
    if "mouseinfo" in sys.modules:
        return
    try:
        import tkinter  # noqa: F401
    except ImportError:
        sys.modules["mouseinfo"] = None  # type: ignore[assignment]  -> import raises ImportError


class InputBackend(Protocol):
    fractional_scroll: bool

    def screen_size(self) -> tuple[int, int]: ...
    def position(self) -> tuple[int, int]: ...
    def move_to(self, x: int, y: int) -> None: ...
    def click(self, button: str = "left", clicks: int = 1) -> None: ...
    def scroll(self, notches: float) -> None: ...
    def hscroll(self, notches: float) -> None: ...
    def press(self, key: str) -> None: ...
    def hotkey(self, *keys: str) -> None: ...
    def key_down(self, key: str) -> None: ...
    def key_up(self, key: str) -> None: ...
    def write_text(self, text: str) -> None: ...


class PyAutoGuiBackend:
    """Real OS input. PyAutoGUI is imported lazily (it needs a display)."""

    def __init__(self, failsafe: bool = True) -> None:
        _disable_mouseinfo_if_unusable()
        import pyautogui  # noqa: PLC0415 - lazy on purpose

        self._pg = pyautogui
        pyautogui.PAUSE = 0  # default 0.1 s sleep after every call would cap us at 10 FPS
        pyautogui.MINIMUM_DURATION = 0
        pyautogui.FAILSAFE = failsafe
        self._win = sys.platform == "win32"
        self.fractional_scroll = self._win
        self._lock = threading.Lock()

    def set_failsafe(self, on: bool) -> None:
        self._pg.FAILSAFE = on

    def _call(self, fn, *args, **kwargs):
        try:
            with self._lock:
                return fn(*args, **kwargs)
        except self._pg.FailSafeException as exc:
            raise FailSafeTriggered(str(exc)) from exc

    def screen_size(self) -> tuple[int, int]:
        w, h = self._pg.size()
        return int(w), int(h)

    def position(self) -> tuple[int, int]:
        x, y = self._pg.position()
        return int(x), int(y)

    def move_to(self, x: int, y: int) -> None:
        self._call(self._pg.moveTo, x, y, _pause=False)

    def click(self, button: str = "left", clicks: int = 1) -> None:
        self._call(self._pg.click, button=button, clicks=clicks, interval=0.0, _pause=False)

    def scroll(self, notches: float) -> None:
        if self._win:
            from . import win32_input

            self._call(self._pg.failSafeCheck)
            win32_input.send_wheel(notches)
        else:
            self._call(self._pg.scroll, int(notches), _pause=False)

    def hscroll(self, notches: float) -> None:
        if self._win:
            from . import win32_input

            self._call(self._pg.failSafeCheck)
            win32_input.send_wheel(notches, horizontal=True)
        else:
            self._call(self._pg.hscroll, int(notches), _pause=False)

    def press(self, key: str) -> None:
        self._call(self._pg.press, key, _pause=False)

    def hotkey(self, *keys: str) -> None:
        self._call(self._pg.hotkey, *keys, interval=0.0, _pause=False)

    def key_down(self, key: str) -> None:
        self._call(self._pg.keyDown, key, _pause=False)

    def key_up(self, key: str) -> None:
        self._call(self._pg.keyUp, key, _pause=False)

    def write_text(self, text: str) -> None:
        if self._win:
            from . import win32_input

            self._call(self._pg.failSafeCheck)
            win32_input.send_text(text)
        else:
            # PyAutoGUI's write() only handles characters on the US layout.
            self._call(self._pg.write, text, interval=0.0, _pause=False)


class RecordingBackend:
    """Records every call instead of touching the OS."""

    def __init__(self, size: tuple[int, int] = (1920, 1080), fractional_scroll: bool = False) -> None:
        self.size = size
        self.fractional_scroll = fractional_scroll
        self.calls: list[tuple] = []
        self.pos = (size[0] // 2, size[1] // 2)

    def screen_size(self) -> tuple[int, int]:
        return self.size

    def position(self) -> tuple[int, int]:
        return self.pos

    def move_to(self, x: int, y: int) -> None:
        self.pos = (x, y)
        self.calls.append(("move_to", x, y))

    def click(self, button: str = "left", clicks: int = 1) -> None:
        self.calls.append(("click", button, clicks))

    def scroll(self, notches: float) -> None:
        self.calls.append(("scroll", notches))

    def hscroll(self, notches: float) -> None:
        self.calls.append(("hscroll", notches))

    def press(self, key: str) -> None:
        self.calls.append(("press", key))

    def hotkey(self, *keys: str) -> None:
        self.calls.append(("hotkey", *keys))

    def key_down(self, key: str) -> None:
        self.calls.append(("key_down", key))

    def key_up(self, key: str) -> None:
        self.calls.append(("key_up", key))

    def write_text(self, text: str) -> None:
        self.calls.append(("write_text", text))

    def named(self, name: str) -> list[tuple]:
        return [c for c in self.calls if c[0] == name]
