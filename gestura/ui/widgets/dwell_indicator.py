# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura. Gestura is free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Small ring next to the mouse pointer: dwell-click progress and scroll mode.

Click-through, never takes focus, always on top: it only shows what is about to
happen, so a hands-free user is never surprised by a click.
"""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QCursor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from .. import theme

SIZE = 46
OFFSET = 18


class DwellIndicator(QWidget):
    def __init__(self) -> None:
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint
                         | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowTransparentForInput
                         | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.resize(SIZE, SIZE)
        self.progress = 0.0
        self.scroll_mode = False

    def set_state(self, progress: float, scroll_mode: bool) -> None:
        self.progress, self.scroll_mode = max(0.0, min(1.0, progress)), scroll_mode
        if self.progress <= 0.05 and not scroll_mode:
            if self.isVisible():
                self.hide()
            return
        pos = QCursor.pos()
        self.move(pos.x() + OFFSET, pos.y() + OFFSET)
        if not self.isVisible():
            self.show()
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(5, 5, SIZE - 10, SIZE - 10)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(14, 16, 20, 170))
        p.drawEllipse(r)
        if self.scroll_mode:
            p.setPen(QColor(theme.WARN))
            f = QFont()
            f.setPixelSize(22)
            f.setBold(True)
            p.setFont(f)
            p.drawText(r, int(Qt.AlignmentFlag.AlignCenter), "↕")
            return
        p.setPen(QPen(QColor(theme.MUTED), 3))
        p.drawEllipse(r.adjusted(4, 4, -4, -4))
        pen = QPen(QColor(theme.SUCCESS if self.progress >= 1 else theme.ACCENT), 4)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(pen)
        p.drawArc(r.adjusted(4, 4, -4, -4), 90 * 16, -int(360 * 16 * self.progress))
