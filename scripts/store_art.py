# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura. Gestura is free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Render the Microsoft Store listing images (Partner Center > Store listings > Store logos).

    python scripts/store_art.py        # writes store/listing/art/*.png

Sizes follow Partner Center: 1:1 box art 2160 x 2160, 2:3 poster art 1440 x 2160,
1:1 app tile icon 300 x 300. Everything is drawn from gestura/assets/icon.svg.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "store" / "listing" / "art"
BG_TOP, BG_BOTTOM = "#1b2230", "#0e1014"
TEXT, MUTED = "#e7e9ef", "#8a93a6"


def main() -> int:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QPointF, QRectF, Qt
    from PySide6.QtGui import QColor, QFont, QImage, QLinearGradient, QPainter
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtWidgets import QApplication

    _app = QApplication.instance() or QApplication([])  # noqa: F841 - needed by QPainter
    svg = QSvgRenderer(str(ROOT / "gestura" / "assets" / "icon.svg"))
    OUT.mkdir(parents=True, exist_ok=True)

    def canvas(w: int, h: int) -> tuple[QImage, QPainter]:
        img = QImage(w, h, QImage.Format.Format_ARGB32)
        p = QPainter(img)
        p.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)
        g = QLinearGradient(QPointF(0, 0), QPointF(w, h))
        g.setColorAt(0, QColor(BG_TOP))
        g.setColorAt(1, QColor(BG_BOTTOM))
        p.fillRect(0, 0, w, h, g)
        return img, p

    def text(p: QPainter, rect: QRectF, s: str, px: int, color: str, bold: bool = False) -> None:
        f = QFont()
        f.setPixelSize(px)
        f.setBold(bold)
        p.setFont(f)
        p.setPen(QColor(color))
        p.drawText(rect, int(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop), s)

    # 1:1 box art: icon centred on the brand background.
    img, p = canvas(2160, 2160)
    svg.render(p, QRectF(380, 380, 1400, 1400))
    p.end()
    img.save(str(OUT / "box_art_2160x2160.png"), "PNG")

    # 2:3 poster art: icon, name and tagline.
    img, p = canvas(1440, 2160)
    svg.render(p, QRectF(320, 420, 800, 800))
    text(p, QRectF(0, 1330, 1440, 220), "Gestura", 190, TEXT, bold=True)
    text(p, QRectF(0, 1580, 1440, 120), "Control your PC with your hands", 72, MUTED)
    text(p, QRectF(0, 1690, 1440, 120), "Webcam · 100% local", 72, MUTED)
    p.end()
    img.save(str(OUT / "poster_art_1440x2160.png"), "PNG")

    # 1:1 app tile icon.
    img = QImage(300, 300, QImage.Format.Format_ARGB32)
    img.fill(Qt.GlobalColor.transparent)
    p = QPainter(img)
    svg.render(p, QRectF(0, 0, 300, 300))
    p.end()
    img.save(str(OUT / "app_tile_300x300.png"), "PNG")

    for f in sorted(OUT.glob("*.png")):
        print(f"{f.relative_to(ROOT)}  ({f.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
