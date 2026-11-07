# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Signal filters for pointer smoothing.

The One Euro filter (Casiez, Roussel & Vogel, CHI 2012) adapts its cutoff to
speed: heavy smoothing when the hand is nearly still (kills jitter), light
smoothing when it moves fast (keeps latency low).
"""

from __future__ import annotations

import math


class _LowPass:
    __slots__ = ("y", "initialized")

    def __init__(self) -> None:
        self.y = 0.0
        self.initialized = False

    def __call__(self, x: float, alpha: float) -> float:
        if not self.initialized:
            self.y, self.initialized = x, True
        else:
            self.y = alpha * x + (1 - alpha) * self.y
        return self.y


def _alpha(cutoff: float, dt: float) -> float:
    tau = 1.0 / (2 * math.pi * cutoff)
    return 1.0 / (1.0 + tau / dt)


class OneEuroFilter:
    def __init__(self, min_cutoff: float = 1.0, beta: float = 0.0, d_cutoff: float = 1.0) -> None:
        self.min_cutoff, self.beta, self.d_cutoff = min_cutoff, beta, d_cutoff
        self._x = _LowPass()
        self._dx = _LowPass()
        self._t: float | None = None

    def reset(self) -> None:
        self._x = _LowPass()
        self._dx = _LowPass()
        self._t = None

    def __call__(self, x: float, t: float) -> float:
        if self._t is None:
            self._t = t
            self._dx(0.0, 1.0)
            return self._x(x, 1.0)
        dt = max(t - self._t, 1e-4)
        self._t = t
        dx = (x - self._x.y) / dt
        edx = self._dx(dx, _alpha(self.d_cutoff, dt))
        cutoff = self.min_cutoff + self.beta * abs(edx)
        return self._x(x, _alpha(cutoff, dt))


class OneEuro2D:
    def __init__(self, min_cutoff: float = 1.0, beta: float = 0.0) -> None:
        self.fx = OneEuroFilter(min_cutoff, beta)
        self.fy = OneEuroFilter(min_cutoff, beta)

    def configure(self, min_cutoff: float, beta: float) -> None:
        for f in (self.fx, self.fy):
            f.min_cutoff, f.beta = min_cutoff, beta

    def reset(self) -> None:
        self.fx.reset()
        self.fy.reset()

    def __call__(self, x: float, y: float, t: float) -> tuple[float, float]:
        return self.fx(x, t), self.fy(y, t)
