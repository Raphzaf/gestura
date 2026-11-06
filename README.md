# Gestura

Hands-free desktop control: move the mouse with your index finger, click by
pinching, scroll with two fingers, navigate pages with head turns and type on a
floating virtual keyboard — using only a regular webcam. All processing runs
locally; no video is stored or uploaded.

Primary target: **Windows 10/11 (x64)**. Built with Python, PySide6, MediaPipe
and OpenCV.

> **Status: early (v0.1.0).** All six milestones are implemented and covered by
> automated tests, but the app has **not yet been used with a live webcam on a
> Windows PC**. See [What has been verified](#what-has-been-verified) before relying on it.

## Quick start (Windows)

Requires **Python 3.12** (3.11 also works) from python.org, 64-bit.

```powershell
git clone https://github.com/Raphzaf/gestura.git
```

```powershell
cd gestura
```

```powershell
py -3.12 -m venv .venv
```

```powershell
.venv\Scripts\activate
```

```powershell
pip install -r requirements.txt
```

```powershell
python main.py
```

Then:

1. Press **Start** on the Dashboard (the camera only turns on when you ask).
2. Gestura starts in **test mode**: gestures are recognised and shown, nothing
   is sent to your computer. Open **Gesture Studio** to watch the landmarks and try gestures.
3. Click **Calibrate…** and follow the six steps (neutral head pose, pinch thresholds, gesture test).
4. Turn **test mode** off on the Dashboard for real control.

**Emergency stop**: the red button in the top bar, `Ctrl+Shift+G` inside Gestura,
`Ctrl+Alt+Shift+G` anywhere (Windows), or push the *physical* mouse into any
screen corner. A held **open palm** pauses/resumes.

Other ways to run: `python -m gestura` or, after `pip install -e .`, `gestura`.
Useful options: `--start` (start tracking immediately), `--page studio`,
`--source <camera index | video file | image folder>`, `--live` / `--test-mode`.

## Gestures

| Hand (Mouse mode) | Action |
|---|---|
| Index finger extended | Move cursor |
| Thumb + index pinch | Left click (two quick pinches = double click) |
| Thumb + middle pinch | Right click |
| Index + middle extended, move up/down | Scroll (left/right: horizontal scroll) |
| Open palm swipe left / right | Previous / next tab |
| Open palm held still (1.2 s) | Pause / resume |
| Fist | Clutch — hand controls ignored while held |

| Head (Navigation mode) | Action |
|---|---|
| Turn left / right | Previous / next page |
| Nod down (twice, to confirm) | Enter |
| Tilt up | Escape |
| Return to neutral | Re-arms head gestures |

Everything is remappable (Settings › Gesture mapping) and every threshold is
configurable. Details, measurements and false-trigger guards: [docs/GESTURES.md](docs/GESTURES.md).

## Features

* **Dashboard** — status of camera, hand and head tracking, engine state, current
  gesture, mode toggles (Mouse / Navigation / Keyboard), live preview.
* **Gesture Studio** — annotated live feed (hand landmarks, face mesh contours, head
  direction, active region), FPS, latency, per-model timings, pinch-ratio meters with
  threshold ticks, head angle meters, gesture log. Works in test mode.
* **Virtual keyboard** — AZERTY and QWERTY, floating, always on top and
  non-activating (it does not steal focus from the app you type into); Shift,
  Caps Lock, Tab, Esc, arrows, Ctrl/Alt/Win shortcuts; Unicode output (é à ç €).
* **Settings** — generated from the validated configuration model: camera,
  tracking, cursor, hand and head thresholds, cooldowns, safety, keyboard,
  overlay, startup (launch at login), gesture mapping.
* **Calibration wizard** — camera position, face, neutral head pose with
  direction check, hand position, pinch thresholds, gesture test.
* **Safety** — test mode by default, pause, emergency stop, confirmation for
  sensitive commands (Enter), allow-listed commands only, safe reset when tracking
  is lost, PyAutoGUI fail-safe, on-screen feedback overlay for every action.

## What has been verified

Development so far ran in a Linux container **without a webcam or Windows**:

| Verified | How |
|---|---|
| Hand/face models, landmarks, head pose | Real MediaPipe inference on sample photos; results stored as regression fixtures |
| Gesture recognition logic | Unit tests with real-photo landmarks and synthetic hand sequences (101 automated tests in total: 97 unit/UI + 4 real-OS-input) |
| Full app (UI, worker thread, preview, telemetry) | Launched under a virtual X display with images as the video source; screenshots reviewed |
| Real OS input | Hand gestures moved the real cursor, clicked a real button and typed into a real text field via the virtual keyboard (X11 / Xvfb) |
| Camera disconnect recovery | Worker test with a simulated camera that stops delivering frames |
| Packaging | PyInstaller bundle built and smoke-tested (Linux); CI builds the Windows executable |
| Windows wheels | All pinned dependencies resolve for win_amd64 on Python 3.11 and 3.12 |

**Not yet verified** (implemented, needs a Windows PC with a webcam):
DirectShow/MSMF capture, real-time gesture feel and default thresholds with a live
user, Win32 `SendInput` horizontal scroll and Unicode typing, the system-wide
emergency hotkey, the keyboard's no-focus-steal behaviour (`WS_EX_NOACTIVATE`),
launch at login, the Inno Setup installer.

## Known limitations

* Cursor control covers the **primary monitor** only.
* Windows does not let normal apps control **elevated (admin) windows**, the UAC
  prompt or the lock screen — see [Troubleshooting](docs/TROUBLESHOOTING.md).
* No drag-and-drop gesture yet. Head-controlled key selection was investigated but
  not implemented (see [docs/GESTURES.md](docs/GESTURES.md#investigation-head-controlled-key-selection)).
* Thresholds were tuned on still photos and synthetic motion; expect to adjust
  them (or re-run calibration) after real use.
* The packaged app is large (~590 MB unpacked): MediaPipe, OpenCV and Qt.

## Documentation

* [Architecture](docs/ARCHITECTURE.md) — layers, threading, safety model
* [Gestures](docs/GESTURES.md) — recognition details and tuning
* [Development](docs/DEVELOPMENT.md) — tests, packaging, adding gestures
* [Troubleshooting](docs/TROUBLESHOOTING.md)

## Privacy

Camera frames are processed in memory on your computer and discarded. Gestura
stores no images or video, sends nothing over the network, and the camera only
runs after you press Start (or enable auto-start). The MediaPipe models
(Apache-2.0, by Google) are bundled in `gestura/assets/models`.
