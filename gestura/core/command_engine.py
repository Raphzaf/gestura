"""Maps gesture events to commands and executes them through controllers.

This is the only path from perception to the operating system:

    GestureEvent --(mapping)--> CommandSpec --(SafetyManager)--> executor

Executors are plain callables registered by the controllers layer, so the
engine itself has no knowledge of PyAutoGUI or Win32.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Callable

from . import event_bus as topics
from .event_bus import EventBus
from .gesture_registry import COMMANDS, CommandSpec
from .safety_manager import FailSafeTriggered, SafetyManager
from .types import GestureEvent

log = logging.getLogger(__name__)

Executor = Callable[[GestureEvent], None]


@dataclass(slots=True)
class CommandRecord:
    command: str
    label: str
    gesture: str
    timestamp: float
    executed: bool
    simulated: bool = False
    reason: str = ""
    data: dict = field(default_factory=dict)


class CommandEngine:
    def __init__(self, safety: SafetyManager, bus: EventBus | None = None) -> None:
        self.safety = safety
        self.bus = bus
        self._lock = threading.Lock()
        self._mapping: dict[str, str] = {}
        self._executors: dict[str, Executor] = {}
        self.history: deque[CommandRecord] = deque(maxlen=200)

    # ------------------------------------------------------------ configuration
    def set_mapping(self, mapping: dict[str, str]) -> None:
        cleaned: dict[str, str] = {}
        for gesture, command in mapping.items():
            spec = COMMANDS.get(command)
            if spec is None:
                log.warning("ignoring unknown command %r for %r", command, gesture)
                continue
            cleaned[gesture] = command
        with self._lock:
            self._mapping = cleaned

    def mapping(self) -> dict[str, str]:
        with self._lock:
            return dict(self._mapping)

    def register(self, command_id: str, executor: Executor) -> None:
        if command_id not in COMMANDS:
            raise KeyError(f"unknown command {command_id!r}")
        self._executors[command_id] = executor

    # ------------------------------------------------------------------ running
    def resolve(self, gesture_name: str) -> CommandSpec | None:
        with self._lock:
            command_id = self._mapping.get(gesture_name, "none")
        spec = COMMANDS.get(command_id)
        if spec is None or spec.id == "none":
            return None
        return spec

    def handle(self, event: GestureEvent) -> CommandRecord | None:
        spec = self.resolve(event.name)
        if spec is None:
            return None
        if spec.continuous != event.continuous:
            # e.g. a discrete gesture mapped to "mouse.move": refuse silently.
            return None

        decision = self.safety.check(spec.id, control=spec.control, sensitive=spec.sensitive)
        record = CommandRecord(
            command=spec.id,
            label=spec.label,
            gesture=event.name,
            timestamp=event.timestamp or time.monotonic(),
            executed=False,
            simulated=decision.simulated,
            reason=decision.reason,
            data=dict(event.data),
        )
        if decision.allowed and not decision.simulated:
            executor = self._executors.get(spec.id)
            if executor is None:
                record.reason = "no executor registered"
            else:
                try:
                    executor(event)
                    record.executed = True
                except FailSafeTriggered:
                    record.reason = "fail-safe: mouse moved to a screen corner"
                    self.safety.emergency_stop(record.reason)
                except Exception as exc:  # noqa: BLE001
                    log.exception("command %s failed", spec.id)
                    record.reason = f"error: {exc}"
        elif decision.allowed and decision.simulated:
            record.reason = "test mode"

        if not spec.continuous:
            self.history.append(record)
            if self.bus is not None:
                topic = topics.COMMAND_EXECUTED if decision.allowed else topics.COMMAND_BLOCKED
                self.bus.publish(topic, record)
        return record
