"""Command-line entry point: `gestura`, `python -m gestura` or `python main.py`."""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from pathlib import Path

log = logging.getLogger("gestura")


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(prog="gestura", description="Hands-free desktop control.")
    p.add_argument("--source", help="camera index, video file, image file or image folder "
                                    "(default: camera from settings)")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--test-mode", dest="test_mode", action="store_true", default=None,
                      help="start in test mode (gestures shown, never executed)")
    mode.add_argument("--live", dest="test_mode", action="store_false",
                      help="start with real control enabled")
    p.add_argument("--start", action="store_true", help="start tracking immediately")
    p.add_argument("--page", choices=["dashboard", "studio", "keyboard", "settings"], help="page to open")
    p.add_argument("--config-dir", help="use this folder for settings and logs")
    p.add_argument("--smoke-test", type=float, metavar="SECONDS",
                   help="start tracking, run for SECONDS, print stats as JSON and exit")
    p.add_argument("--screenshot", metavar="PNG", help="with --smoke-test: save a window screenshot")
    p.add_argument("--verbose", action="store_true")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.config_dir:
        os.environ["GESTURA_CONFIG_DIR"] = args.config_dir

    from .bootstrap import create_qt_app, setup_logging

    setup_logging(args.verbose)
    qt = create_qt_app(sys.argv[:1])

    from ..services.configuration_service import ConfigurationService
    from .application import GesturaApp
    from .windows import build_main_window

    test_mode = True if args.smoke_test and args.test_mode is None else args.test_mode
    app = GesturaApp(ConfigurationService(), source_spec=args.source, force_test_mode=test_mode)
    window = build_main_window(app)
    if args.page:
        window.show_page(args.page)
    if app.settings.startup.start_minimized and not args.smoke_test:
        window.showMinimized()
    else:
        window.show()

    if args.start or args.smoke_test or app.settings.startup.auto_start_tracking:
        app.start()

    if args.smoke_test:
        from PySide6.QtCore import QTimer

        stats: dict = {}
        app.tracking.telemetry.connect(lambda t: stats.update(
            fps=round(t.fps, 1), latency_ms=round(t.latency_ms, 1), hand_ms=round(t.hand_ms, 1),
            face_ms=round(t.face_ms, 1), hands=t.hands_visible, face=t.face_visible,
            pose=t.hand.pose.value, head=None if not t.head.visible else
            [round(t.head.yaw, 1), round(t.head.pitch, 1), round(t.head.roll, 1)]))
        gestures: list[str] = []
        app.tracking.gesture.connect(lambda e: gestures.append(e.label))
        status: list[str] = []
        app.tracking.camera_status.connect(lambda s, m: status.append(f"{s}: {m}"))

        def finish() -> None:
            if args.screenshot:
                Path(args.screenshot).parent.mkdir(parents=True, exist_ok=True)
                window.grab().save(args.screenshot)
            frames = app.tracking.worker.frames_processed if app.tracking.worker else 0
            print(json.dumps({"frames": frames, "last": stats, "gestures": gestures[-20:],
                              "status": status, "backend_error": app.backend_error}, indent=1))
            window.close()
            qt.exit(0 if frames > 0 else 1)

        QTimer.singleShot(int(args.smoke_test * 1000), finish)

    return qt.exec()


if __name__ == "__main__":
    sys.exit(main())
