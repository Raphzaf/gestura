"""Central authority on whether commands may reach the operating system.

States
------
STOPPED    tracking is not running; nothing executes.
ACTIVE     commands execute (or are only simulated in test mode).
PAUSED     soft pause: only app-control commands (resume) are honoured.
EMERGENCY  hard stop: nothing executes; only an explicit UI action clears it.

Test mode ("dry run") is orthogonal: when on, every command is logged and shown
but never sent to the OS. It is on by default at startup.
"""

from __future__ import annotations

import enum
import threading
import time
from dataclasses import dataclass
from typing import Callable


class FailSafeTriggered(Exception):
    """Raised by an input backend when its fail-safe fires (e.g. mouse in a corner)."""


class EngineState(str, enum.Enum):
    STOPPED = "stopped"
    ACTIVE = "active"
    PAUSED = "paused"
    EMERGENCY = "emergency"


@dataclass(slots=True)
class Decision:
    allowed: bool
    simulated: bool = False
    reason: str = ""
    needs_confirmation: bool = False


Listener = Callable[["SafetyManager"], None]


class SafetyManager:
    def __init__(
        self,
        test_mode: bool = True,
        confirm_sensitive: bool = True,
        confirm_window_s: float = 2.5,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._lock = threading.RLock()
        self._state = EngineState.STOPPED
        self._test_mode = test_mode
        self.confirm_sensitive = confirm_sensitive
        self.confirm_window_s = confirm_window_s
        self._clock = clock
        self._pending: tuple[str, float] | None = None  # (command_id, deadline)
        self._listeners: list[Listener] = []
        self.last_reason = ""

    # ----------------------------------------------------------------- state
    @property
    def state(self) -> EngineState:
        return self._state

    @property
    def test_mode(self) -> bool:
        return self._test_mode

    @property
    def pending_confirmation(self) -> str | None:
        with self._lock:
            if self._pending and self._clock() <= self._pending[1]:
                return self._pending[0]
            return None

    def add_listener(self, listener: Listener) -> None:
        self._listeners.append(listener)

    def _set(self, state: EngineState, reason: str) -> None:
        with self._lock:
            if self._state == state and reason == self.last_reason:
                return
            self._state = state
            self.last_reason = reason
            self._pending = None
        for listener in list(self._listeners):
            listener(self)

    def start(self) -> None:
        with self._lock:
            if self._state == EngineState.EMERGENCY:
                return  # must be cleared explicitly
        self._set(EngineState.ACTIVE, "started")

    def stop(self) -> None:
        with self._lock:
            if self._state == EngineState.EMERGENCY:
                return
        self._set(EngineState.STOPPED, "stopped")

    def pause(self, reason: str = "paused") -> None:
        if self._state == EngineState.ACTIVE:
            self._set(EngineState.PAUSED, reason)

    def resume(self, reason: str = "resumed") -> None:
        if self._state == EngineState.PAUSED:
            self._set(EngineState.ACTIVE, reason)

    def toggle_pause(self, reason: str = "") -> None:
        if self._state == EngineState.ACTIVE:
            self.pause(reason or "paused")
        elif self._state == EngineState.PAUSED:
            self.resume(reason or "resumed")

    def emergency_stop(self, reason: str = "emergency stop") -> None:
        self._set(EngineState.EMERGENCY, reason)

    def clear_emergency(self) -> None:
        """Only called from an explicit UI action, never from a gesture."""
        if self._state == EngineState.EMERGENCY:
            self._set(EngineState.STOPPED, "emergency cleared")

    def set_test_mode(self, on: bool) -> None:
        with self._lock:
            changed = on != self._test_mode
            self._test_mode = on
            self._pending = None
        if changed:
            for listener in list(self._listeners):
                listener(self)

    # -------------------------------------------------------------- decisions
    def check(self, command_id: str, *, control: bool, sensitive: bool) -> Decision:
        with self._lock:
            state = self._state
            if state == EngineState.EMERGENCY:
                return Decision(False, reason="emergency stop active")
            if state == EngineState.STOPPED:
                return Decision(False, reason="engine stopped")
            if control:
                # App-control commands (pause/resume, emergency) always run.
                return Decision(True)
            if state == EngineState.PAUSED:
                return Decision(False, reason="paused")
            if sensitive and self.confirm_sensitive:
                now = self._clock()
                if self._pending and self._pending[0] == command_id and now <= self._pending[1]:
                    self._pending = None
                else:
                    self._pending = (command_id, now + self.confirm_window_s)
                    return Decision(False, reason="repeat gesture to confirm", needs_confirmation=True)
            return Decision(True, simulated=self._test_mode)
