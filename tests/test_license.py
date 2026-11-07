# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""The project is GPL v3: the license text is present and every source file says so."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _headers():
    spec = importlib.util.spec_from_file_location("license_headers", ROOT / "scripts" / "license_headers.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_license_file_is_gpl_v3():
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "GNU GENERAL PUBLIC LICENSE" in text and "Version 3, 29 June 2007" in text
    assert "END OF TERMS AND CONDITIONS" in text


def test_every_source_file_has_the_license_header():
    mod = _headers()
    files = mod.source_files()
    assert len(files) > 50
    missing = [str(p.relative_to(ROOT)) for p in files if not mod.has_header(p.read_text(encoding="utf-8"))]
    assert missing == [], "run: python scripts/license_headers.py"


def test_header_insertion_keeps_shebang_and_is_idempotent():
    mod = _headers()
    src = "#!/usr/bin/env python\n\"\"\"Doc.\"\"\"\nx = 1\n"
    once = mod.with_header(src)
    assert once.startswith("#!/usr/bin/env python\n# SPDX-License-Identifier: GPL-3.0-or-later")
    assert once.endswith('"""Doc."""\nx = 1\n')
    assert mod.has_header(once)
    assert mod.with_header("") == mod.HEADER


def test_app_links_to_source_and_license():
    """GPL: distributed builds (Store, installer) must say where the source is."""
    import gestura

    assert gestura.SOURCE_URL.startswith("https://github.com/")
    text = (Path(__file__).resolve().parent.parent / "gestura" / "ui" / "main_window.py").read_text(encoding="utf-8")
    assert "SOURCE_URL" in text and "GPL v3" in text
