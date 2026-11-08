# Gestures

All gestures are mapped to commands in **Settings › Gesture mapping**; every
threshold below is adjustable in **Settings › Hand gestures / Head gestures / Cursor**.
Use **Gesture Studio** (with test mode on) to see exactly what the recogniser sees.

## Hand (Mouse mode)

| Gesture | Default action | How it is recognised |
|---|---|---|
| Index finger extended (other fingers folded) | Move cursor | Pose `point`, debounced over 3 frames; index fingertip mapped from the *active region* (grey rectangle) to the whole screen, smoothed with a One-Euro filter |
| Thumb + index pinch | Left click | Thumb–index distance / palm size < 0.25 for 2 frames; re-opens above 0.38 (hysteresis). The click fires when the pinch **opens** (so a held pinch can become a drag); with `drag_enabled` off it fires on close |
| Thumb + index pinch held ≥ 450 ms | Drag and drop | The left button goes down where the cursor was aimed (the cursor is frozen while pinching), the cursor then follows the hand while pinched, and opening the pinch releases the button. Losing the hand, pausing, stopping or the emergency stop always release it |
| Two quick pinches | Double click | Second pinch within 450 ms. Executed as two clicks, exactly like a mouse, so the OS forms the double click |
| Thumb + middle pinch | Right click | Same thresholds on thumb–middle; 600 ms cooldown |
| Index + middle extended, move hand up/down | Scroll | Pose `two_fingers`; vertical hand motion → wheel notches (hand up = scroll up). Dominant-axis only; horizontal motion scrolls horizontally |
| Two open hands, spread apart / bring together | Zoom in / out | Both hands in pose `open_palm` (debounced); the distance between palm centres is smoothed and turned into steps, 12 per frame-width, max 2 per frame. Each step is Ctrl + one wheel notch, which zooms in browsers, PDF / photo viewers, Office and maps on any keyboard layout. One-palm gestures (pause, swipes) are suspended while zooming and for 1 s after |
| Three fingers, quick horizontal swipe | Snap window left / right | Same swipe rules as the open palm (distance, duration, monotonic, mostly horizontal); sends Win+← / Win+→. Volume only reacts to mostly-vertical motion, so a swipe never changes the volume |
| Index + middle + ring extended, move hand up/down | Volume up / down | Pose `three_fingers` (pinky folded); vertical motion is accumulated into steps, 30 steps per frame height (each step = one system volume key press, 2 % on Windows), at most 3 steps per frame; same dead zone as scrolling |
| Open palm, fast horizontal swipe | Previous / next tab | Palm centre travels > 22 % of frame width within 350 ms, ≥70 % of steps in the same direction, mostly horizontal; 1 s cooldown |
| Open palm held still | Pause / resume | Pose `open_palm` held for 1.2 s while the palm moves < 0.35 frame-widths/s; 2 s cooldown; must leave the pose before it can fire again |
| Fist | Clutch (do nothing) | While a fist is held, the hand produces no events — use it to reposition your hand |

### Window commands

`Snap window left/right` (Win+←/→), `Maximize` (Win+↑), `Minimize` (Win+↓),
`Show desktop` (Win+D) and `Task view` (Win+Tab) can be assigned to any gesture.
Closing windows is deliberately not offered: it can lose work.

### Media commands

`Volume up`, `Volume down`, `Mute / unmute`, `Play / pause media`, `Next track` and
`Previous track` send the standard multimedia keys, so they work with the Windows
volume, Spotify, browsers (YouTube, Netflix…), VLC and any app that honours media keys.
Assign them to any gesture in Settings › Gesture mapping; head tilts to the shoulders
(unmapped by default) are a good fit for next / previous track.

### Two-hand mouse

With *Two-hand mouse* on (Dashboard or Settings › Hand gestures), the hands get roles:

* **Movement hand** = the control hand (Settings › Tracking, right by default): cursor,
  scroll, volume, three-finger and palm swipes, palm-hold pause, fist clutch. Its own
  pinches are ignored, so the cursor never needs to freeze while you aim.
* **Click hand** = the other hand: thumb + index (click on release, hold to drag while
  the movement hand moves), thumb + middle (right click). Nothing else it does triggers
  an action, and a fist on the movement hand does not block its clicks.
* Roles come from MediaPipe's handedness; if both hands get the same label, the hand on
  the control-hand side of the mirrored image moves.
