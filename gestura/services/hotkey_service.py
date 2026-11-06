"""System-wide emergency-stop hotkey (Ctrl+Alt+Shift+G) on Windows.

Uses Win32 RegisterHotKey on a dedicated thread with its own message loop, so
it works even when another application has focus. This is for a helper or the
user's physical keyboard; the primary hands-free stops are the open-palm
gesture, the on-screen button and PyAutoGUI's corner fail-safe.

On non-Windows platforms this is a no-op (the in-app shortcut still works).
"""

from __future__ import annotations

import ctypes
import logging
import sys
import threading
from typing import Callable

log = logging.getLogger(__name__)

MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_NOREPEAT = 0x0001, 0x0002, 0x0004, 0x4000
WM_HOTKEY, WM_QUIT = 0x0312, 0x0012
HOTKEY_ID = 0x6E57


class GlobalHotkey:
    def __init__(self, callback: Callable[[], None], key: str = "G") -> None:
        self.callback = callback
        self.key = key
        self._thread: threading.Thread | None = None
        self._thread_id = 0
        self.registered = False
        self.error = ""

    def start(self) -> bool:
        if sys.platform != "win32":
            self.error = "global hotkey is only available on Windows"
            return False
        ready = threading.Event()
        self._thread = threading.Thread(target=self._run, args=(ready,), name="gestura-hotkey", daemon=True)
        self._thread.start()
        ready.wait(2.0)
        return self.registered

    def _run(self, ready: threading.Event) -> None:  # pragma: no cover - Windows only
        from ctypes import wintypes

        user32 = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32
        self._thread_id = kernel32.GetCurrentThreadId()
        mods = MOD_CONTROL | MOD_ALT | MOD_SHIFT | MOD_NOREPEAT
        self.registered = bool(user32.RegisterHotKey(None, HOTKEY_ID, mods, ord(self.key)))
        if not self.registered:
            self.error = "hotkey already in use by another application"
            log.warning("RegisterHotKey failed: %s", self.error)
        ready.set()
        if not self.registered:
            return
        msg = wintypes.MSG()
        try:
            while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                if msg.message == WM_HOTKEY and msg.wParam == HOTKEY_ID:
                    try:
                        self.callback()
                    except Exception:  # noqa: BLE001
                        log.exception("hotkey callback failed")
        finally:
            user32.UnregisterHotKey(None, HOTKEY_ID)

    def stop(self) -> None:
        if self._thread and self._thread_id and sys.platform == "win32":  # pragma: no cover
            ctypes.windll.user32.PostThreadMessageW(self._thread_id, WM_QUIT, 0, 0)
            self._thread.join(1.0)
        self._thread = None
