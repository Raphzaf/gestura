"""Minimal thread-safe publish/subscribe bus.

Topics are plain strings. Handlers run synchronously on the publisher's thread;
a handler that raises is logged and never breaks the publisher (a crashing UI
subscriber must not stop the tracking loop). The Qt UI receives events through
Qt signals emitted by the tracking service, which marshal them onto the GUI
thread.
"""

from __future__ import annotations

import logging
import threading
from collections import defaultdict
from typing import Any, Callable

log = logging.getLogger(__name__)

Handler = Callable[[Any], None]

# Well-known topics
GESTURE = "gesture"  # payload: GestureEvent
COMMAND_EXECUTED = "command.executed"  # payload: CommandRecord
COMMAND_BLOCKED = "command.blocked"  # payload: CommandRecord
SAFETY_STATE = "safety.state"  # payload: EngineState


class EventBus:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._handlers: dict[str, list[Handler]] = defaultdict(list)

    def subscribe(self, topic: str, handler: Handler) -> Callable[[], None]:
        with self._lock:
            self._handlers[topic].append(handler)

        def unsubscribe() -> None:
            with self._lock:
                if handler in self._handlers.get(topic, []):
                    self._handlers[topic].remove(handler)

        return unsubscribe

    def publish(self, topic: str, payload: Any = None) -> None:
        with self._lock:
            handlers = list(self._handlers.get(topic, ()))
        for handler in handlers:
            try:
                handler(payload)
            except Exception:  # noqa: BLE001 - isolation is the point
                log.exception("event handler for %r failed", topic)
