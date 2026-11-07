# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
import sys, cv2, numpy as np, glob, os
files = sys.argv[2:]
tiles = []
for f in files:
    im = cv2.resize(cv2.imread(f), (960, 540), interpolation=cv2.INTER_AREA)
    cv2.putText(im, os.path.basename(f)[2:-4] + "s", (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2)
    tiles.append(im)
while len(tiles) % 2: tiles.append(np.zeros_like(tiles[0]))
rows = [np.hstack(tiles[i:i+2]) for i in range(0, len(tiles), 2)]
cv2.imwrite(sys.argv[1], np.vstack(rows))
