# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Isolated build profile for the Microsoft Store (MSIX).

    python store/build_store.py --check        # validate config + render manifest/assets (any OS)
    python store/build_store.py                # build the MSIX to upload (Windows)
    python store/build_store.py --sign         # also make a test-signed copy for local install
    python store/build_store.py --submit       # also send it to Partner Center as a draft
    python store/build_store.py --submit --commit   # ...and commit the submission
    python store/build_store.py --submit --package store/out/X.msix   # submit without rebuilding

Everything goes to store/out/ (never to dist/), so it cannot mix with the classic
installer build. Configuration and secrets are read from environment variables;
store/.env fills in the ones that are not already set (the real environment, e.g. CI
secrets, always wins). Secret values are never printed.

The package uploaded to the Store is left unsigned: Microsoft signs it during
certification. --sign only produces a separate copy for testing on your own PC.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
import tomllib
import xml.etree.ElementTree as ET
from pathlib import Path

STORE_DIR = Path(__file__).resolve().parent
ROOT = STORE_DIR.parent
OUT = STORE_DIR / "out"
LAYOUT = OUT / "layout"
DEFAULT_ENV_FILE = STORE_DIR / ".env"

# name -> (required for, is secret)
VARIABLES: dict[str, tuple[str, bool]] = {
    "GESTURA_STORE_IDENTITY_NAME": ("build", False),
    "GESTURA_STORE_PUBLISHER": ("build", False),
    "GESTURA_STORE_PUBLISHER_DISPLAY_NAME": ("build", False),
    "MSSTORE_TENANT_ID": ("submit", True),
    "MSSTORE_SELLER_ID": ("submit", True),
    "MSSTORE_CLIENT_ID": ("submit", True),
    "MSSTORE_CLIENT_SECRET": ("submit", True),
    "MSSTORE_PRODUCT_ID": ("submit", False),
    "GESTURA_SIGN_CERT_PFX": ("sign", False),
    "GESTURA_SIGN_CERT_PASSWORD": ("sign", True),
}
ASSETS = {  # file name -> (width, height)
    "StoreLogo.png": (50, 50),
    "Square44x44Logo.png": (44, 44),
    "Square150x150Logo.png": (150, 150),
    "Wide310x150Logo.png": (310, 150),
}


class ConfigError(Exception):
    pass


def _rel(path: Path) -> str:
    """Path for display: relative to the project when possible."""
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


