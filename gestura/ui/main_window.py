# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Main window: sidebar navigation, status top bar, page stack."""

from __future__ import annotations

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QCloseEvent, QKeySequence, QShortcut
from PySide6.QtWidgets import (QButtonGroup, QHBoxLayout, QMainWindow, QPushButton, QStackedWidget, QVBoxLayout,
                               QWidget)

from .. import __version__
from ..core.safety_manager import EngineState
from .dashboard.dashboard_page import DashboardPage
from .gesture_studio.studio_page import StudioPage
from .settings.settings_page import SettingsPage
from .widgets.common import StatusChip, label

ENGINE_CHIP = {
    EngineState.STOPPED: ("Stopped", "stopped"),
    EngineState.ACTIVE: ("Active", "active"),
    EngineState.PAUSED: ("Paused", "paused"),
    EngineState.EMERGENCY: ("EMERGENCY STOP", "emergency"),
}


class MainWindow(QMainWindow):
    def __init__(self, app, extra_pages: list[tuple[str, str, QWidget]] | None = None) -> None:
        super().__init__()
        self.app = app
        self.setWindowTitle("Gestura")
        self.resize(1320, 840)
        self.setMinimumSize(1040, 680)

        root = QWidget()
        root.setObjectName("root")
        h = QHBoxLayout(root)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)

        # ---- sidebar
        side = QWidget()
        side.setObjectName("sidebar")
        side.setFixedWidth(220)
        sv = QVBoxLayout(side)
        sv.setContentsMargins(16, 22, 16, 18)
        sv.setSpacing(4)
        sv.addWidget(label("Gestura", "brand"))
        sv.addWidget(label("Hands-free desktop control", "brandSub"))
        sv.addSpacing(22)
        self.stack = QStackedWidget()
        self.nav = QButtonGroup(self)
        self.nav.setExclusive(True)
        self.pages: dict[str, QWidget] = {}
        self.dashboard = DashboardPage(app)
        self.studio = StudioPage(app)
        self.settings_page = SettingsPage(app)
        pages = [("dashboard", "Dashboard", self.dashboard), ("studio", "Gesture Studio", self.studio)]
        pages += extra_pages or []
        pages.append(("settings", "Settings", self.settings_page))
        for key, title, page in pages:
            btn = QPushButton(title)
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda _c=False, k=key: self.show_page(k))
            self.nav.addButton(btn)
            sv.addWidget(btn)
            self.stack.addWidget(page)
            self.pages[key] = page
            page.setProperty("navButton", btn)
            page.setProperty("title", title)
        sv.addStretch(1)
        sv.addWidget(label("All video is processed locally.\nNo footage is stored or uploaded.", "privacy"))
        sv.addWidget(label(f"v{__version__}", "privacy"))
        h.addWidget(side)

        # ---- main column
        col = QVBoxLayout()
        col.setContentsMargins(0, 0, 0, 0)
        col.setSpacing(0)
        top = QWidget()
        top.setObjectName("topbar")
        tb = QHBoxLayout(top)
        tb.setContentsMargins(24, 12, 20, 12)
        self.title = label("Dashboard", "pageTitle")
        tb.addWidget(self.title)
        tb.addStretch(1)
        self.cam_chip = StatusChip("Camera off", "off")
        self.engine_chip = StatusChip("Stopped", "stopped")
        self.test_chip = StatusChip("Test mode", "starting")
        for chip in (self.test_chip, self.cam_chip, self.engine_chip):
            tb.addWidget(chip)
        self.estop = QPushButton("■  EMERGENCY STOP")
        self.estop.setObjectName("danger")
        self.estop.setToolTip("Stops all gesture control and turns the camera off (Ctrl+Shift+G).\n"
                              "Physical mouse to any screen corner also triggers it.")
        self.estop.setCursor(Qt.CursorShape.PointingHandCursor)
        self.estop.clicked.connect(lambda: app.emergency_stop("emergency stop button"))
        tb.addSpacing(8)
        tb.addWidget(self.estop)
        col.addWidget(top)
        col.addWidget(self.stack, 1)
        h.addLayout(col, 1)
        self.setCentralWidget(root)

        sc = QShortcut(QKeySequence("Ctrl+Shift+G"), self)
        sc.setContext(Qt.ShortcutContext.ApplicationShortcut)
        sc.activated.connect(lambda: app.emergency_stop("keyboard shortcut"))

        app.state_changed.connect(self._refresh)
        app.tracking.camera_status.connect(self._on_camera)
        self.stack.currentChanged.connect(self._page_changed)
        self.show_page(app.settings.startup.open_page)
        self._refresh()

    def show_page(self, key: str) -> None:
        page = self.pages.get(key, self.dashboard)
        self.stack.setCurrentWidget(page)
        page.property("navButton").setChecked(True)
        self.title.setText(page.property("title"))

    def _page_changed(self, _i: int) -> None:
        # Only render preview frames when a page that shows them is visible.
        page = self.stack.currentWidget()
        self.app.tracking.set_preview(page in (self.dashboard, self.studio) and not self.isMinimized())

    def _refresh(self) -> None:
        text, state = ENGINE_CHIP[self.app.safety.state]
        self.engine_chip.set(text, state)
        self.test_chip.setVisible(self.app.safety.test_mode)

    def _on_camera(self, status: str, _msg: str) -> None:
        self.cam_chip.set({"on": "Camera on", "off": "Camera off", "starting": "Camera starting",
                           "lost": "Camera lost", "error": "Camera error"}[status], status)

    def changeEvent(self, event) -> None:  # noqa: N802
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange and hasattr(self, "stack"):
            self._page_changed(0)  # stop rendering previews while minimized

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802
        self.app.shutdown()
        super().closeEvent(event)
