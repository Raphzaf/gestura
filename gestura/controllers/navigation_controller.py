# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Browser / window navigation via standard shortcuts.

These shortcuts work in Chrome, Edge, Firefox and File Explorer (back/forward),
so navigation is application-agnostic rather than tied to one browser.
"""

from __future__ import annotations

from .keyboard_controller import KeyboardController


class NavigationController:
    def __init__(self, keyboard: KeyboardController) -> None:
        self.kb = keyboard

    def back(self) -> None:
        self.kb.hotkey("alt", "left")

    def forward(self) -> None:
        self.kb.hotkey("alt", "right")

    def next_tab(self) -> None:
        self.kb.hotkey("ctrl", "tab")

    def prev_tab(self) -> None:
        self.kb.hotkey("ctrl", "shift", "tab")

    def page_down(self) -> None:
        self.kb.press("pagedown")

    def page_up(self) -> None:
        self.kb.press("pageup")

    def switch_window(self) -> None:
        self.kb.hotkey("alt", "tab")
