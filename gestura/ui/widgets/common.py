# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Reusable widgets: cards, chips, toggle switch, meters, video view."""

from __future__ import annotations

from PySide6.QtCore import QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QBrush, QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import (QAbstractButton, QFrame, QHBoxLayout, QLabel, QSizePolicy, QVBoxLayout,
                               QWidget)

from .. import theme


class Card(QFrame):
    def __init__(self, title: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("card")
        self.body = QVBoxLayout(self)
        self.body.setContentsMargins(18, 14, 18, 16)
        self.body.setSpacing(8)
        if title:
            t = QLabel(title.upper())
            t.setObjectName("cardTitle")
            self.body.addWidget(t)


def label(text: str = "", obj: str = "value", wrap: bool = False) -> QLabel:
    lab = QLabel(text)
    lab.setObjectName(obj)
    lab.setWordWrap(wrap)
    return lab


class StatusChip(QLabel):
    """Pill with a coloured dot, e.g. "● Camera on"."""

    def __init__(self, text: str = "", state: str = "off", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("chip")
        self.set(text, state)

    def set(self, text: str, state: str) -> None:
        color = theme.STATE_COLORS.get(state, theme.MUTED)
        self.setText(f'<span style="color:{color}">●</span>&nbsp; {text}')
        self.setAccessibleName(text)


class ToggleSwitch(QAbstractButton):
    def __init__(self, checked: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setCheckable(True)
        self.setChecked(checked)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(44, 24)

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(1, 1, -1, -1)
        on = self.isChecked()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(theme.ACCENT if on else theme.SURFACE_3))
        if not self.isEnabled():
            p.setOpacity(0.5)
        p.drawRoundedRect(r, r.height() / 2, r.height() / 2)
        d = r.height() - 6
        x = r.right() - d - 3 if on else r.left() + 3
        p.setBrush(QColor("#ffffff"))
        p.drawEllipse(QRectF(x, r.top() + 3, d, d))


class ToggleRow(QWidget):
    toggled = Signal(bool)

    def __init__(self, title: str, subtitle: str = "", checked: bool = False, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 4, 0, 4)
        text = QVBoxLayout()
        text.setSpacing(0)
        text.addWidget(label(title, "value"))
        if subtitle:
            text.addWidget(label(subtitle, "hint", wrap=True))
        lay.addLayout(text, 1)
        self.switch = ToggleSwitch(checked)
        self.switch.setAccessibleName(title)
        self.switch.toggled.connect(self.toggled)
        lay.addWidget(self.switch, 0, Qt.AlignmentFlag.AlignVCenter)

    def setChecked(self, on: bool) -> None:  # noqa: N802
        self.switch.blockSignals(True)
        self.switch.setChecked(on)
        self.switch.blockSignals(False)
        self.switch.update()


class Meter(QWidget):
    """Horizontal bar. `centered` draws from the middle for signed values.

    `marks` are threshold positions in value units, drawn as ticks.
    """

    def __init__(self, minimum: float = 0.0, maximum: float = 1.0, centered: bool = False,
                 marks: tuple[float, ...] = (), parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.minimum, self.maximum, self.centered = minimum, maximum, centered
        self.marks = marks
        self.value = 0.0
        self.color = QColor(theme.ACCENT)
        self.setMinimumHeight(10)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(160, 10)

    def set(self, value: float, color: str | None = None) -> None:
        self.value = value
        if color:
            self.color = QColor(color)
        self.update()

    def _x(self, v: float, w: float) -> float:
        span = self.maximum - self.minimum or 1.0
        return (min(self.maximum, max(self.minimum, v)) - self.minimum) / span * w

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(theme.SURFACE_3))
        p.drawRoundedRect(QRectF(0, 0, w, h), h / 2, h / 2)
        p.setBrush(self.color)
        x0 = self._x(0.0, w) if self.centered else 0.0
        x1 = self._x(self.value, w)
        left, right = sorted((x0, x1))
        if right - left > 0.5:
            p.drawRoundedRect(QRectF(left, 0, right - left, h), h / 2, h / 2)
        p.setPen(QPen(QColor(theme.TEXT), 1.5))
        for m in self.marks:
            x = self._x(m, w)
            p.drawLine(QPointF(x, -1), QPointF(x, h + 1))


class VideoView(QWidget):
    """Paints the latest preview frame, letterboxed to keep its aspect ratio."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._image: QImage | None = None
        self.placeholder = "Camera is off"
        self.setMinimumSize(320, 240)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    def set_image(self, img: QImage | None) -> None:
        self._image = img
        self.update()

    def clear(self, text: str = "Camera is off") -> None:
        self._image = None
        self.placeholder = text
        self.update()

    def paintEvent(self, _event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        r = QRectF(self.rect())
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(QColor("#08090c")))
        p.drawRoundedRect(r, 12, 12)
        if self._image is None or self._image.isNull():
            p.setPen(QColor(theme.MUTED))
            p.drawText(r, Qt.AlignmentFlag.AlignCenter, self.placeholder)
            return
        iw, ih = self._image.width(), self._image.height()
        scale = min(r.width() / iw, r.height() / ih)
        tw, th = iw * scale, ih * scale
        target = QRectF(r.x() + (r.width() - tw) / 2, r.y() + (r.height() - th) / 2, tw, th)
        p.drawImage(target, self._image)
