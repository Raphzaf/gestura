# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Add or check the GPL v3 license header in Gestura's Python sources.

    python scripts/license_headers.py          # add missing headers
    python scripts/license_headers.py --check  # exit 1 if any file lacks one

The header goes after a shebang / encoding line, before the module docstring.
Running it twice changes nothing.
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKER = "SPDX-License-Identifier: GPL-3.0-or-later"
HEADER = """\
# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""
SOURCE_DIRS = ("gestura", "scripts", "tests", "promo")
EXTRA_FILES = ("main.py", "gestura.spec")
SKIP_PARTS = {".venv", "build", "dist", "__pycache__", ".git"}


def source_files() -> list[Path]:
    files = [ROOT / f for f in EXTRA_FILES if (ROOT / f).exists()]
    for d in SOURCE_DIRS:
        files += [p for p in (ROOT / d).rglob("*.py") if not SKIP_PARTS & set(p.relative_to(ROOT).parts)]
    return sorted(set(files))


def has_header(text: str) -> bool:
    return MARKER in "\n".join(text.splitlines()[:5])


def with_header(text: str) -> str:
    lines = text.splitlines(keepends=True)
    prefix = []
    # keep a shebang and/or a PEP 263 encoding declaration on the first lines
    while lines and len(prefix) < 2 and (lines[0].startswith("#!") or "coding" in lines[0][:40] and lines[0].startswith("#")):
        prefix.append(lines.pop(0))
    body = "".join(lines)
    if not body.strip():
        return "".join(prefix) + HEADER
    return "".join(prefix) + HEADER + body


def main(argv: list[str]) -> int:
    check = "--check" in argv
    missing = [p for p in source_files() if not has_header(p.read_text(encoding="utf-8"))]
    if check:
        for p in missing:
            print(f"missing license header: {p.relative_to(ROOT)}")
        return 1 if missing else 0
    for p in missing:
        p.write_text(with_header(p.read_text(encoding="utf-8")), encoding="utf-8")
        print(f"added: {p.relative_to(ROOT)}")
    print(f"{len(missing)} file(s) updated, {len(source_files()) - len(missing)} already had the header")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
