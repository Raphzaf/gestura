# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
import json, sys, time
import cv2, numpy as np
from gestura.config.settings import Settings
from gestura.vision.frame_processor import FrameProcessor
fist = cv2.imread(sys.argv[1])
def pad(img, w, h):
    c = np.full((h, w, 3), 90, np.uint8); s = min(w / img.shape[1], h / img.shape[0]) * 0.8
    im = cv2.resize(img, (int(img.shape[1] * s), int(img.shape[0] * s)))
    y, x = (h - im.shape[0]) // 2, (w - im.shape[1]) // 2; c[y:y+im.shape[0], x:x+im.shape[1]] = im; return c
out = {}
for (w, h) in ((640, 480), (1280, 720)):
    for label, frame in (("main suivie", pad(fist, w, h)), ("aucune main (recherche)", np.full((h, w, 3), 90, np.uint8))):
        for flabel, face in (("mains seules", False), ("mains + visage", True)):
            s = Settings(); s.tracking.face_enabled = face
            p = FrameProcessor(s.tracking, s.camera)
            for _ in range(15): _, tf = p.process(frame)
            n = 150; c0, t0 = time.process_time(), time.perf_counter()
            for _ in range(n): _, tf = p.process(frame)
            cpu, wall = (time.process_time() - c0) / n * 1000, (time.perf_counter() - t0) / n * 1000
            p.close()
            k = f"{w}x{h} · {label} · {flabel}"
            out[k] = {"latence_ms": round(wall, 1), "cpu_ms": round(cpu, 1), "coeurs_30fps": round(cpu * 0.03, 2),
                      "mains_detectees": len(tf.hands)}
            print(k, out[k], flush=True)
json.dump(out, open(sys.argv[2], "w"), indent=1, ensure_ascii=False)
