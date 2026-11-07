# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Synthesised music bed + sound effects, timed from film_scenes.events(). -> work/bed.wav, work/sfx.wav"""
import os
import sys

import numpy as np
import wave

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.dirname(__file__))
import film_scenes as fs  # noqa: E402
from film_core import DUR, VDIR  # noqa: E402

SR = 48000
N = int(DUR * SR)
t = np.arange(N) / SR
rng = np.random.default_rng(7)


def env_adsr(n, a, d, s_lvl, r):
    e = np.ones(n) * s_lvl
    na, nd, nr = int(a * SR), int(d * SR), int(r * SR)
    e[:na] = np.linspace(0, 1, na)
    e[na:na + nd] = np.linspace(1, s_lvl, nd)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr)
    return e


def onepole_lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):  # small buffers only
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def lp_fft(x, fc, order=2):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X /= np.sqrt(1 + (f / fc) ** (2 * order))
    return np.fft.irfft(X, len(x))


def bp_fft(x, lo, hi):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / np.sqrt(1 + (lo / np.maximum(f, 1)) ** 4) / np.sqrt(1 + (f / hi) ** 4)
    return np.fft.irfft(X, len(x))


def note(f):
    return 440.0 * 2 ** ((f - 69) / 12)


# ------------------------------------------------------------------ music bed
bed = np.zeros((N, 2))
chords = [(0, [50, 57, 62, 66, 69, 76]), (12.6, [47, 54, 62, 66, 69, 73]),   # Dmaj9 -> Bm(add9)
          (23.8, [43, 50, 59, 62, 66, 74]), (32.6, [45, 52, 61, 64, 69, 71]),  # Gmaj7 -> Asus
          (40.5, [50, 57, 62, 66, 69, 76]), (45.6, [50, 57, 62, 69, 74, 78])]  # Dmaj -> D (resolve)
for i, (t0, notes) in enumerate(chords):
    t1 = chords[i + 1][0] if i + 1 < len(chords) else DUR
    a, b = int(max(0, t0 - 0.6) * SR), int(min(DUR, t1 + 0.9) * SR)
    seg_t = t[a:b] - t[a]
    e = np.clip(seg_t / 1.2, 0, 1) * np.clip((seg_t[-1] - seg_t) / 1.2, 0, 1)
    for j, m in enumerate(notes):
        f = note(m)
        for side, det in ((0, -0.12), (1, 0.12)):
            ph = 2 * np.pi * (f + det) * seg_t + j
            tone = np.sin(ph) + 0.25 * np.sin(2 * ph + 0.3) + 0.08 * np.sin(3 * ph)
            lfo = 0.75 + 0.25 * np.sin(2 * np.pi * 0.11 * seg_t + j * 1.7)
            bed[a:b, side] += tone * e * lfo * (0.05 if m < 55 else 0.028)
air = lp_fft(rng.normal(0, 1, N), 2500) * 0.012
bed += np.stack([air, np.roll(air, 337)], 1)
# overall arc: quiet problem scene, swell at the reveal, lift at the montage, resolve
arc = np.interp(t, [0, 5.5, 6.3, 12.0, 40.4, 41.0, 45.4, 46.0, 49.0, 50.0],
                [0.35, 0.45, 0.95, 0.85, 0.85, 1.0, 1.0, 0.8, 0.7, 0.0])
bed *= arc[:, None]
# soft sub pulse (96 BPM) under the demo scenes
beat = 60 / 96
for bt in np.arange(fs.S3, fs.S7 - 0.2, beat):
    i = int(bt * SR)
    n = int(0.45 * SR)
    tt = np.arange(n) / SR
    k = np.sin(2 * np.pi * (48 + 40 * np.exp(-tt * 30)) * tt) * np.exp(-tt * 7) * 0.10
    bed[i:i + n] += k[:min(n, N - i), None]

# -------------------------------------------------------------------- sfx
sfx = np.zeros((N, 2))


def add(t0, sig, pan=0.0, gain=1.0):
    i = int(t0 * SR)
    if i >= N:
        return
    sig = sig[:N - i]
    L, R = np.sqrt((1 - pan) / 2), np.sqrt((1 + pan) / 2)
    sfx[i:i + len(sig), 0] += sig * L * gain
    sfx[i:i + len(sig), 1] += sig * R * gain


