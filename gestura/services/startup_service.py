# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Launch-at-login on Windows via the per-user Run key (no admin rights needed).

HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run  ->  "Gestura" = "<command>"
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

log = logging.getLogger(__name__)

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "Gestura"


def launch_command() -> str:
    """Command line that starts this installation of Gestura minimized."""
    if getattr(sys, "frozen", False):  # PyInstaller executable
        return f'"{Path(sys.executable)}" --minimized'
    exe = Path(sys.executable)
    pythonw = exe.with_name("pythonw.exe")  # no console window on Windows
    return f'"{pythonw if pythonw.exists() else exe}" -m gestura --minimized'


APPMODEL_ERROR_NO_PACKAGE = 15700
PACKAGED_STARTUP_HINT = ("In the Microsoft Store version, turn on Gestura in Windows Settings > Apps > "
                         "Startup (Windows does not let packaged apps use the sign-in registry key).")


def is_packaged(kernel32=None) -> bool:
    """True when running as an MSIX package (e.g. installed from the Microsoft Store)."""
    if kernel32 is None:
        if sys.platform != "win32":
            return False
        import ctypes

        kernel32 = ctypes.windll.kernel32
    import ctypes

    length = ctypes.c_uint32(0)
    rc = kernel32.GetCurrentPackageFullName(ctypes.byref(length), None)
    return rc != APPMODEL_ERROR_NO_PACKAGE


def is_supported() -> bool:
    """The Run key works for the installer / portable builds, not for the MSIX package:
    there, start-up is a manifest startup task the user enables in Windows Settings."""
    return sys.platform == "win32" and not is_packaged()


def is_enabled(registry=None) -> bool:
    reg = registry or _winreg()
    if reg is None:
        return False
    try:
        with reg.OpenKey(reg.HKEY_CURRENT_USER, RUN_KEY, 0, reg.KEY_READ) as key:
            reg.QueryValueEx(key, VALUE_NAME)
            return True
    except OSError:
        return False


def set_enabled(on: bool, registry=None) -> bool:
    """Returns True on success. `registry` is injectable for tests."""
    reg = registry or _winreg()
    if reg is None:
        return False
    try:
        with reg.CreateKeyEx(reg.HKEY_CURRENT_USER, RUN_KEY, 0, reg.KEY_SET_VALUE) as key:
            if on:
                reg.SetValueEx(key, VALUE_NAME, 0, reg.REG_SZ, launch_command())
            else:
                try:
                    reg.DeleteValue(key, VALUE_NAME)
                except FileNotFoundError:
                    pass
        return True
    except OSError:
        log.exception("could not update the Run key")
        return False


def _winreg():
    if sys.platform != "win32":
        return None
    import winreg  # noqa: PLC0415

    return winreg