* Either hand may leave the view: the other keeps working. If the click hand disappears
  during a drag, the button is released. Two open hands still zoom.

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

## Eyes & face (Hands-free mouse mode)

For people who cannot use their hands (or whose hands are busy): the eyes and the
head move the pointer, the eyes and the face click. Turn it on with
**Dashboard › Hands-free mouse (eyes & head)**.

### Pointer

| Pointer | How it works | Calibration |
|---|---|---|
| **Eyes + head** (recommended) | Look at a far-away target: after ¼ s the pointer jumps there. Small head movements then fine-tune it. | Eyes (Dashboard › *Calibrate eyes…*) |
| **Eyes only** | The pointer follows your gaze; movements smaller than 3.5 % of the screen are ignored to hold it steady. | Eyes |
| **Head only** | The head is a pointer: turn ±14° to reach the sides, tilt ±10° to reach the top and bottom. Most precise. | Head neutral pose (*Calibrate…*) |

Until the eyes are calibrated, *Eyes + head* and *Eyes only* use the head pointer.
While the head drives the pointer, the Navigation-mode head gestures are muted (a
head turn moves the pointer instead of going back a page). When a hand is controlling
the mouse in Mouse mode, the hand has priority over the face pointer; winks keep working.

**Eye calibration** — a full-screen dot moves to 9 positions: follow it with your
eyes, head still (about 25 s, nothing to click). 4 more dots then *measure* the
accuracy, which is shown in pixels with advice. Webcam eye tracking is coarse:
expect roughly 100–250 px on a 1080p screen, depending on light, webcam and
glasses. That is why the hybrid pointer lets the head do the last centimetres.

How it works: the iris centre (landmarks 468 / 473) is measured in each eye's own
frame (along and across the corner-to-corner axis, divided by the eye width), plus
the eye opening (the upper lid follows vertical gaze). A second-order polynomial
fitted with ridge regression maps these to the screen; head rotation is added
physically (gaze = head direction + eye-in-head direction). See
`gestura/gestures/gaze.py`.

### Eye and face actions (all remappable)

| Gesture | Default action |
|---|---|
| **Left wink** (left eye closed 150–800 ms, right eye open) | Left click |
| **Right wink** | Right click |
| **Long left wink** (≥ 0.8 s) | Drag: press the button; long left wink again to drop |
| **Long right wink** | Re-centre the head pointer |
| **Long blink** (both eyes ≥ 0.6 s) | Double click |
| **Eyes closed 2 s** | Pause / resume Gestura |
| **Raise eyebrows** | Scroll mode on / off: tilt (or look) up / down to scroll, back to centre to stop |
| **Dwell** (pointer still 1 s, *Dwell click* switch) | Left click |
| Double blink, open mouth, smile | unmapped (available) |

Guards against accidental clicks:

* **Natural blinks do nothing.** They close both eyes for ~100–400 ms; a wink needs
  one eye open, a long blink needs ≥ 600 ms.
* **Per-eye calibration on the fly**: each eye's "open" size is its 85th percentile
  over the last ~8 s, so no setup is needed and narrow or droopy eyes work. Closed
  = below 55 % of that size, open again = above 75 % (hysteresis).
* **A wink that turns into a blink is cancelled**; the other eye may squint a
  little once the wink has started.
* **The pointer freezes while an eye closes** and goes back to where it was 0.12 s
  before: closing lids pull the iris landmarks down, which would otherwise move the
  pointer just before the click.
* Expressions are measured against a rolling neutral face and must be held 0.3 s.
* 0.5 s between two eye / face actions; dwell clicks once per rest (move away to
  re-arm). A ring next to the pointer shows the dwell progress and scroll mode.

Gesture Studio's *Eyes & face* card shows both eyes' opening against the thresholds,
the mouth, smile and eyebrow levels, and what is about to happen. Every threshold is
in **Settings › Eyes & face**; every action in **Settings › Gesture mapping**.

**Typing with the eyes**: show the virtual keyboard (Keyboard mode), enlarge it
(Settings › Keyboard › Size) and click keys with winks or dwell.

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

Done in 0.4.0: the head pointer and dwell click are part of the hands-free mouse
(see *Eyes & face* above), with winks as faster clicks. Row/column scanning is
still not implemented.