# --------------------------------------------------------------------------- environment
def parse_env_file(path: Path) -> dict[str, str]:
    """Minimal .env parser: KEY=VALUE lines, optional `export`, quotes, # comments."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, sep, value = line.partition("=")
        if not sep:
            continue
        key, value = key.strip(), value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        else:
            value = value.split(" #", 1)[0].rstrip()
        values[key] = value
    return values


def load_config(env_file: Path, environ: dict[str, str] | None = None) -> dict[str, str]:
    """Real environment first, then the .env file for anything not set."""
    environ = dict(os.environ if environ is None else environ)
    config = {}
    file_values = parse_env_file(env_file)
    for name in VARIABLES:
        value = environ.get(name) or file_values.get(name, "")
        config[name] = value
    return config


def require(config: dict[str, str], *purposes: str) -> None:
    missing = [n for n, (purpose, _) in VARIABLES.items() if purpose in purposes and not config.get(n)]
    if missing:
        raise ConfigError("missing variables (set them in store/.env or the environment): " + ", ".join(missing))
    publisher = config.get("GESTURA_STORE_PUBLISHER", "")
    if "build" in purposes and not publisher.startswith("CN="):
        raise ConfigError("GESTURA_STORE_PUBLISHER must look like 'CN=...' (copy it from Partner Center)")


def secrets_of(config: dict[str, str]) -> list[str]:
    return [config[n] for n, (_, secret) in VARIABLES.items() if secret and config.get(n)]


def mask(text: str, secrets: list[str]) -> str:
    for s in sorted(secrets, key=len, reverse=True):
        if s:
            text = text.replace(s, "****")
    return text


def run(cmd: list[str], secrets: list[str], **kw) -> None:
    print("  $ " + mask(" ".join(f'"{c}"' if " " in c else c for c in cmd), secrets), flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True, **kw)
    out = mask((result.stdout or "") + (result.stderr or ""), secrets).strip()
    if out:
        print("    " + out.replace("\n", "\n    "))
    if result.returncode != 0:
        raise SystemExit(f"command failed with exit code {result.returncode}")


# --------------------------------------------------------------------------- manifest
def store_version() -> str:
    """MSIX needs four numbers; the Store requires the last one to be 0."""
    version = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    parts = [int(p) for p in re.findall(r"\d+", version)[:3]]
    while len(parts) < 3:
        parts.append(0)
    return ".".join(str(p) for p in parts) + ".0"


def render_manifest(config: dict[str, str], version: str) -> str:
    template = (STORE_DIR / "AppxManifest.template.xml").read_text(encoding="utf-8")
    values = {**config, "VERSION": version}

    def sub(m: re.Match) -> str:
        key = m.group(1)
        if key not in values:
            raise ConfigError(f"unknown placeholder ${{{key}}} in the manifest template")
        if VARIABLES.get(key, ("", False))[1]:
            raise ConfigError(f"secret {key} must never be written into the package")
        return (values[key].replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                .replace('"', "&quot;"))

    xml = re.sub(r"\$\{([A-Z0-9_]+)\}", sub, template)
    ET.fromstring(xml.encode("utf-8"))  # must be well-formed
    return xml


# --------------------------------------------------------------------------- assets
def render_assets(dest: Path) -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer
    from PySide6.QtWidgets import QApplication

    # A full QApplication (not a bare QGuiApplication): other Qt code in the same process
    # may need widgets later.
    _app = QApplication.instance() or QApplication([])  # noqa: F841 - needed by QPainter
    svg = QSvgRenderer(str(ROOT / "gestura" / "assets" / "icon.svg"))
    dest.mkdir(parents=True, exist_ok=True)
    for name, (w, h) in ASSETS.items():
        img = QImage(w, h, QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.transparent)
        side = min(w, h)
        p = QPainter(img)
        svg.render(p, QRectF((w - side) / 2, (h - side) / 2, side, side))
        p.end()
        img.save(str(dest / name), "PNG")


# --------------------------------------------------------------------------- tools
def find_sdk_tool(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    kits = Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Windows Kits" / "10" / "bin"
    candidates = sorted(kits.glob(f"10.*/x64/{name}"), reverse=True)
    if not candidates:
        raise ConfigError(f"{name} not found: install the Windows 10/11 SDK")
    return str(candidates[0])


# --------------------------------------------------------------------------- steps
def build(args, config: dict[str, str]) -> Path:
    secrets = secrets_of(config)
    version = store_version()
    print(f"Gestura {version} — Microsoft Store build")
    print("[1/4] manifest and assets")
    if LAYOUT.exists():
        shutil.rmtree(LAYOUT)
    LAYOUT.mkdir(parents=True)
    (LAYOUT / "AppxManifest.xml").write_text(render_manifest(config, version), encoding="utf-8")
    render_assets(LAYOUT / "Assets")
    if args.check:
        print(f"OK: configuration valid, manifest and assets written to {_rel(LAYOUT)}")
        return LAYOUT
    if sys.platform != "win32":
        raise ConfigError("packaging needs Windows (PyInstaller Windows build + makeappx); use --check here")

    print("[2/4] application (PyInstaller, isolated output)")
    run([sys.executable, "-m", "PyInstaller", "--noconfirm", "--distpath", str(OUT / "pyinstaller"),
         "--workpath", str(OUT / "work"), str(ROOT / "gestura.spec")], secrets, cwd=ROOT)
    shutil.copytree(OUT / "pyinstaller" / "Gestura", LAYOUT / "Gestura")

    print("[3/4] MSIX package")
    package = OUT / f"Gestura_{version}_x64.msix"
    run([find_sdk_tool("makeappx.exe"), "pack", "/d", str(LAYOUT), "/p", str(package), "/o"], secrets)
    print(f"  -> {_rel(package)} (unsigned: the Store signs it)")

    if args.sign:
        print("[3b] test-signed copy for local installation")
        require(config, "sign")
        test_pkg = OUT / f"Gestura_{version}_x64_test-signed.msix"
        shutil.copy2(package, test_pkg)
        run([find_sdk_tool("signtool.exe"), "sign", "/fd", "SHA256", "/f", config["GESTURA_SIGN_CERT_PFX"],
             "/p", config["GESTURA_SIGN_CERT_PASSWORD"], str(test_pkg)], secrets)
        print(f"  -> {_rel(test_pkg)} (the certificate subject must equal GESTURA_STORE_PUBLISHER)")
    return package


def submit(args, config: dict[str, str], package: Path) -> None:
    print("[4/4] submission to Partner Center")
    require(config, "submit")
    secrets = secrets_of(config)
    msstore = shutil.which("msstore") or shutil.which("msstore.exe")
    if not msstore:
        raise ConfigError("msstore CLI not found: install the Microsoft Store Developer CLI")
    run([msstore, "reconfigure", "--tenantId", config["MSSTORE_TENANT_ID"], "--sellerId", config["MSSTORE_SELLER_ID"],
         "--clientId", config["MSSTORE_CLIENT_ID"], "--clientSecret", config["MSSTORE_CLIENT_SECRET"]], secrets)
    cmd = [msstore, "publish", str(ROOT), "--inputFile", str(package), "--appId", config["MSSTORE_PRODUCT_ID"]]
    if not args.commit:
        cmd.append("--noCommit")  # draft: review and submit it in Partner Center
    run(cmd, secrets)
    print("  -> submission " + ("committed for certification" if args.commit else "saved as a draft in Partner Center"))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--env-file", type=Path, default=DEFAULT_ENV_FILE, help="default: store/.env")
    p.add_argument("--check", action="store_true", help="validate and render manifest/assets only")
    p.add_argument("--sign", action="store_true", help="also produce a test-signed copy (local install)")
    p.add_argument("--submit", action="store_true", help="send the package to Partner Center")
    p.add_argument("--commit", action="store_true", help="with --submit: commit instead of keeping a draft")
    p.add_argument("--package", type=Path, help="with --submit: send this already-built .msix (no rebuild)")
    args = p.parse_args(argv)
    config = load_config(args.env_file)
    try:
        require(config, "build")
        if args.submit and args.check:
            raise ConfigError("--submit cannot be combined with --check")
        if args.package:
            if not args.submit:
                raise ConfigError("--package is only used with --submit")
            if not args.package.is_file():
                raise ConfigError(f"package not found: {args.package}")
            package = args.package
        else:
            package = build(args, config)
        if args.submit:
            submit(args, config, package)
    except ConfigError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
