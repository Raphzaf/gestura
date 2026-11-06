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
    excludes=["tkinter", "PySide6.QtWebEngineCore", "PySide6.Qt3DCore", "PySide6.QtQuick", "PySide6.QtQml",
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
