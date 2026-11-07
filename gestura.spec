# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
# PyInstaller spec for Gestura.  Build:  pyinstaller --noconfirm gestura.spec
# Produces dist/Gestura/ (one-folder build; starts faster and is friendlier to
# antivirus scanners than one-file). On Windows the entry point is Gestura.exe.
import sys

from PyInstaller.utils.hooks import collect_all, collect_data_files

block_cipher = None

# MediaPipe loads its C library through importlib.resources from
# mediapipe/tasks/c/, so its package layout must be preserved: collect_all does that.
mp_datas, mp_binaries, mp_hidden = collect_all("mediapipe")

datas = [
    ("gestura/assets", "gestura/assets"),
    ("gestura/config/default_settings.json", "gestura/config"),
    ("LICENSE", "."),  # the GPL requires the license text to travel with the binaries
] + mp_datas

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=mp_binaries,
    datas=datas,
    hiddenimports=mp_hidden + ["PySide6.QtSvg"],
    hookspath=[],
    runtime_hooks=[],
    # Not used by Gestura; mouseinfo (pulled by PyAutoGUI) degrades gracefully without tkinter.
    # mouseinfo (pulled in by PyAutoGUI, GPLv3) is never used by Gestura: leaving it out keeps
    # the bundle free of third-party GPL code, so a dual-licensed edition stays possible.
    excludes=["tkinter", "mouseinfo", "PySide6.QtWebEngineCore", "PySide6.Qt3DCore", "PySide6.QtQuick", "PySide6.QtQml",
              "pytest"],
    noarchive=False,
    cipher=block_cipher,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Gestura",
    debug=False,
    strip=False,
    upx=False,
    console=False,  # GUI app: no console window on Windows
    icon="gestura/assets/icon.ico",
)
coll = COLLECT(exe, a.binaries, a.zipfiles, a.datas, strip=False, upx=False, name="Gestura")
