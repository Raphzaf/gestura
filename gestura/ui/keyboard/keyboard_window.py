"""Floating, always-on-top, non-activating virtual keyboard.

Focus is the hard part of an on-screen keyboard: if clicking a key activated
our window, keystrokes would go to Gestura instead of the app you are typing
in. We combine:
  * Qt.WindowDoesNotAcceptFocus + WA_ShowWithoutActivating,
  * Qt.Tool (no taskbar entry) + WindowStaysOnTopHint,
  * on Windows, WS_EX_NOACTIVATE | WS_EX_TOPMOST set explicitly via Win32
    (the documented way on-screen keyboards stay click-through for focus),
  * Qt.NoFocus on every key.
Keys are activated by ordinary clicks, so the hand cursor + pinch works with
no special integration: the OS delivers the click like any other.
"""

from __future__ import annotations

import sys

from PySide6.QtCore import QPoint, QSize, Qt, Signal
from PySide6.QtGui import QGuiApplication, QMouseEvent
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget

from ...controllers.virtual_keyboard_controller import VirtualKeyboardController
from .layouts import Key, layout

BASE_KEY = 46  # px at scale 1.0


def _make_noactivate(widget: QWidget) -> bool:
    if sys.platform != "win32":
        return False
    try:  # pragma: no cover - Windows only
        import ctypes

        GWL_EXSTYLE, WS_EX_NOACTIVATE, WS_EX_TOPMOST, WS_EX_TOOLWINDOW = -20, 0x08000000, 0x00000008, 0x00000080
        user32 = ctypes.windll.user32
        get = user32.GetWindowLongPtrW
        set_ = user32.SetWindowLongPtrW
        get.restype = set_.restype = ctypes.c_ssize_t
        get.argtypes = [ctypes.c_void_p, ctypes.c_int]
        set_.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_ssize_t]
        hwnd = ctypes.c_void_p(int(widget.winId()))
        style = get(hwnd, GWL_EXSTYLE)
        set_(hwnd, GWL_EXSTYLE, style | WS_EX_NOACTIVATE | WS_EX_TOPMOST | WS_EX_TOOLWINDOW)
        return True
    except Exception:  # noqa: BLE001
        return False


class KeyButton(QPushButton):
    """Key whose preferred size is exactly its configured size (style-independent)."""

    def __init__(self, text: str, width: int, height: int) -> None:
        super().__init__(text)
        self._hint = QSize(width, height)
        self.setMinimumWidth(width)
        self.setFixedHeight(height)

    def sizeHint(self) -> QSize:  # noqa: N802
        return self._hint

    def minimumSizeHint(self) -> QSize:  # noqa: N802
        return self._hint


