# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Virtual keyboard layouts (pure data).

A key is (kind, value, label, shifted_label, width):
  kind "char": types `value` (or `shifted` when Shift/Caps applies)
  kind "key":  presses a named key ("enter", "backspace", "left", ...)
  kind "mod":  sticky modifier ("shift", "ctrl", "alt", "win")
  kind "caps": Caps Lock toggle
Characters are sent as Unicode text, so AZERTY output (é, è, à, ç, ù, €…) does
not depend on the system keyboard layout.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Key:
    kind: str
    value: str
    label: str
    shifted: str = ""
    width: float = 1.0
    letter: bool = False  # Caps Lock affects it

    def text(self, shift: bool, caps: bool) -> str:
        upper = shift != caps if self.letter else shift
        if upper and self.shifted:
            return self.shifted
        return self.value


def _chars(pairs: str, letters: bool = False) -> list[Key]:
    """'aA zZ' -> keys; for non-letters 'unshifted shifted' pairs."""
    keys = []
    for pair in pairs.split(" "):
        base, shifted = pair[0], pair[1:] or pair[0]
        keys.append(Key("char", base, base.upper() if letters else base, shifted, 1.0, letters))
    return keys


def _letters(s: str) -> list[Key]:
    return [Key("char", c, c.upper(), c.upper(), 1.0, True) for c in s]


BACKSPACE = Key("key", "backspace", "⌫", width=1.8)
TAB = Key("key", "tab", "Tab", width=1.4)
ENTER = Key("key", "enter", "Enter ⏎", width=1.9)
CAPS = Key("caps", "caps", "Caps", width=1.7)
SHIFT_L = Key("mod", "shift", "⇧ Shift", width=2.0)
SHIFT_R = Key("mod", "shift", "⇧ Shift", width=2.0)
ESC = Key("key", "esc", "Esc", width=1.2)
CTRL = Key("mod", "ctrl", "Ctrl", width=1.4)
WIN = Key("mod", "win", "Win", width=1.2)
ALT = Key("mod", "alt", "Alt", width=1.2)
SPACE = Key("char", " ", "Space", " ", width=6.0)
ARROWS = [Key("key", "left", "←"), Key("key", "up", "↑"), Key("key", "down", "↓"), Key("key", "right", "→")]
DELETE = Key("key", "delete", "Del", width=1.2)


def _qwerty() -> list[list[Key]]:
    return [
        [ESC, *_chars("1! 2@ 3# 4$ 5% 6^ 7& 8* 9( 0) -_ =+"), BACKSPACE],
        [TAB, *_letters("qwertyuiop"), *_chars("[{ ]} \\|")],
        [CAPS, *_letters("asdfghjkl"), *_chars(";: '\""), ENTER],
        [SHIFT_L, *_letters("zxcvbnm"), *_chars(",< .> /?"), SHIFT_R],
        [CTRL, WIN, ALT, SPACE, DELETE, *ARROWS],
    ]


def _azerty() -> list[list[Key]]:
    # French AZERTY: the number row types symbols unshifted and digits with Shift.
    num = [Key("char", a, a, b) for a, b in
           (("&", "1"), ("é", "2"), ('"', "3"), ("'", "4"), ("(", "5"), ("-", "6"),
            ("è", "7"), ("_", "8"), ("ç", "9"), ("à", "0"), (")", "°"), ("=", "+"))]
    return [
        [ESC, *num, BACKSPACE],
        [TAB, *_letters("azertyuiop"), Key("char", "^", "^", "¨"), Key("char", "$", "$", "£"),
         Key("char", "*", "*", "µ")],
        [CAPS, *_letters("qsdfghjklm"), Key("char", "ù", "ù", "%"), ENTER],
        [SHIFT_L, Key("char", "<", "<", ">"), *_letters("wxcvbn"),
         *[Key("char", a, a, b) for a, b in ((",", "?"), (";", "."), (":", "/"), ("!", "§"))], SHIFT_R],
        [CTRL, WIN, ALT, SPACE, Key("char", "@", "@", "€"), DELETE, *ARROWS],
    ]


LAYOUTS = {"qwerty": _qwerty, "azerty": _azerty}


def layout(name: str) -> list[list[Key]]:
    return LAYOUTS.get(name, _qwerty)()
