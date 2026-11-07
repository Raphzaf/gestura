# Gestures

All gestures are mapped to commands in **Settings › Gesture mapping**; every
threshold below is adjustable in **Settings › Hand gestures / Head gestures / Cursor**.
Use **Gesture Studio** (with test mode on) to see exactly what the recogniser sees.

## Hand (Mouse mode)

| Gesture | Default action | How it is recognised |
|---|---|---|
| Index finger extended (other fingers folded) | Move cursor | Pose `point`, debounced over 3 frames; index fingertip mapped from the *active region* (grey rectangle) to the whole screen, smoothed with a One-Euro filter |
| Thumb + index pinch | Left click | Thumb–index distance / palm size < 0.25 for 2 frames; re-opens above 0.38 (hysteresis). Fires once per pinch |
| Two quick pinches | Double click | Second pinch within 450 ms. Executed as two clicks, exactly like a mouse, so the OS forms the double click |
| Thumb + middle pinch | Right click | Same thresholds on thumb–middle; 600 ms cooldown |
| Index + middle extended, move hand up/down | Scroll | Pose `two_fingers`; vertical hand motion → wheel notches (hand up = scroll up). Dominant-axis only; horizontal motion scrolls horizontally |
| Index + middle + ring extended, move hand up/down | Volume up / down | Pose `three_fingers` (pinky folded); vertical motion is accumulated into steps, 30 steps per frame height (each step = one system volume key press, 2 % on Windows), at most 3 steps per frame; same dead zone as scrolling |
| Open palm, fast horizontal swipe | Previous / next tab | Palm centre travels > 22 % of frame width within 350 ms, ≥70 % of steps in the same direction, mostly horizontal; 1 s cooldown |
| Open palm held still | Pause / resume | Pose `open_palm` held for 1.2 s while the palm moves < 0.35 frame-widths/s; 2 s cooldown; must leave the pose before it can fire again |
| Fist | Clutch (do nothing) | While a fist is held, the hand produces no events — use it to reposition your hand |

### Media commands

`Volume up`, `Volume down`, `Mute / unmute`, `Play / pause media`, `Next track` and
`Previous track` send the standard multimedia keys, so they work with the Windows
volume, Spotify, browsers (YouTube, Netflix…), VLC and any app that honours media keys.
Assign them to any gesture in Settings › Gesture mapping; head tilts to the shoulders
(unmapped by default) are a good fit for next / previous track.

### How poses are computed

Per frame, using MediaPipe's metric *world* landmarks (independent of distance,
image aspect ratio and in-plane rotation):

* **Reach** of each finger = straight-line distance wrist→fingertip divided by the
  length of the bone chain. Straight ≈ 0.93–0.99; curled ≈ 0.45–0.70.
  Extended ≥ 0.84, curled < 0.78 (the gap is an uncertainty band).
* **Pinch ratio** = thumb-tip ↔ fingertip distance divided by palm size
  (wrist ↔ middle knuckle).

### False-trigger guards (measured on real photos)

Landmarks from real photos are stored in `tests/data/real_landmarks.json` and used
as regression tests.

| Trap | Measurement | Guard |
|---|---|---|
| A fist looks like a pinch | fist: thumb–index 0.33, thumb–middle 0.36 | Left pinch requires thumb–middle ≥ 1.4 × thumb–index *and* index reach ≥ 0.55 (fist: 0.49) |
| Pointing with the thumb resting on the middle finger looks like a right-click | pointing: thumb–middle 0.25 | Right pinch requires middle-finger reach ≥ 0.60 (pointing: 0.46) and thumb–index ≥ 1.4 × thumb–middle |
| A relaxed hand has thumb near index | relaxed: thumb–index 0.27 | Pinch closes below 0.25 and must transition from open (> 0.38) |
| Pinching bends the index, changing the pose | — | Pose updates are frozen while a pinch is forming; cursor freezes during pinch and 150 ms after a click so clicks land where you aimed |

## Head (Navigation mode)

| Gesture | Default action |
|---|---|
| Turn right | Next page (Alt+Right) |
| Turn left | Previous page (Alt+Left) |
| Nod down | Enter — **sensitive: nod twice** within 2.5 s |
| Tilt up | Escape |
| Tilt to shoulder (left/right) | unmapped (available) |

Angles come from the face landmarker's facial transformation matrix, relative to
your calibrated neutral pose. A head gesture fires only when **all** hold:

1. **Armed**: the head rested in the neutral zone (< 40 % of every threshold) for
   150 ms. After each gesture — and whenever the face is lost — the engine disarms,
   so you must return to neutral before the next gesture.
2. **One axis dominates** by ≥ 1.5× (rejects diagonal looking-around).
3. Deflection beyond the threshold (turn 18°, nod 13°, tilt-up 13°) for ≥ 220 ms
   (brief glances are ignored).
4. 900 ms cooldown since the last head gesture.

Run the **Calibration wizard** once: it captures your neutral pose and asks you to
turn right and nod once, learning the sign of each axis for your camera.

## Virtual keyboard (Keyboard mode)

Point at a key and pinch to press it. Shift applies to the next character (select
twice to lock); Caps Lock affects letters; Ctrl/Alt/Win stay held until the next
key (Ctrl, then C → Ctrl+C). Characters are typed as Unicode, so AZERTY output
(é, è, à, ç, ù, €) does not depend on the Windows keyboard layout.

### Investigation: head-controlled key selection

Considered for users without reliable hand control:

* **Head-pointer** (head yaw/pitch → cursor): feasible with the existing pose
  stream, but resolution is coarse (±20° of comfortable motion over ~1,900 px ≈
  50 px/°) and the head-gesture navigation would have to be disabled meanwhile.
  Would need dwell-to-click (hover N ms) rather than nod-to-click, because a nod
  moves the pointer.
* **Row/column scanning** with nod to select: robust and low-effort, but slow
  (~2–4 s per character).

Recommendation for a follow-up: a "head pointer" mode with dwell clicking, built
as a new continuous head gesture mapped to `mouse.move`, plus a dwell-click
timer in the command layer. Not implemented in this version.