class KeyboardWindow(QWidget):
    closed = Signal()
    geometry_changed = Signal(int, int)
    layout_changed = Signal(str)
    scale_changed = Signal(float)

    def __init__(self, controller: VirtualKeyboardController, layout_name: str = "azerty",
                 scale: float = 1.0, opacity: float = 0.95) -> None:
        super().__init__(None, Qt.WindowType.Tool | Qt.WindowType.FramelessWindowHint |
                         Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setObjectName("keyboardWindow")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.setWindowTitle("Gestura keyboard")
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.controller = controller
        self.layout_name = layout_name
        self.scale = scale
        self._drag: QPoint | None = None
        self._mod_buttons: list[tuple[QPushButton, Key]] = []
        self._char_buttons: list[tuple[QPushButton, Key]] = []
        self.noactivate = False
        self.setWindowOpacity(opacity)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 8, 12, 12)
        root.setSpacing(6)
        header = QHBoxLayout()
        self.handle = QLabel("⠿  Gestura keyboard")
        self.handle.setObjectName("muted")
        self.handle.setCursor(Qt.CursorShape.SizeAllCursor)
        self.handle.setToolTip("Drag to move")
        header.addWidget(self.handle)
        self.preview = QLabel("")
        self.preview.setObjectName("value")
        self.preview.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        header.addWidget(self.preview, 1)
        self.status = QLabel("")
        self.status.setObjectName("hint")
        header.addWidget(self.status)
        for text, tip, fn in (("AZ/QW", "Switch layout", self._toggle_layout),
                              ("▲", "Dock at top", lambda: self.dock("top")),
                              ("▼", "Dock at bottom", lambda: self.dock("bottom")),
                              ("−", "Smaller", lambda: self.set_scale(self.scale - 0.1)),
                              ("+", "Larger", lambda: self.set_scale(self.scale + 0.1)),
                              ("✕", "Hide keyboard", self.hide_keyboard)):
            b = QPushButton(text)
            b.setToolTip(tip)
            b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            b.setFixedHeight(30)
            b.clicked.connect(fn)
            header.addWidget(b)
        root.addLayout(header)
        self.keys_host = QWidget()
        self.keys_layout = QVBoxLayout(self.keys_host)
        self.keys_layout.setContentsMargins(0, 0, 0, 0)
        self.keys_layout.setSpacing(5)
        root.addWidget(self.keys_host)
        self._build()

    # ------------------------------------------------------------- building
    def _build(self) -> None:
        # Rebuild into a fresh container: refilling a live layout leaves stale
        # cached size hints, which broke resizing.
        old = self.keys_host
        self.keys_host = QWidget()
        self.keys_layout = QVBoxLayout(self.keys_host)
        self.keys_layout.setContentsMargins(0, 0, 0, 0)
        self.keys_layout.setSpacing(5)
        self.layout().replaceWidget(old, self.keys_host)
        old.hide()
        old.deleteLater()
        self._mod_buttons.clear()
        self._char_buttons.clear()
        size = int(BASE_KEY * self.scale)
        for row in layout(self.layout_name):
            h = QHBoxLayout()
            h.setSpacing(5)
            for key in row:
                b = KeyButton(key.label, int(size * key.width), size)
                b.setObjectName("keyButton")
                b.setFocusPolicy(Qt.FocusPolicy.NoFocus)
                b.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                b.setAccessibleName(key.label)
                if key.kind in ("mod", "caps"):
                    b.setCheckable(True)
                    self._mod_buttons.append((b, key))
                elif key.kind == "char":
                    self._char_buttons.append((b, key))
                b.clicked.connect(lambda _c=False, k=key: self._press(k))
                h.addWidget(b, int(key.width * 10))
            self.keys_layout.addLayout(h)
        self._sync()
        # Qt defers showing widgets added to a visible window, and hidden widgets
        # don't count toward the size hint: show it now, then lay out.
        self.keys_host.setVisible(True)
        self.layout().activate()
        self.adjustSize()

    def _press(self, key: Key) -> None:
        desc = self.controller.press(key.kind, key.value, key.shifted, key.letter)
        self.status.setText(desc)
        self._sync()

    def _sync(self) -> None:
        st = self.controller.state
        for b, key in self._mod_buttons:
            on = st.caps if key.kind == "caps" else (st.shift if key.value == "shift" else key.value in st.mods)
            b.setChecked(on)
        for b, key in self._char_buttons:
            if key.value != " ":
                b.setText(key.text(st.shift, st.caps) if key.letter or st.shift else key.label)
        self.preview.setText(self.controller.preview[-40:])

    # ------------------------------------------------------------ placement
    def show_keyboard(self) -> None:
        if not self.isVisible():
            self.show()
            self.noactivate = _make_noactivate(self)
            self.raise_()

    def hide_keyboard(self) -> None:
        self.hide()
        self.closed.emit()

    def dock(self, where: str) -> None:
        screen = (self.screen() or QGuiApplication.primaryScreen()).availableGeometry()
        self.adjustSize()
        x = screen.x() + (screen.width() - self.width()) // 2
        y = screen.y() + 12 if where == "top" else screen.bottom() - self.height() - 12
        self.move(x, y)
        self.geometry_changed.emit(x, y)

    def set_scale(self, scale: float) -> None:
        self.scale = round(min(2.0, max(0.6, scale)), 2)
        self._build()
        self.scale_changed.emit(self.scale)

    def set_layout(self, name: str) -> None:
        if name != self.layout_name:
            self.layout_name = name
            self._build()

    def _toggle_layout(self) -> None:
        self.set_layout("qwerty" if self.layout_name == "azerty" else "azerty")
        self.layout_changed.emit(self.layout_name)

    # ---------------------------------------------------------------- drag
    def mousePressEvent(self, e: QMouseEvent) -> None:  # noqa: N802
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag = e.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, e: QMouseEvent) -> None:  # noqa: N802
        if self._drag is not None:
            self.move(e.globalPosition().toPoint() - self._drag)

    def mouseReleaseEvent(self, _e: QMouseEvent) -> None:  # noqa: N802
        if self._drag is not None:
            self._drag = None
            self.geometry_changed.emit(self.x(), self.y())
