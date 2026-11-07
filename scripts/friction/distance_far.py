# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
import json, sys
from pathlib import Path
import robustness as r
r.CONDITIONS = {"distance_x0.18": lambda im: r.distance(im, 0.18), "distance_x0.12": lambda im: r.distance(im, 0.12)}
r.run(Path(sys.argv[1]), Path(sys.argv[2]))
