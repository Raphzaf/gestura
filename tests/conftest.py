# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
import os

# GUI tests run headless unless a display is explicitly provided for OS tests.
if os.environ.get("GESTURA_OS_TESTS") != "1":
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
