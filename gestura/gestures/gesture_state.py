# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Small temporal primitives: debouncing, holds and cooldowns.

Gestures are never triggered from a single frame; these helpers make that
explicit and testable.
"""

from __future__ import annotations

from typing import Generic, TypeVar

T = TypeVar("T")


class Debounced(Generic[T]):
    """A value that only changes after `min_frames` consecutive identical inputs."""

    def __init__(self, initial: T, min_frames: int = 3) -> None:
        self.value = initial
        self.min_frames = min_frames
        self._candidate = initial
        self._count = 0

    def update(self, raw: T) -> bool:
        """Feed a raw value; returns True when the stable value changed."""
        if raw == self.value:
            self._candidate, self._count = raw, 0
            return False
        if raw == self._candidate:
            self._count += 1
        else:
            self._candidate, self._count = raw, 1
        if self._count >= self.min_frames:
            self.value, self._count = raw, 0
            return True
        return False

    def reset(self, value: T) -> None:
        self.value = self._candidate = value
        self._count = 0


class Cooldown:
    def __init__(self, seconds: float) -> None:
        self.seconds = seconds
        self._until = float("-inf")

    def ready(self, now: float) -> bool:
        return now >= self._until

    def trigger(self, now: float) -> None:
        self._until = now + self.seconds

    def reset(self) -> None:
        self._until = float("-inf")


class HoldTimer:
    """Tracks how long a condition has been continuously true."""

    def __init__(self) -> None:
        self._since: float | None = None

    def update(self, condition: bool, now: float) -> float:
        if not condition:
            self._since = None
            return 0.0
        if self._since is None:
            self._since = now
        return now - self._since

    def reset(self) -> None:
        self._since = None
