# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Dark theme: colour tokens and the application stylesheet."""

from __future__ import annotations

BG = "#0e1014"
SURFACE = "#161920"
SURFACE_2 = "#1d212a"
SURFACE_3 = "#252a35"
BORDER = "#2a303c"
TEXT = "#e7e9ef"
MUTED = "#8a93a6"
ACCENT = "#40c4ff"
ACCENT_DIM = "#1f5f7d"
SUCCESS = "#5fd38d"
WARN = "#ffb454"
DANGER = "#ff5a5f"
DANGER_DIM = "#5a2326"

STATE_COLORS = {
    "active": SUCCESS,
    "paused": WARN,
    "stopped": MUTED,
    "emergency": DANGER,
    "on": SUCCESS,
    "starting": ACCENT,
    "off": MUTED,
    "lost": WARN,
    "error": DANGER,
}

_STYLESHEET = f"""
* {{ color: {TEXT}; font-size: 10pt; }}
QMainWindow, QWidget#root {{ background: {BG}; }}
QWidget {{ background: transparent; }}
QToolTip {{ background: {SURFACE_3}; color: {TEXT}; border: 1px solid {BORDER}; padding: 6px; }}

#sidebar {{ background: {SURFACE}; border-right: 1px solid {BORDER}; }}
#brand {{ font-size: 17pt; font-weight: 700; letter-spacing: 0.5px; }}
#brandSub {{ color: {MUTED}; font-size: 8.5pt; }}
#navButton {{
    text-align: left; padding: 10px 14px; border: none; border-radius: 8px;
    color: {MUTED}; font-size: 10.5pt;
}}
#navButton:hover {{ background: {SURFACE_2}; color: {TEXT}; }}
#navButton:checked {{ background: {SURFACE_3}; color: {TEXT}; border-left: 3px solid {ACCENT}; }}
#privacy {{ color: {MUTED}; font-size: 8.5pt; }}

#topbar {{ background: {BG}; border-bottom: 1px solid {BORDER}; }}
#pageTitle {{ font-size: 15pt; font-weight: 600; }}

QFrame#card {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px; }}
#cardTitle {{ color: {MUTED}; font-size: 8.5pt; font-weight: 600; letter-spacing: 1px; }}
#bigValue {{ font-size: 18pt; font-weight: 600; }}
#value {{ font-size: 11pt; }}
#muted {{ color: {MUTED}; }}
#hint {{ color: {MUTED}; font-size: 9pt; }}

QPushButton {{
    background: {SURFACE_3}; border: 1px solid {BORDER}; border-radius: 8px;
    padding: 8px 16px; font-weight: 500;
}}
QPushButton:hover {{ background: #2e3441; }}
QPushButton:pressed {{ background: {SURFACE_2}; }}
QPushButton:disabled {{ color: #59606e; }}
QPushButton#primary {{ background: {ACCENT}; color: #04121a; border: none; font-weight: 700; }}
QPushButton#primary:hover {{ background: #6fd3ff; }}
QPushButton#danger {{
    background: {DANGER}; color: white; border: none; font-weight: 800;
    padding: 10px 18px; letter-spacing: 0.5px;
}}
QPushButton#danger:hover {{ background: #ff7a7e; }}
QPushButton#ghost {{ background: transparent; border: 1px solid {BORDER}; }}

#chip {{
    background: {SURFACE_2}; border: 1px solid {BORDER}; border-radius: 13px;
    padding: 4px 12px; font-size: 9pt;
}}
#banner {{ background: {ACCENT_DIM}; border-radius: 8px; padding: 8px 12px; }}
#bannerDanger {{ background: {DANGER_DIM}; border: 1px solid {DANGER}; border-radius: 8px; padding: 10px 12px; }}

QTabWidget::pane {{ border: 1px solid {BORDER}; border-radius: 10px; top: -1px; background: {SURFACE}; }}
QTabBar::tab {{ background: transparent; color: {MUTED}; padding: 8px 14px; border: none; }}
QTabBar::tab:selected {{ color: {TEXT}; border-bottom: 2px solid {ACCENT}; }}
QGroupBox {{ border: 1px solid {BORDER}; border-radius: 10px; margin-top: 14px; padding: 10px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 4px; color: {MUTED}; }}

QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit {{
    background: {SURFACE_2}; border: 1px solid {BORDER}; border-radius: 6px; padding: 5px 8px;
    min-height: 20px;
}}
QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus, QLineEdit:focus {{ border-color: {ACCENT}; }}
QAbstractSpinBox::up-button, QAbstractSpinBox::down-button {{
    subcontrol-origin: border; width: 22px; border: none; background: {SURFACE_3};
}}
QAbstractSpinBox::up-button {{ subcontrol-position: top right; border-top-right-radius: 6px; }}
QAbstractSpinBox::down-button {{ subcontrol-position: bottom right; border-bottom-right-radius: 6px; }}
QAbstractSpinBox::up-button:hover, QAbstractSpinBox::down-button:hover {{ background: #323949; }}
QAbstractSpinBox::up-arrow {{ image: url(@ASSETS@/ui/arrow_up.svg); width: 10px; height: 6px; }}
QAbstractSpinBox::down-arrow {{ image: url(@ASSETS@/ui/arrow_down.svg); width: 10px; height: 6px; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox::down-arrow {{ image: url(@ASSETS@/ui/arrow_down.svg); width: 10px; height: 6px; }}
QComboBox QAbstractItemView {{ background: {SURFACE_2}; selection-background-color: {SURFACE_3}; }}
QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 4px; border: 1px solid {BORDER}; background: {SURFACE_2}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; image: url(@ASSETS@/ui/check.svg); }}
QCheckBox {{ spacing: 8px; }}
QListWidget {{ background: {SURFACE_2}; border: 1px solid {BORDER}; border-radius: 8px; padding: 4px; }}
QListWidget::item {{ padding: 4px 6px; }}
QScrollArea {{ border: none; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {SURFACE_3}; border-radius: 4px; min-height: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; }}
QSlider::groove:horizontal {{ height: 4px; background: {SURFACE_3}; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: {ACCENT}; width: 14px; margin: -6px 0; border-radius: 7px; }}

#keyButton {{
    background: {SURFACE_2}; border: 1px solid {BORDER}; border-radius: 8px;
    font-size: 13pt; font-weight: 500; padding: 0;
}}
#keyButton:hover {{ background: {SURFACE_3}; border-color: {ACCENT}; }}
#keyButton:pressed {{ background: {ACCENT}; color: #04121a; }}
#keyButton:checked {{ background: {ACCENT_DIM}; border-color: {ACCENT}; }}
QWidget#keyboardWindow {{ background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 14px; }}
"""


def stylesheet() -> str:
    """The stylesheet with asset paths resolved (Qt needs forward slashes)."""
    from ..vision.models import assets_dir

    return _STYLESHEET.replace("@ASSETS@", assets_dir().as_posix())
