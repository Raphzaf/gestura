"""Application controller: wires every layer together.

    vision ─▶ gestures ─▶ CommandEngine ─(SafetyManager)─▶ controllers ─▶ OS
                                       ▲
    UI ─────── GesturaApp (this) ──────┘   (UI never calls controllers directly)
"""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QTimer, Signal

from ..config.settings import Settings
from ..controllers import register_executors
from ..controllers.backends import InputBackend, PyAutoGuiBackend, RecordingBackend
from ..controllers.keyboard_controller import KeyboardController
from ..controllers.mouse_controller import MouseController
from ..controllers.navigation_controller import NavigationController
from ..core.command_engine import CommandEngine
from ..core.event_bus import EventBus
from ..core.safety_manager import EngineState, SafetyManager
from ..services.configuration_service import ConfigurationService
from ..services.hotkey_service import GlobalHotkey
from ..services.tracking_service import TrackingService

log = logging.getLogger(__name__)


class GesturaApp(QObject):
    state_changed = Signal()  # safety state / test mode changed (always on GUI thread)
    settings_changed = Signal(object)  # Settings
    keyboard_toggle_requested = Signal()
    notice = Signal(str)

    def __init__(self, config: ConfigurationService, source_spec: str | None = None,
                 force_test_mode: bool | None = None, backend: InputBackend | None = None) -> None:
        super().__init__()
        self.config = config
        self.settings: Settings = config.load()
        test_mode = self.settings.safety.start_in_test_mode if force_test_mode is None else force_test_mode
        self.safety = SafetyManager(test_mode=test_mode,
                                    confirm_sensitive=self.settings.safety.confirm_sensitive,
                                    confirm_window_s=self.settings.safety.confirm_window_ms / 1000)
        self.bus = EventBus()
        self.commands = CommandEngine(self.safety, self.bus)
        self.commands.set_mapping(self._mapping())

        self.backend_error = ""
        if backend is None:
            try:
                backend = PyAutoGuiBackend(failsafe=self.settings.safety.pyautogui_failsafe)
            except (Exception, SystemExit) as exc:  # noqa: BLE001 - e.g. no display on Linux CI
                self.backend_error = f"System input is unavailable ({exc}); running in simulation only."
                log.warning(self.backend_error)
                backend = RecordingBackend()
        self.backend = backend
        self.keyboard = KeyboardController(backend)
        self.mouse = MouseController(backend, self.settings.cursor)
        self.nav = NavigationController(self.keyboard)
        register_executors(self.commands, self.mouse, self.keyboard, self.nav, {
            "app.toggle_pause": lambda: self.safety.toggle_pause("open palm"),
            "app.emergency_stop": lambda: self.safety.emergency_stop("emergency gesture"),
            "app.toggle_keyboard": self.keyboard_toggle_requested.emit,
        })

        self.tracking = TrackingService(self.settings, self.safety, self.commands, self.bus, source_spec)
        # Safety listeners may fire on the worker thread (palm gesture, fail-safe):
        # re-emit through a queued signal so all UI work happens on the GUI thread.
        self._safety_signal_relay = _Relay()
        self._safety_signal_relay.fired.connect(self._on_safety_changed)
        self.safety.add_listener(lambda _s: self._safety_signal_relay.fired.emit())
        self.tracking.running_changed.connect(lambda _r: self.state_changed.emit())

        self.hotkey = GlobalHotkey(lambda: self._safety_signal_relay.hotkey.emit())
        self._safety_signal_relay.hotkey.connect(lambda: self.emergency_stop("global hotkey"))
        if self.settings.safety.global_hotkey:
            self.hotkey.start()

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(400)
        self._save_timer.timeout.connect(self._save_now)

    # --------------------------------------------------------------- control
    def start(self) -> None:
        if self.safety.state == EngineState.EMERGENCY:
            self.notice.emit("Clear the emergency stop first.")
            return
        self.tracking.start()
        self.safety.start()

    def stop(self) -> None:
        self.safety.stop()
        self.tracking.stop()
        self._release_inputs()

    def emergency_stop(self, reason: str = "emergency stop button") -> None:
        self.safety.emergency_stop(reason)  # blocks commands immediately (thread-safe)
        self._release_inputs()
        self.tracking.stop()

    def clear_emergency(self) -> None:
        self.safety.clear_emergency()

    def toggle_pause(self) -> None:
        self.safety.toggle_pause("button")

    def set_test_mode(self, on: bool) -> None:
        self.safety.set_test_mode(on)

    def _release_inputs(self) -> None:
        self.keyboard.release_all()
        self.mouse.reset()

    def _on_safety_changed(self) -> None:
        if self.safety.state in (EngineState.EMERGENCY, EngineState.PAUSED, EngineState.STOPPED):
            self._release_inputs()
        if self.safety.state == EngineState.EMERGENCY and self.tracking.running:
            self.tracking.stop()
        self.state_changed.emit()

    # -------------------------------------------------------------- settings
    def _mapping(self) -> dict[str, str]:
        return {**self.settings.mappings.hand, **self.settings.mappings.head}

    def update_settings(self, settings: Settings, save: bool = True) -> None:
        if settings.startup.launch_at_login != self.settings.startup.launch_at_login:
            from ..services import startup_service

            if startup_service.is_supported() and not startup_service.set_enabled(settings.startup.launch_at_login):
                self.notice.emit("Could not change the launch-at-login setting.")
        self.settings = settings
        self.mouse.settings = settings.cursor
        self.safety.confirm_sensitive = settings.safety.confirm_sensitive
        self.safety.confirm_window_s = settings.safety.confirm_window_ms / 1000
        if hasattr(self.backend, "set_failsafe"):
            self.backend.set_failsafe(settings.safety.pyautogui_failsafe)
        self.commands.set_mapping(self._mapping())
        self.tracking.apply_settings(settings)
        self.settings_changed.emit(settings)
        if save:
            self._save_timer.start()

    def set_mode(self, mode: str, on: bool) -> None:
        s = self.settings.copy_deep()
        setattr(s.modes, mode, on)
        self.update_settings(s)

    def _save_now(self) -> None:
        try:
            self.config.save(self.settings)
        except OSError as exc:
            self.notice.emit(f"Could not save settings: {exc}")

    def shutdown(self) -> None:
        self.stop()
        self.hotkey.stop()
        if self._save_timer.isActive():
            self._save_timer.stop()
            self._save_now()


class _Relay(QObject):
    fired = Signal()
    hotkey = Signal()
