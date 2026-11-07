# Changelog

## Unreleased

* Gestura is now licensed under the **GNU GPL v3 or later**: `LICENSE` file at the
  root, SPDX header in every source file (checked by a test and by
  `scripts/license_headers.py --check`), license shown by the installer and shipped
  with the executable. The unused GPL dependency `mouseinfo` is no longer bundled.
* **Microsoft Store build profile** (`store/`): `store/build_store.py` renders the MSIX
  manifest and logos, builds with PyInstaller into `store/out/`, packs with `makeappx`,
  optionally test-signs and submits to Partner Center (`msstore`). Identity and secrets
  come from environment variables / `store/.env` (git-ignored, values masked in logs);
  manual GitHub Actions workflow `Microsoft Store`. In the packaged app, launch at
  sign-in is a Windows startup task (Settings > Apps > Startup) instead of the Run key.

## 0.3.0

* **Two-hand mouse** (Dashboard switch): the control hand moves the cursor, scrolls,
  swipes and sets the volume; the other hand pinches to click, drag and right-click.
  The cursor no longer moves when you click. The preview colours the moving hand blue
  and the clicking hand green.

## 0.2.0

* **Drag and drop**: pinch and hold ½ s, move, release. The mouse button is always
  released if the hand is lost, on pause, stop or emergency stop.
* **Zoom**: spread / bring together two open hands (Ctrl + wheel).
* **Window management**: three-finger swipe left / right snaps the window (Win+←/→);
  maximize, minimize, show desktop and task view can be assigned to any gesture.
* **Volume**: three fingers up / down; media commands (mute, play/pause, next /
  previous track) for any gesture.
* Clicks now fire when the pinch opens (needed to tell a click from a drag); set
  *Pinch and hold to drag* off in Settings › Hand gestures to click on close as before.

## 0.1.0

* First release: cursor, clicks, scroll, swipes, pause, head navigation, virtual
  keyboard, calibration wizard, settings, Windows installer.
