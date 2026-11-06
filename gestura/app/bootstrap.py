"""Process setup: logging, Qt application, theme, crash logging."""

from __future__ import annotations

import logging
import logging.handlers
import sys
import threading

from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication

from ..services.configuration_service import log_dir
from ..vision.models import assets_dir

log = logging.getLogger("gestura")


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    try:
        d = log_dir()
        d.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.handlers.RotatingFileHandler(d / "gestura.log", maxBytes=1_000_000,
                                                             backupCount=3, encoding="utf-8"))
    except OSError:
        pass
    logging.basicConfig(level=level, handlers=handlers,
                        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s")
    # MediaPipe / absl are very chatty at INFO
    logging.getLogger("absl").setLevel(logging.WARNING)

    def excepthook(exc_type, exc, tb):
        log.critical("uncaught exception", exc_info=(exc_type, exc, tb))

    sys.excepthook = excepthook
    threading.excepthook = lambda a: log.critical("uncaught exception in %s", a.thread, exc_info=(
        a.exc_type, a.exc_value, a.exc_traceback))


def create_qt_app(argv: list[str]) -> QApplication:
    if sys.platform == "win32":
        try:  # own taskbar group + icon instead of python.exe's
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Gestura.Desktop")
        except Exception:  # noqa: BLE001
            pass
    from ..ui import theme

    qt = QApplication.instance() or QApplication(argv)
    qt.setApplicationName("Gestura")
    qt.setOrganizationName("Gestura")
    qt.setStyle("Fusion")
    font = QFont("Segoe UI" if sys.platform == "win32" else qt.font().family())
    font.setPointSizeF(10)
    qt.setFont(font)
    qt.setStyleSheet(theme.stylesheet())
    icon = assets_dir() / "icon.svg"
    if icon.exists():
        qt.setWindowIcon(QIcon(str(icon)))
    return qt
