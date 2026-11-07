# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Render the Gestura film.

  preview T1 T2 ...            -> work/preview/t_<T>.png at 1920x1080
  segment START END OUT.mp4    -> frames [START, END) at 3840x2160, encoded with x264
"""
import os
import subprocess
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtGui import QGuiApplication, QImage  # noqa: E402

app = QGuiApplication(sys.argv[:1])
import film_scenes as fs  # noqa: E402
from film_core import FPS, H, W, VDIR  # noqa: E402


def render(t, scale):
    img = QImage(int(W * scale), int(H * scale), QImage.Format.Format_RGB32)
    img.fill(0)
    fs.draw_frame(img, t, scale)
    return img


def main():
    mode = sys.argv[1]
    if mode == "preview":
        out = os.path.join(VDIR, "work", "preview")
        os.makedirs(out, exist_ok=True)
        for s in sys.argv[2:]:
            render(float(s), 1.0).save(os.path.join(out, f"t_{float(s):05.2f}.png"))
        return
    start, end, path = int(sys.argv[2]), int(sys.argv[3]), sys.argv[4]
    scale = float(os.environ.get("FILM_SCALE", "2"))
    w, h = int(W * scale), int(H * scale)
    enc = subprocess.Popen([
        "ffmpeg", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "bgra", "-s", f"{w}x{h}",
        "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-preset", os.environ.get("FILM_PRESET", "medium"),
        "-crf", os.environ.get("FILM_CRF", "16"), "-pix_fmt", "yuv420p", "-profile:v", "high",
        "-x264-params", "keyint=48:min-keyint=48:scenecut=0", "-threads", "2", path], stdin=subprocess.PIPE)
    for i in range(start, end):
        img = render(i / FPS, scale)
        enc.stdin.write(bytes(img.constBits()))
        if (i - start) % 48 == 0:
            print(f"{path}: frame {i}", flush=True)
    enc.stdin.close()
    sys.exit(enc.wait())


if __name__ == "__main__":
    main()
