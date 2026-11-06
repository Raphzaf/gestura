"""Builds the main window with all pages and dialogs."""

from __future__ import annotations


def build_main_window(app):
    from ..ui.main_window import MainWindow

    return MainWindow(app)
