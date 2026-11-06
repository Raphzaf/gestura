"""Registry of the commands Gestura is allowed to execute.

Gestures can only be mapped to commands listed here. There is no way to map a
gesture to an arbitrary key combination, program or shell command: the
registry is the allow-list. Commands flagged ``sensitive`` need a confirming
repeat of the gesture (see SafetyManager) because they can submit or dismiss
things.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CommandSpec:
    id: str
    label: str
    category: str
    continuous: bool = False  # consumes a stream (cursor / scroll)
    sensitive: bool = False  # requires confirmation
    control: bool = False  # app control: runs even while paused / in test mode


_COMMANDS: tuple[CommandSpec, ...] = (
    CommandSpec("none", "Do nothing", "General"),
    # Mouse
    CommandSpec("mouse.move", "Move cursor", "Mouse", continuous=True),
    CommandSpec("mouse.left_click", "Left click", "Mouse"),
    CommandSpec("mouse.right_click", "Right click", "Mouse"),
    CommandSpec("mouse.double_click", "Double click", "Mouse"),
    CommandSpec("mouse.middle_click", "Middle click", "Mouse"),
    CommandSpec("mouse.scroll", "Scroll", "Mouse", continuous=True),
    # Browser / navigation
    CommandSpec("browser.back", "Previous page (Alt+Left)", "Navigation"),
    CommandSpec("browser.forward", "Next page (Alt+Right)", "Navigation"),
    CommandSpec("browser.next_tab", "Next tab (Ctrl+Tab)", "Navigation"),
    CommandSpec("browser.prev_tab", "Previous tab (Ctrl+Shift+Tab)", "Navigation"),
    CommandSpec("browser.page_down", "Page down", "Navigation"),
    CommandSpec("browser.page_up", "Page up", "Navigation"),
    # Keys
    CommandSpec("key.enter", "Enter / confirm", "Keyboard", sensitive=True),
    CommandSpec("key.escape", "Escape / back", "Keyboard"),
    CommandSpec("key.tab", "Tab", "Keyboard"),
    CommandSpec("key.space", "Space", "Keyboard"),
    CommandSpec("key.arrow_left", "Arrow left", "Keyboard"),
    CommandSpec("key.arrow_right", "Arrow right", "Keyboard"),
    CommandSpec("key.arrow_up", "Arrow up", "Keyboard"),
    CommandSpec("key.arrow_down", "Arrow down", "Keyboard"),
    CommandSpec("system.alt_tab", "Switch window (Alt+Tab)", "System"),
    # App control
    CommandSpec("app.toggle_pause", "Pause / resume Gestura", "Gestura", control=True),
    CommandSpec("app.emergency_stop", "Emergency stop", "Gestura", control=True),
    CommandSpec("app.toggle_keyboard", "Show / hide virtual keyboard", "Gestura", control=True),
)

COMMANDS: dict[str, CommandSpec] = {c.id: c for c in _COMMANDS}


def get(command_id: str) -> CommandSpec | None:
    return COMMANDS.get(command_id)


def discrete_commands() -> list[CommandSpec]:
    return [c for c in _COMMANDS if not c.continuous]


def continuous_commands() -> list[CommandSpec]:
    return [c for c in _COMMANDS if c.continuous or c.id == "none"]
