"""Win32 SendInput helpers for what PyAutoGUI does not do correctly on Windows.

* Horizontal wheel: PyAutoGUI's Windows `hscroll` falls back to vertical scroll.
* Fractional (high-resolution) wheel deltas for smooth scrolling.
* Unicode text: KEYEVENTF_UNICODE types any character (é, à, ç, €…)
  independently of the active keyboard layout.

Structures are declared with fixed-width integer types (not ctypes.wintypes)
so their layout can be unit-tested on any 64-bit platform.
"""

from __future__ import annotations

import ctypes
import sys

INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
MOUSEEVENTF_WHEEL = 0x0800
MOUSEEVENTF_HWHEEL = 0x1000
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
WHEEL_DELTA = 120

ULONG_PTR = ctypes.c_size_t


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_int32), ("dy", ctypes.c_int32), ("mouseData", ctypes.c_uint32),
                ("dwFlags", ctypes.c_uint32), ("time", ctypes.c_uint32), ("dwExtraInfo", ULONG_PTR)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_uint16), ("wScan", ctypes.c_uint16), ("dwFlags", ctypes.c_uint32),
                ("time", ctypes.c_uint32), ("dwExtraInfo", ULONG_PTR)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", ctypes.c_uint32), ("wParamL", ctypes.c_uint16), ("wParamH", ctypes.c_uint16)]


class _INPUTUNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("u",)
    _fields_ = [("type", ctypes.c_uint32), ("u", _INPUTUNION)]


def _send(inputs: list[INPUT]) -> int:
    if sys.platform != "win32":  # pragma: no cover - guarded by callers
        raise OSError("SendInput is only available on Windows")
    arr = (INPUT * len(inputs))(*inputs)
    return ctypes.windll.user32.SendInput(len(inputs), arr, ctypes.sizeof(INPUT))


def wheel_input(delta: int, horizontal: bool = False) -> INPUT:
    inp = INPUT(type=INPUT_MOUSE)
    inp.mi = MOUSEINPUT(0, 0, ctypes.c_uint32(delta).value,
                        MOUSEEVENTF_HWHEEL if horizontal else MOUSEEVENTF_WHEEL, 0, 0)
    return inp


def unicode_inputs(text: str) -> list[INPUT]:
    """Key down/up pairs for each UTF-16 code unit of `text`."""
    events: list[INPUT] = []
    data = text.encode("utf-16-le")
    for i in range(0, len(data), 2):
        unit = int.from_bytes(data[i:i + 2], "little")
        for flags in (KEYEVENTF_UNICODE, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP):
            inp = INPUT(type=INPUT_KEYBOARD)
            inp.ki = KEYBDINPUT(0, unit, flags, 0, 0)
            events.append(inp)
    return events


def send_wheel(notches: float, horizontal: bool = False) -> None:
    delta = int(round(notches * WHEEL_DELTA))
    if delta:
        _send([wheel_input(delta, horizontal)])


def send_text(text: str) -> None:
    if text:
        _send(unicode_inputs(text))
