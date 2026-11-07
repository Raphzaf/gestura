# Gestura

Hands-free desktop control: move the mouse with your index finger, click by
pinching, scroll with two fingers, navigate pages with head turns and type on a
floating virtual keyboard — using only a regular webcam. All processing runs
locally; no video is stored or uploaded.

Primary target: **Windows 10/11 (x64)**. Built with Python, PySide6, MediaPipe
and OpenCV.

> **Status: early (v0.2.0).** All six milestones are implemented and covered by
> automated tests, including on Windows in CI, but the app has **not yet been used
> with a live webcam by a real user**. See [What has been verified](#what-has-been-verified).

> 🇫🇷 **Guide d'installation en français : [voir plus bas](#-installation-et-premiers-pas-en-français).**

## Install on Windows

**You need:** Windows 10 or 11 (64-bit), a webcam (built-in or USB), and about
1.5 GB of free disk space. No Python or admin rights are required.

### 1. Download

1. Sign in to GitHub (the repository is private, so downloads need an account with access).
2. Open **[Releases](https://github.com/Raphzaf/gestura/releases/latest)**.
3. Under **Assets**, download one of:
   * **`Gestura-Setup-<version>.exe`**: installer (recommended), or
   * **`Gestura-windows-x64.zip`**: portable version, nothing to install.

### 2. Install

* **Installer**: double-click `Gestura-Setup-<version>.exe` and follow the steps. It
  installs for your user only (no admin rights) and adds Gestura to the Start menu
  (plus an optional desktop shortcut).
* **Portable zip**: right-click the zip → **Extract All…**, open the extracted
  `Gestura` folder and double-click **`Gestura.exe`**. Keep the whole folder together:
  the `.exe` needs the `_internal` folder next to it.

**"Windows protected your PC"?** Gestura is not code-signed yet, so Microsoft
SmartScreen may warn on first launch. Click **More info → Run anyway**. Your
antivirus may also ask, because the app controls the mouse and keyboard.

### 3. Allow the camera

On first start, if the camera does not turn on: **Settings → Privacy & security →
Camera**, enable *Camera access* and *Let desktop apps access your camera*. Close
other apps that use the camera (Teams, Zoom, the Camera app).

### 4. First use (5 minutes)

1. **Start** — on the Dashboard press **Start**. The camera turns on only when you
   ask; "Camera on" shows in the top bar.
2. **Look in Gesture Studio** — you should see your hand skeleton and face mesh.
   Gestura starts in **test mode**: gestures are recognised and listed, but nothing
   is sent to your computer.
3. **Calibrate** — Dashboard → **Calibrate…**. Sit 50–80 cm from the screen with the
   camera at eye level, then follow the six steps (about 2 minutes).
4. **Practise in test mode** — point with your index finger, pinch thumb + index,
   try two fingers up/down to scroll, hold an open palm to pause. Watch each one
   appear in the Gesture Studio log.
5. **Go live** — on the Dashboard switch **Test mode** off. Now:
   * **Mouse mode** (on by default): index finger moves the cursor, a quick pinch clicks,
     pinch-and-hold drags (release to drop), thumb + middle pinch right-clicks, two
     fingers scroll, three fingers up/down change the volume, a quick three-finger swipe
     snaps the window left/right, two open hands spread/closed zoom, a fist is a
     "clutch" to reposition your hand.
   * **Navigation mode**: turn on to go back/forward with head turns; nod twice to press Enter.
   * **Keyboard mode**: shows the floating keyboard; point at a key and pinch.
     Click the text field you want to type into first.
6. **Stop any time** — red **EMERGENCY STOP** button, `Ctrl+Shift+G`,
   `Ctrl+Alt+Shift+G` from any app, the *physical* mouse pushed into a screen corner,
   or hold an open palm (pause/resume).

Optional: Settings → Startup → *Launch Gestura when I sign in*. If something
doesn't work, see [Troubleshooting](docs/TROUBLESHOOTING.md).

**Uninstall**: Windows Settings → Apps → Gestura → Uninstall (or delete the folder
for the portable version). Settings are stored in `%APPDATA%\Gestura`.

### Run from source (developers)

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

Other ways to run: `python -m gestura` or, after `pip install -e .`, `gestura`.
Useful options: `--start` (start tracking immediately), `--page studio`,
`--source <camera index | video file | image folder>`, `--live` / `--test-mode`.
Build the `.exe` yourself with `.\scripts\build_windows.ps1`.

**Publishing a new version** (maintainers): bump `version` in `pyproject.toml`
and push to `main`. The Release workflow tests and builds `Gestura.exe` and the
installer on Windows and publishes them as a GitHub Release named after the version
(nothing happens if that release already exists). You can also run it manually from
**Actions → Release → Run workflow**.

## Gestures

| Hand (Mouse mode) | Action |
|---|---|
| Index finger extended | Move cursor |
| Thumb + index pinch | Left click on release (two quick pinches = double click) |
| Thumb + index pinch, **hold** ½ s, move, release | Drag and drop (files, windows, sliders, selections) |
| Thumb + middle pinch | Right click |
| Index + middle extended, move up/down | Scroll (left/right: horizontal scroll) |
| Index + middle + ring extended, move up/down | Volume up / down |
| Three fingers, quick swipe left / right | Snap window to the left / right half (Win+← / Win+→) |
| **Two** open hands, spread apart / bring together | Zoom in / out (Ctrl + wheel) |
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
configurable. Media commands (volume, mute, play/pause, next/previous track) and window
commands (maximize, minimize, show desktop, task view, snap) can be assigned to any
gesture — for example head tilts to change track or show the desktop. Details, measurements and false-trigger guards: [docs/GESTURES.md](docs/GESTURES.md).

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

Development ran in a Linux container without a webcam; Windows is covered by
GitHub Actions (`windows-latest`, Python 3.11 and 3.12):

| Verified | How |
|---|---|
| Hand/face models, landmarks, head pose | Real MediaPipe inference on sample photos; results stored as regression fixtures |
| Gesture recognition logic | Unit tests with real-photo landmarks and synthetic hand sequences (101 automated tests in total: 97 unit/UI + 4 real-OS-input) |
| Full app (UI, worker thread, preview, telemetry) | Launched under a virtual X display with images as the video source; screenshots reviewed |
| Real OS input | Hand gestures moved the real cursor, clicked a real button and typed into a real text field via the virtual keyboard — on X11 (Xvfb) **and on a Windows desktop session in CI** |
| Camera disconnect recovery | Worker test with a simulated camera that stops delivering frames |
| Packaging | PyInstaller bundle built and smoke-tested on Linux and **on Windows (CI)**; `Gestura.exe` is uploaded as the `Gestura-windows-x64` artifact of every CI run |
| Windows wheels | All pinned dependencies resolve for win_amd64 on Python 3.11 and 3.12 |

**Not yet verified** (implemented, needs a Windows PC with a webcam and a person):
DirectShow/MSMF capture, real-time gesture feel and default thresholds with a live
user, Win32 `SendInput` horizontal scroll and Unicode typing of accented characters,
the system-wide emergency hotkey, the keyboard's no-focus-steal behaviour
(`WS_EX_NOACTIVATE`) against other apps, launch at login, the Inno Setup installer.

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

---

## 🇫🇷 Installation et premiers pas (en français)

**Il vous faut :** Windows 10 ou 11 (64 bits), une webcam (intégrée ou USB) et environ
1,5 Go d'espace disque. Pas besoin de Python ni de droits administrateur.

### 1. Télécharger

1. Connectez-vous à GitHub (le dépôt est privé : il faut un compte qui y a accès).
2. Ouvrez la page **[Releases](https://github.com/Raphzaf/gestura/releases/latest)**.
3. Dans **Assets**, téléchargez au choix :
   * **`Gestura-Setup-<version>.exe`** : l'installateur (recommandé), ou
   * **`Gestura-windows-x64.zip`** : la version portable, sans installation.

### 2. Installer

* **Installateur** : double-cliquez sur `Gestura-Setup-<version>.exe` et suivez les étapes.
  Il s'installe pour votre compte uniquement (sans droits admin) et ajoute Gestura au
  menu Démarrer (raccourci bureau en option).
* **Zip portable** : clic droit sur le zip → **Extraire tout…**, ouvrez le dossier
  `Gestura` et double-cliquez sur **`Gestura.exe`**. Gardez le dossier complet :
  le `.exe` a besoin du dossier `_internal` à côté de lui.

**« Windows a protégé votre ordinateur » ?** Gestura n'est pas encore signé
numériquement : SmartScreen peut afficher cet avertissement au premier lancement.
Cliquez sur **Informations complémentaires → Exécuter quand même**. Votre antivirus
peut aussi demander confirmation, car l'application contrôle la souris et le clavier.

### 3. Autoriser la caméra

Si la caméra ne s'allume pas : **Paramètres → Confidentialité et sécurité → Caméra**,
activez *Accès à la caméra* et *Autoriser les applications de bureau à accéder à votre
caméra*. Fermez les autres applications qui utilisent la caméra (Teams, Zoom, Caméra).

### 4. Premiers pas (5 minutes)

1. **Démarrer** : sur le tableau de bord (Dashboard), cliquez sur **Start**. La caméra ne
   s'allume que quand vous le demandez ; « Camera on » s'affiche en haut.
2. **Regarder dans Gesture Studio** : vous devez voir le squelette de votre main et le
   maillage du visage. Gestura démarre en **mode test** : les gestes sont reconnus et
   affichés, mais rien n'est envoyé à l'ordinateur.
3. **Calibrer** : Dashboard → **Calibrate…**. Asseyez-vous à 50–80 cm de l'écran, caméra
   à hauteur des yeux, et suivez les six étapes (environ 2 minutes).
4. **S'entraîner en mode test** : pointez avec l'index, pincez pouce + index, montez/
   descendez deux doigts pour défiler, gardez la paume ouverte pour mettre en pause.
   Chaque geste apparaît dans le journal de Gesture Studio.
5. **Passer en contrôle réel** : sur le Dashboard, désactivez **Test mode**. Ensuite :
   * **Mode souris** (Mouse mode, activé par défaut) : l'index déplace le curseur,
     un pincement rapide pouce + index clique, un pincement **maintenu** ½ seconde
     attrape (glisser-déposer : déplacez la main puis relâchez pour déposer), pouce +
     majeur fait un clic droit, deux doigts font défiler, trois doigts montés ou descendus
     règlent le volume, un balayage rapide à trois doigts colle la fenêtre à gauche ou à
     droite de l'écran, **deux mains ouvertes** qu'on écarte ou rapproche zooment, le
     poing fermé « débraye » pour repositionner la main.
   * **Mode navigation** (Navigation mode) : tournez la tête pour page précédente /
     suivante ; hochez la tête deux fois pour valider (Entrée).
   * **Mode clavier** (Keyboard mode) : affiche le clavier flottant (AZERTY par défaut) ;
     pointez une touche et pincez. Cliquez d'abord dans le champ où vous voulez écrire.
6. **Arrêter à tout moment** : bouton rouge **EMERGENCY STOP**, `Ctrl+Maj+G`,
   `Ctrl+Alt+Maj+G` depuis n'importe quelle application, la souris *physique* poussée
   dans un coin de l'écran, ou la paume ouverte maintenue (pause / reprise).

Option : Settings → Startup → *Launch Gestura when I sign in* pour lancer Gestura à
l'ouverture de session. En cas de problème : [Troubleshooting](docs/TROUBLESHOOTING.md).

**Désinstaller** : Paramètres Windows → Applications → Gestura → Désinstaller (ou
supprimez le dossier pour la version portable). Les réglages sont dans `%APPDATA%\Gestura`.
