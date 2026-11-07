# SPDX-License-Identifier: GPL-3.0-or-later
# Copyright (C) 2026 Gestura contributors
#
# This file is part of Gestura, free and open-source software: you can
# redistribute it and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version. Gestura is distributed
# WITHOUT ANY WARRANTY; see the LICENSE file at the project root for details.
"""Microsoft Store build profile: configuration, secret handling, manifest."""

import importlib.util
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
NS = {"m": "http://schemas.microsoft.com/appx/manifest/foundation/windows10",
      "rescap": "http://schemas.microsoft.com/appx/manifest/foundation/windows10/restrictedcapabilities"}


@pytest.fixture(scope="module")
def bs():
    spec = importlib.util.spec_from_file_location("build_store", ROOT / "store" / "build_store.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


GOOD = {"GESTURA_STORE_IDENTITY_NAME": "12345Pub.Gestura", "GESTURA_STORE_PUBLISHER": "CN=ABCD-1234",
        "GESTURA_STORE_PUBLISHER_DISPLAY_NAME": "Gestura & Co"}


def test_env_file_parsing(bs, tmp_path):
    f = tmp_path / ".env"
    f.write_text('# comment\n\nexport MSSTORE_CLIENT_ID=abc\nMSSTORE_CLIENT_SECRET="s3cr et#x"\n'
                 "GESTURA_STORE_PUBLISHER='CN=X'\nMSSTORE_TENANT_ID=t1 # trailing comment\nBROKEN LINE\n")
    v = bs.parse_env_file(f)
    assert v == {"MSSTORE_CLIENT_ID": "abc", "MSSTORE_CLIENT_SECRET": "s3cr et#x", "GESTURA_STORE_PUBLISHER": "CN=X",
                 "MSSTORE_TENANT_ID": "t1"}


def test_real_environment_wins_over_env_file(bs, tmp_path):
    f = tmp_path / ".env"
    f.write_text("MSSTORE_CLIENT_SECRET=from_file\nMSSTORE_SELLER_ID=file_seller\n")
    cfg = bs.load_config(f, {"MSSTORE_CLIENT_SECRET": "from_ci"})
    assert cfg["MSSTORE_CLIENT_SECRET"] == "from_ci" and cfg["MSSTORE_SELLER_ID"] == "file_seller"


def test_missing_and_invalid_configuration_is_reported(bs, tmp_path):
    with pytest.raises(bs.ConfigError, match="GESTURA_STORE_IDENTITY_NAME"):
        bs.require(bs.load_config(tmp_path / "none", {}), "build")
    with pytest.raises(bs.ConfigError, match="CN="):
        bs.require({**GOOD, "GESTURA_STORE_PUBLISHER": "Gestura"}, "build")
    bs.require(GOOD, "build")
    with pytest.raises(bs.ConfigError, match="MSSTORE_CLIENT_SECRET"):
        bs.require(GOOD, "submit")


def test_secrets_are_masked_in_logs(bs):
    cfg = {**GOOD, "MSSTORE_CLIENT_SECRET": "very-secret-value", "GESTURA_SIGN_CERT_PASSWORD": "p@ss"}
    line = bs.mask("msstore reconfigure --clientSecret very-secret-value && signtool /p p@ss", bs.secrets_of(cfg))
    assert "very-secret-value" not in line and "p@ss" not in line and line.count("****") == 2


def test_manifest_is_rendered_well_formed_and_has_no_secrets(bs):
    cfg = {**GOOD, "MSSTORE_CLIENT_SECRET": "very-secret-value"}
    xml = bs.render_manifest(cfg, "0.3.0.0")
    root = ET.fromstring(xml)
    ident = root.find("m:Identity", NS)
    assert ident.get("Name") == "12345Pub.Gestura" and ident.get("Publisher") == "CN=ABCD-1234"
    assert ident.get("Version") == "0.3.0.0"
    assert root.find("m:Properties/m:PublisherDisplayName", NS).text == "Gestura & Co"
    caps = root.find("m:Capabilities", NS)
    assert caps.find("rescap:Capability", NS).get("Name") == "runFullTrust"
    assert caps.find("m:DeviceCapability", NS).get("Name") == "webcam"
    assert "very-secret-value" not in xml and "${" not in xml


def test_secret_placeholders_are_refused(bs, tmp_path, monkeypatch):
    bad = tmp_path / "AppxManifest.template.xml"
    bad.write_text("<a b='${MSSTORE_CLIENT_SECRET}'/>")
    monkeypatch.setattr(bs, "STORE_DIR", tmp_path)
    with pytest.raises(bs.ConfigError, match="never be written"):
        bs.render_manifest({**GOOD, "MSSTORE_CLIENT_SECRET": "x"}, "1.0.0.0")


def test_store_version_has_four_parts_ending_in_zero(bs):
    v = bs.store_version()
    assert len(v.split(".")) == 4 and v.endswith(".0")


def test_check_mode_renders_layout(bs, tmp_path, monkeypatch):
    monkeypatch.setattr(bs, "OUT", tmp_path / "out")
    monkeypatch.setattr(bs, "LAYOUT", tmp_path / "out" / "layout")
    env = tmp_path / ".env"
    env.write_text("\n".join(f"{k}={v}" for k, v in GOOD.items()))
    for k in GOOD:
        monkeypatch.delenv(k, raising=False)
    assert bs.main(["--check", "--env-file", str(env)]) == 0
    layout = tmp_path / "out" / "layout"
    assert (layout / "AppxManifest.xml").is_file()
    assert {p.name for p in (layout / "Assets").iterdir()} == set(bs.ASSETS)


def test_env_files_and_certificates_are_git_ignored():
    def ignored(path):
        return subprocess.run(["git", "check-ignore", "-q", path], cwd=ROOT).returncode == 0

    for path in ("store/.env", ".env", "store/.env.local", "cert.pfx", "store/signing.p12", "store/out/x.msix"):
        assert ignored(path), path
    for path in ("store/.env.example", "store/build_store.py"):
        assert not ignored(path), path


def test_env_example_contains_no_values():
    for line in (ROOT / "store" / ".env.example").read_text().splitlines():
        if line and not line.startswith("#"):
            key, _, value = line.partition("=")
            assert value == "", f"{key} must stay empty in the committed template"


def test_packaged_detection_uses_get_current_package_full_name():
    from gestura.services import startup_service as ss

    class K:
        def __init__(self, rc):
            self.rc = rc

        def GetCurrentPackageFullName(self, length, buf):  # noqa: N802
            return self.rc

    assert ss.is_packaged(K(15700)) is False  # APPMODEL_ERROR_NO_PACKAGE
    assert ss.is_packaged(K(122)) is True  # ERROR_INSUFFICIENT_BUFFER: running packaged


def test_package_option_requires_submit_and_existing_file(bs, tmp_path, monkeypatch, capsys):
    env = tmp_path / ".env"
    env.write_text(
        "GESTURA_STORE_IDENTITY_NAME=Contoso.Gestura\n"
        "GESTURA_STORE_PUBLISHER=CN=1234-ABCD\n"
        "GESTURA_STORE_PUBLISHER_DISPLAY_NAME=Contoso\n",
        encoding="utf-8",
    )
    for name in bs.VARIABLES:
        monkeypatch.delenv(name, raising=False)
    assert bs.main(["--env-file", str(env), "--package", str(tmp_path / "x.msix")]) == 2
    assert "only used with --submit" in capsys.readouterr().err
    assert bs.main(["--env-file", str(env), "--submit", "--package", str(tmp_path / "x.msix")]) == 2
    assert "package not found" in capsys.readouterr().err
