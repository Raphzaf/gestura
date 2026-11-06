# Development

## Setup

```bash
python -m venv .venv
```

Windows: `.venv\Scripts\activate` · Linux/macOS: `source .venv/bin/activate`

```bash
pip install -r requirements-dev.txt
```

```bash
pip install -e . --no-deps
```

Python 3.12 is the primary target (3.11 is supported; NumPy is pinned per version
in `requirements.txt`). Do **not** install `opencv-python` alongside
`opencv-contrib-python` (MediaPipe's dependency) — both provide `cv2`.

Linux only: MediaPipe needs `libegl1 libgles2`, Qt's xcb plugin needs `libxcb-cursor0`
(see `.github/workflows/ci.yml` for the full list).

## Running without a webcam

`--source` accepts a camera index, a video file, an image, or a folder of images:

```bash
python main.py --source path/to/clip.mp4 --page studio --start
```

Smoke test (start tracking, run N seconds, print JSON stats, save screenshots):

```bash
python main.py --source path/to/images --smoke-test 8 --screenshot shot.png
```

## Tests

```bash
python -m pytest
```

* Unit tests for gestures, head pose, safety, commands, controllers, keyboard logic.
* `tests/data/real_landmarks.json`: MediaPipe output captured from sample photos
  (the photos themselves are not committed). Regenerate with
  `python scripts/capture_fixtures.py <image_dir> tests/data/real_landmarks.json`.
* `tests/synthetic.py`: articulated synthetic hand for deterministic sequences.
* Headless GUI tests run on Qt's `offscreen` platform.
* **Real OS input tests** (move the real cursor, click real buttons, type into a
  real field through the virtual keyboard) are opt-in:

```bash
GESTURA_OS_TESTS=1 xvfb-run -a -s "-screen 0 1600x1000x24" python -m pytest tests/test_os_integration.py
```

  On Windows run them from a normal desktop session with `GESTURA_OS_TESTS=1`
  (don't touch the mouse while they run).

## Settings

`gestura/config/settings.py` is the source of truth. After changing a default:

```bash
python -m gestura.config.settings
```

This regenerates `gestura/config/default_settings.json`; a test fails if you forget.
New fields appear automatically in the Settings screen (widget type, range and
label come from the field definition).

## Adding a gesture or command

1. Command: add a `CommandSpec` to `core/gesture_registry.py` and bind it in
   `controllers/__init__.py:register_executors`.
2. Gesture: emit a `GestureEvent` from the relevant engine, add it to the
   `HandGesture`/`HeadGesture` enum and default mappings in `config/settings.py`,
   and a label in `ui/settings/settings_page.py:GESTURE_LABELS`.
3. Add tests with synthetic frames (see `tests/test_hand_gestures.py`).

## Packaging (Windows)

```powershell
.\scripts\build_windows.ps1
```

Builds `dist\Gestura\Gestura.exe` with PyInstaller (`gestura.spec`) and, if Inno
Setup 6 is installed, `installer\Output\Gestura-Setup-0.1.0.exe` (per-user install,
no admin rights). CI builds the executable on every push and uploads it as the
`Gestura-windows-x64` artifact.

Icons: edit `gestura/assets/icon.svg`, then `python scripts/make_icon.py`.
Models: bundled and hash-pinned in `gestura/vision/models.py`;
`python scripts/download_models.py` restores them (`--update` for new versions).

## Logs

* Windows: `%LOCALAPPDATA%\Gestura\logs\gestura.log`
* Linux: `~/.config/gestura/logs/gestura.log`
