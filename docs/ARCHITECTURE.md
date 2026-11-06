# Gestura architecture

Gestura turns webcam frames into operating-system input. The design goal is that
**perception can never act on the OS directly**: every action passes through a
single, allow-listed, safety-checked path.

```
            ┌──────────── worker thread (QThread "gestura-tracking") ────────────┐
 camera ──▶ │ vision/          gestures/              core/              controllers/ │ ──▶ OS input
 (or video, │ FrameProcessor ─▶ HandGestureEngine ─▶ CommandEngine ──▶  Mouse / Keyboard │    (PyAutoGUI +
  images)   │  hand + face     HeadGestureEngine     │  mapping         Navigation       │     Win32 SendInput)
            │  landmarkers     (pure Python)          ▼                                   │
            │                                   SafetyManager                            │
            └──────────────┬───────────────────────────┬──────────────────────────────────┘
                           │ preview QImage (≤1 queued) │ telemetry ~15 Hz, gesture + command records
                           ▼                            ▼
            ┌──────────────────────── GUI thread (Qt) ─────────────────────────────────┐
            │ GesturaApp (app/application.py) ◀── Dashboard · Gesture Studio · Settings │
            │   start/stop · emergency stop · test mode · settings · calibration wizard │
            │ KeyboardWindow (floating, non-activating) · FeedbackOverlay (click-through)│
            └────────────────────────────────────────────────────────────────────────────┘
```

## Layers

| Package | Responsibility | Depends on |
|---|---|---|
| `gestura/core` | Data types, event bus, command registry (allow-list), command engine, safety manager | nothing (stdlib + numpy) |
| `gestura/vision` | Frame sources, MediaPipe hand & face landmarkers, head pose, preview drawing | core, OpenCV, MediaPipe |
| `gestura/gestures` | Per-frame features, temporal gesture state machines, filters, calibration | core |
| `gestura/controllers` | Mouse / keyboard / navigation / virtual-keyboard actions over an `InputBackend` | core, PyAutoGUI (lazy), ctypes |
| `gestura/services` | Tracking worker thread, configuration persistence, global hotkey, launch-at-login | all of the above, Qt core |
| `gestura/ui` | PySide6 widgets only. Talks to `GesturaApp`, never to controllers | services, Qt widgets |
| `gestura/config` | Pydantic settings model — the single source of truth for every tunable | pydantic |
| `gestura/app` | Entry point, bootstrap (logging, Qt, theme), wiring (`GesturaApp`, `windows.py`) | everything |

`gestures/` and `core/` import neither Qt nor MediaPipe, so all recognition and
safety logic is unit-tested with synthetic or recorded landmarks.

## Data flow for one frame

1. `TrackingWorker` reads a BGR frame (`vision/camera_manager.py`).
2. `FrameProcessor` mirrors it (selfie view), converts to RGB once, and runs the
   hand and face landmarkers **in parallel** (two threads; MediaPipe's C++ graph
   releases the GIL). Measured on a 4-core VM: 36 ms serial → 24 ms parallel.
   Models are created once and reused; VIDEO running mode with strictly
   increasing timestamps enables MediaPipe's temporal tracking.
3. Head pose is decomposed from the face landmarker's 4×4 facial transformation
   matrix (`vision/head_pose_estimator.py`) — no extra solvePnP step.
4. Result → `TrackingFrame` (plain dataclass).
5. `HandGestureEngine` / `HeadGestureEngine` update their state machines and emit
   `GestureEvent`s (e.g. `hand.pinch`, `head.turn_left`, continuous `hand.cursor`).
6. Events of enabled modes go to `CommandEngine.handle()`:
   mapping (settings) → `CommandSpec` from the registry → `SafetyManager.check()` →
   executor (controller method) — or simulated in test mode.
7. OS input is injected **on the worker thread**, so cursor latency never depends
   on UI repaint load.
8. The GUI gets at most one pending preview image (frames are dropped, not queued,
   if the UI is slow) and a telemetry snapshot at ~15 Hz.

## Safety model

* **Allow-list**: `core/gesture_registry.py` lists every executable command. A
  mapping to anything else is ignored; there is no "run program" or arbitrary
  key-combo command.
* **States** (`core/safety_manager.py`): STOPPED → ACTIVE ⇄ PAUSED, and EMERGENCY,
  which only an explicit UI action clears (never a gesture).
* **Test mode** (default at start-up): everything is recognised and logged, nothing
  reaches the OS — including virtual-keyboard keys.
* **Sensitive commands** (Enter) need the same gesture repeated within the
  confirmation window; the overlay prompts "Repeat to confirm".
* **Emergency stop** sources: top-bar button, Ctrl+Shift+G in-app, Ctrl+Alt+Shift+G
  system-wide (Windows), PyAutoGUI fail-safe (physical mouse to a screen corner;
  Gestura's own cursor is kept 1 px from corners so it can never trigger it).
  Emergency stop also turns the camera off and releases held modifiers.
* **Tracking loss**: losing the hand resets pinch/scroll state (nothing stays
  pressed); losing the face disarms head gestures until neutral is seen again;
  losing the camera resets engines and reconnects every 2 s.
* **Privacy**: frames live only in memory; nothing is recorded or uploaded. The
  camera starts only on an explicit Start (or the opt-in auto-start setting).

## Threading rules

* Only the worker thread touches the camera, models and gesture engines.
* Settings are handed to the worker by reference swap (`update_settings`) and
  applied at the top of the next iteration; models are rebuilt only when their
  construction parameters change.
* `SafetyManager` is lock-protected because the worker (palm gesture, fail-safe)
  and the GUI (buttons) both change it; its listeners re-emit through a queued Qt
  signal so UI updates always happen on the GUI thread.
* State snapshots (`HandState`, `HeadState`) are replaced, never mutated, so the
  GUI can read them without locks.

## Deviations from the suggested layout (and why)

* Code lives in an importable `gestura/` package (needed for `pip install`,
  `python -m gestura` and PyInstaller).
* `default_settings.json` and the gesture mappings are generated from one pydantic
  model instead of two hand-written JSON files, so defaults, validation and the
  Settings UI cannot drift apart (a test enforces it).
* No separate `state_manager.py`: app state is `SafetyManager` (engine state) plus
  the `Settings.modes` section; a third store would duplicate them.
* `ui/keyboard/` and `services/hotkey_service.py`, `services/startup_service.py`
  were added for the floating keyboard, global emergency hotkey and launch-at-login.
