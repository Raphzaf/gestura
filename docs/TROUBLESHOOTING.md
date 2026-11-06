# Troubleshooting

## The camera does not open

* **Windows privacy**: Settings › Privacy & security › Camera → allow camera access
  and "Let desktop apps access your camera".
* Close other apps using the camera (Teams, Zoom, the Camera app).
* Settings › Camera › **Detect cameras** (stop the camera first) and pick the right one.
* Try **Capture backend** `msmf` instead of `auto` (DirectShow) or vice versa.
* Unplugging the camera while running shows "Camera lost"; Gestura reconnects
  automatically every 2 seconds.

## Low FPS or high latency

* Gesture Studio shows FPS, latency and per-model times.
* Turn off **Face / head tracking** if you don't use Navigation mode (the face
  model is also skipped automatically when no visible page or mode needs it).
* Keep capture at 640×480; higher resolutions cost CPU without improving tracking.
* Laptops: plug in power — Windows battery saver throttles the CPU.

## Cursor is jittery / lags

* Jittery: lower **Smoothing** (`smoothing_min_cutoff`) or raise **Dead zone**.
* Laggy on fast moves: raise **Responsiveness to fast moves** (`smoothing_beta`).
* Hard to reach screen edges: shrink the **Active region** or raise **Cursor speed**.

## Clicks don't register, or happen by accident

* Run the **Calibration wizard** — the pinch step learns your thresholds.
* Watch the *Thumb–index* meter in Gesture Studio: the bar must cross the left tick
  (closes) and come back past the right tick (opens).
* Accidental clicks: lower `pinch_on_ratio`; raise `pinch_min_frames`.

## Head gestures fire when I just look around

Raise the thresholds (Settings › Head gestures), raise *Hold beyond threshold*,
and re-run the calibration so "neutral" matches how you sit. Head gestures only
fire after returning to neutral, so a sustained look at a second monitor fires at
most once — raise *Turn threshold* if that is still too sensitive.

## Some windows ignore Gestura's input

* **Windows UIPI**: apps running *as administrator* (and Task Manager) ignore
  synthetic input from non-elevated programs. Run Gestura as administrator to
  control them — only if you trust that setup.
* The **UAC prompt, lock screen and Ctrl+Alt+Del screen** run on the secure desktop,
  which no normal application can control. This is a Windows security boundary.
* Games using raw input or anti-cheat may ignore synthetic mouse/keyboard input.

## The virtual keyboard types into the wrong window

The keyboard never takes focus, so keys go to the window that had focus before.
Click (pinch) into the target text field first, then type. Keys are not sent while
**test mode** or an **emergency stop** is active (they still appear in the
keyboard header).

## Emergency stop

Top-bar button, `Ctrl+Shift+G` (in Gestura), `Ctrl+Alt+Shift+G` (system-wide on
Windows), or move the *physical* mouse into any screen corner. Clear it with
**Clear emergency stop** on the Dashboard.

## Settings were reset

If `settings.json` is invalid, Gestura backs it up as
`settings.invalid-<timestamp>.json` next to it and starts with defaults.
Location: `%APPDATA%\Gestura\settings.json` (Windows), `~/.config/gestura/settings.json` (Linux).

## Linux: `libEGL.so.1: cannot open shared object file`

MediaPipe's native library needs EGL: `sudo apt-get install libegl1 libgles2`.
Qt also needs `libxcb-cursor0` for its xcb platform plugin.

## Antivirus flags `Gestura.exe`

Unsigned PyInstaller executables that inject input are sometimes flagged
heuristically. Build from source, or code-sign the executable for distribution.
