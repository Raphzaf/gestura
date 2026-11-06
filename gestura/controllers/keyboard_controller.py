"""Keyboard actions: named keys, shortcuts, text and held modifiers."""

from __future__ import annotations

import logging

from .backends import InputBackend

log = logging.getLogger(__name__)

MODIFIERS = ("ctrl", "alt", "shift", "win")


class KeyboardController:
    def __init__(self, backend: InputBackend) -> None:
        self.backend = backend
        self._held: set[str] = set()

    def press(self, key: str) -> None:
        self.backend.press(key)

    def hotkey(self, *keys: str) -> None:
        self.backend.hotkey(*keys)

    def type_text(self, text: str) -> None:
        self.backend.write_text(text)

    def hold(self, modifier: str) -> None:
        if modifier in MODIFIERS and modifier not in self._held:
            self.backend.key_down(modifier)
            self._held.add(modifier)

    def release(self, modifier: str) -> None:
        if modifier in self._held:
            self.backend.key_up(modifier)
            self._held.discard(modifier)

    @property
    def held(self) -> frozenset[str]:
        return frozenset(self._held)

    def release_all(self) -> None:
        """Never leave a modifier stuck down (called on stop / emergency)."""
        for mod in list(self._held):
            try:
                self.backend.key_up(mod)
            except Exception:  # noqa: BLE001
                log.exception("failed to release %s", mod)
        self._held.clear()
