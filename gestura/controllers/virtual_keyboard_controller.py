"""Virtual keyboard behaviour (Qt-free, unit-tested).

* Shift is one-shot: it applies to the next character, then releases.
  Selecting Shift twice in a row latches it until selected again.
* Caps Lock toggles letters only.
* Ctrl / Alt / Win are sticky: select Ctrl, then C -> sends Ctrl+C.
  They release after the next non-modifier key.
* Plain characters are typed as Unicode text; with Ctrl/Alt/Win held they are
  sent as a shortcut on the base key instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .keyboard_controller import KeyboardController

ALLOWED_SHORTCUT_MODS = ("ctrl", "alt", "win", "shift")


@dataclass(slots=True)
class KeyboardState:
    shift: bool = False
    shift_locked: bool = False
    caps: bool = False
    mods: set[str] = field(default_factory=set)  # ctrl / alt / win


class VirtualKeyboardController:
    def __init__(self, keyboard: KeyboardController, can_send: Callable[[], bool] = lambda: True) -> None:
        self.kb = keyboard
        self.can_send = can_send  # False in test mode / emergency: preview only
        self.state = KeyboardState()
        self.preview = ""  # what has been typed, for on-keyboard feedback

    def press(self, kind: str, value: str, shifted: str = "", letter: bool = False) -> str:
        """Handle one key selection. Returns a short description of what happened."""
        st = self.state
        if kind == "mod":
            if value == "shift":
                if st.shift and not st.shift_locked:
                    st.shift_locked = True
                elif st.shift:
                    st.shift = st.shift_locked = False
                else:
                    st.shift = True
                return "Shift locked" if st.shift_locked else ("Shift" if st.shift else "Shift off")
            if value in st.mods:
                st.mods.discard(value)
            else:
                st.mods.add(value)
            return "+".join(sorted(st.mods)) or "modifiers off"
        if kind == "caps":
            st.caps = not st.caps
            return "Caps Lock on" if st.caps else "Caps Lock off"

        send = self.can_send()
        if kind == "char":
            upper = (st.shift != st.caps) if letter else st.shift
            text = shifted if upper and shifted else value
            if st.mods:
                combo = [*sorted(st.mods), value.lower()]
                if st.shift:
                    combo.insert(-1, "shift")
                if send:
                    self.kb.hotkey(*combo)
                desc = "+".join(combo)
            else:
                if send:
                    self.kb.type_text(text)
                self.preview = (self.preview + text)[-60:]
                desc = text
        elif kind == "key":
            combo = [*sorted(st.mods)] + (["shift"] if st.shift else [])
            if send:
                if combo:
                    self.kb.hotkey(*combo, value)
                else:
                    self.kb.press(value)
            if not combo:
                if value == "backspace":
                    self.preview = self.preview[:-1]
                elif value == "enter":
                    self.preview = ""
            desc = "+".join([*combo, value])
        else:
            return ""
        # one-shot modifiers release after a non-modifier key
        st.mods.clear()
        if not st.shift_locked:
            st.shift = False
        return desc if send else f"{desc} (not sent)"

    def reset(self) -> None:
        self.state = KeyboardState()
