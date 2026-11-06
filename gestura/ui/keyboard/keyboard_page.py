"""Keyboard page: show/hide the floating keyboard, configure it, practise."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QFormLayout, QHBoxLayout, QLineEdit, QPushButton, QSlider, QVBoxLayout, QWidget

from ...core.safety_manager import EngineState
from ..widgets.common import Card, ToggleRow, label


class KeyboardPage(QWidget):
    def __init__(self, app, keyboard_window, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.app = app
        self.kw = keyboard_window
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(16)

        top = QHBoxLayout()
        top.setSpacing(16)
        show = Card("Floating keyboard")
        self.show_row = ToggleRow("Show keyboard", "Stays on top of other windows without taking focus.",
                                  app.settings.modes.keyboard)
        self.show_row.toggled.connect(lambda on: app.set_mode("keyboard", on))
        show.body.addWidget(self.show_row)
        dock = QHBoxLayout()
        for text, where in (("Dock at top", "top"), ("Dock at bottom", "bottom")):
            b = QPushButton(text)
            b.clicked.connect(lambda _c=False, w=where: self._dock(w))
            dock.addWidget(b)
        dock.addStretch(1)
        show.body.addLayout(dock)
        self.send_note = label("", "hint", wrap=True)
        show.body.addWidget(self.send_note)
        show.body.addStretch(1)
        top.addWidget(show, 1)

        cfg = Card("Appearance")
        form = QFormLayout()
        self.layout_combo = QComboBox()
        self.layout_combo.addItem("AZERTY (French)", "azerty")
        self.layout_combo.addItem("QWERTY (US)", "qwerty")
        self.layout_combo.currentIndexChanged.connect(self._layout)
        form.addRow("Layout", self.layout_combo)
        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setRange(60, 200)
        self.size_slider.valueChanged.connect(lambda v: self._set("scale", v / 100))
        form.addRow("Size", self.size_slider)
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(40, 100)
        self.opacity_slider.valueChanged.connect(lambda v: self._set("opacity", v / 100))
        form.addRow("Opacity", self.opacity_slider)
        cfg.body.addLayout(form)
        cfg.body.addStretch(1)
        top.addWidget(cfg, 1)
        root.addLayout(top)

        how = Card("How to type hands-free")
        for line in (
            "1. Turn on Mouse mode and Keyboard mode on the Dashboard.",
            "2. Point with your index finger to move the cursor onto a key.",
            "3. Pinch thumb and index to press it. The key flashes and the typed text appears in the keyboard header.",
            "4. Shift applies to the next letter (select twice to lock). Ctrl / Alt / Win stay held until the next key, "
            "so Ctrl then C sends Ctrl+C.",
        ):
            how.body.addWidget(label(line, "value", wrap=True))
        how.body.addSpacing(6)
        how.body.addWidget(label("Practice field: click it, then type with the floating keyboard.", "hint"))
        self.practice = QLineEdit()
        self.practice.setPlaceholderText("Type here with the virtual keyboard…")
        how.body.addWidget(self.practice)
        root.addWidget(how)
        root.addStretch(1)

        app.settings_changed.connect(self.load)
        app.state_changed.connect(self._note)
        self.load(app.settings)
        self._note()

    def load(self, s) -> None:
        for w in (self.layout_combo, self.size_slider, self.opacity_slider):
            w.blockSignals(True)
        self.layout_combo.setCurrentIndex(max(0, self.layout_combo.findData(s.keyboard.layout)))
        self.size_slider.setValue(int(s.keyboard.scale * 100))
        self.opacity_slider.setValue(int(s.keyboard.opacity * 100))
        for w in (self.layout_combo, self.size_slider, self.opacity_slider):
            w.blockSignals(False)
        self.show_row.setChecked(s.modes.keyboard)

    def _note(self) -> None:
        st = self.app.safety
        if st.state == EngineState.EMERGENCY:
            self.send_note.setText("Emergency stop is active: the keyboard does not send keys.")
        elif st.test_mode:
            self.send_note.setText("Test mode: keys are shown in the keyboard header but not sent to applications.")
        else:
            self.send_note.setText("Keys are sent to the window that has focus.")

    def _layout(self) -> None:
        self._set("layout", self.layout_combo.currentData())

    def _set(self, field: str, value) -> None:
        s = self.app.settings.copy_deep()
        setattr(s.keyboard, field, value)
        self.app.update_settings(s)

    def _dock(self, where: str) -> None:
        if not self.app.settings.modes.keyboard:
            self.app.set_mode("keyboard", True)
        self.kw.dock(where)
