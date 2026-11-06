"""Click-through, always-on-top toast that confirms recognised gestures.

When Gestura runs in the background the user cannot see its window, so every
discrete gesture, confirmation request and pause/stop is echoed here.
The window never takes focus and is transparent to mouse input.
"""

from __future__ import annotations

from PySide6.QtCore import QPropertyAnimation, Qt, QTimer
from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget

from .. import theme


class FeedbackOverlay(QWidget):
    def __init__(self, position: str = "top") -> None:
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint |
                         Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowDoesNotAcceptFocus |
                         Qt.WindowType.WindowTransparentForInput)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.position = position
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        self.label = QLabel("")
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.addWidget(self.label)
        self._hide = QTimer(self)
        self._hide.setSingleShot(True)
        self._hide.timeout.connect(self._fade_out)
        self._anim = QPropertyAnimation(self, b"windowOpacity", self)
        self._anim.setDuration(250)
        self._anim.finished.connect(self._after_anim)
        self.last_message = ""

    def flash(self, text: str, kind: str = "info", ms: int = 1300) -> None:
        color = {"info": theme.ACCENT, "ok": theme.SUCCESS, "warn": theme.WARN, "danger": theme.DANGER}[kind]
        self.last_message = text
        self.label.setText(text)
        self.label.setStyleSheet(
            f"background: rgba(14,16,20,235); color: {color}; border: 1px solid {color};"
            "border-radius: 14px; padding: 10px 22px; font-size: 13pt; font-weight: 600;")
        self.adjustSize()
        screen = QGuiApplication.primaryScreen().availableGeometry()
        x = screen.x() + (screen.width() - self.width()) // 2
        y = screen.y() + 24 if self.position == "top" else screen.bottom() - self.height() - 24
        self.move(x, y)
        self._anim.stop()
        self.setWindowOpacity(1.0)
        self.show()
        self.raise_()
        self._hide.start(ms)

    def _fade_out(self) -> None:
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.start()

    def _after_anim(self) -> None:
        if self.windowOpacity() <= 0.01:
            self.hide()
