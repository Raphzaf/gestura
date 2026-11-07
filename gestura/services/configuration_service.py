# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Load / save settings from the per-user config directory.

* Windows: %APPDATA%\\Gestura\\settings.json
* Other:   $XDG_CONFIG_HOME/gestura/settings.json (~/.config/gestura)

Saves are atomic (temp file + replace). A corrupt or invalid file never stops
the app: it is backed up next to the original and defaults are used.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import time
from pathlib import Path

from pydantic import ValidationError

from ..config.settings import Settings

log = logging.getLogger(__name__)


def config_dir() -> Path:
    override = os.environ.get("GESTURA_CONFIG_DIR")
    if override:
        return Path(override)
    if sys.platform == "win32":
        return Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming")) / "Gestura"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "gestura"


def log_dir() -> Path:
    if sys.platform == "win32" and "GESTURA_CONFIG_DIR" not in os.environ:
        return Path(os.environ.get("LOCALAPPDATA", config_dir())) / "Gestura" / "logs"
    return config_dir() / "logs"


class ConfigurationService:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (config_dir() / "settings.json")
        self.load_error: str = ""

    def load(self) -> Settings:
        if not self.path.exists():
            return Settings()
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return Settings.model_validate(data)
        except (OSError, ValueError, ValidationError) as exc:
            backup = self.path.with_suffix(f".invalid-{int(time.time())}.json")
            try:
                self.path.replace(backup)
            except OSError:
                pass
            self.load_error = f"Settings file was invalid and has been reset (backup: {backup.name}): {exc}"
            log.warning(self.load_error)
            return Settings()

    def save(self, settings: Settings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(settings.model_dump_json(indent=2), encoding="utf-8")
        os.replace(tmp, self.path)