def whoosh(dur=0.7):
    n = int(dur * SR)
    x = rng.normal(0, 1, n)
    e = np.sin(np.linspace(0, np.pi, n)) ** 2
    return bp_fft(x, 400, 3500) * e * 0.22


def click():
    n = int(0.09 * SR)
    tt = np.arange(n) / SR
    body = np.sin(2 * np.pi * 1900 * tt) * np.exp(-tt * 90) * 0.5
    snap = rng.normal(0, 1, n) * np.exp(-tt * 300) * 0.3
    return body + bp_fft(snap, 2000, 9000)


def key_tap():
    n = int(0.07 * SR)
    tt = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1300 * tt) * np.exp(-tt * 110) * 0.28 +
            bp_fft(rng.normal(0, 1, n), 1500, 7000) * np.exp(-tt * 260) * 0.2)


def tone(freqs, dur, decay, gain=0.25, attack=0.004):
    n = int(dur * SR)
    tt = np.arange(n) / SR
    s = sum(np.sin(2 * np.pi * f * tt) + 0.2 * np.sin(4 * np.pi * f * tt) for f in freqs) / len(freqs)
    return s * np.minimum(tt / attack, 1) * np.exp(-tt * decay) * gain


def swish():
    n = int(0.35 * SR)
    x = rng.normal(0, 1, n)
    e = np.sin(np.linspace(0, np.pi, n)) ** 3
    return bp_fft(x, 1500, 6000) * e * 0.16


for when, kind in fs.events():
    if kind == "whoosh":
        add(when - 0.35, whoosh(), 0.0, 0.9)
    elif kind == "click":
        add(when, click(), 0.25)
    elif kind == "key":
        add(when, key_tap(), rng.uniform(-0.3, 0.3))
    elif kind == "enter":
        add(when, click(), 0.0, 1.1)
        add(when + 0.02, tone([880, 1320], 0.5, 9, 0.12))
    elif kind == "scroll_tick":
        add(when, key_tap() * 0.35, 0.3)
    elif kind == "tick_soft":
        add(when, tone([2400], 0.08, 60, 0.05), rng.uniform(-0.5, 0.5))
    elif kind == "camera_on":
        add(when, tone([1046.5, 1568], 0.35, 12, 0.16))
    elif kind == "chime_soft":
        add(when, tone([587.3, 880, 1174.7], 1.6, 2.6, 0.12, attack=0.02))
    elif kind == "pause":
        add(when, tone([659.3], 0.3, 10, 0.14))
        add(when + 0.12, tone([523.3], 0.45, 7, 0.14))
    elif kind == "swish":
        add(when - 0.05, swish(), 0.4 if when < 29 else -0.4)
    elif kind == "confirm_prompt":
        add(when, tone([784], 0.16, 22, 0.13))
        add(when + 0.15, tone([784], 0.16, 22, 0.13))
    elif kind == "confirm":
        add(when, tone([784, 1174.7], 0.6, 6, 0.16))
    elif kind == "keyboard_in":
        add(when, whoosh(0.45) * 0.6, -0.1)
    elif kind == "cut":
        add(when, tone([3200], 0.05, 80, 0.06))
    elif kind == "toggle":
        add(when, click() * 0.6, 0.2)
        add(when + 0.01, tone([1174.7], 0.25, 14, 0.07))
    elif kind == "sonic_logo":
        # three-note signature: D5 - A5 - F#6 over a soft sub
        for k_, (f, dt) in enumerate(((587.33, 0.0), (880.0, 0.16), (1479.98, 0.34))):
            add(when + dt, tone([f, f * 2.0], 2.6, 1.6, 0.16 - k_ * 0.02, attack=0.01), [-0.25, 0.25, 0.0][k_])
        add(when, tone([73.4], 2.6, 1.4, 0.18, attack=0.03))

for name, sig in (("bed", bed), ("sfx", sfx)):
    peak = np.abs(sig).max()
    print(name, "peak", round(float(peak), 3))
    x = np.clip(sig / max(1.0, peak * 1.05), -1, 1)
    pcm = (x * (2 ** 23 - 1)).astype("<i4")
    raw = np.stack([pcm & 0xFF, (pcm >> 8) & 0xFF, (pcm >> 16) & 0xFF], -1).astype(np.uint8).reshape(-1, 6)
    with wave.open(os.path.join(VDIR, "work", f"{name}.wav"), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(3)
        w.setframerate(SR)
        w.writeframes(raw.tobytes())
