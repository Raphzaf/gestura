"""(Re)download the MediaPipe models into gestura/assets/models and verify them.

The models are already bundled in the repository; use this to restore them or,
with --update, to fetch the latest published versions (prints new hashes).
"""

from __future__ import annotations

import hashlib
import sys
import urllib.request

from gestura.vision.models import MODEL_SHA256, MODEL_URLS, assets_dir


def main(update: bool = False) -> int:
    out = assets_dir() / "models"
    out.mkdir(parents=True, exist_ok=True)
    status = 0
    for name, url in MODEL_URLS.items():
        target = out / name
        print(f"downloading {name} …")
        with urllib.request.urlopen(url, timeout=60) as r:  # noqa: S310 - fixed https URL
            data = r.read()
        digest = hashlib.sha256(data).hexdigest()
        if digest != MODEL_SHA256[name] and not update:
            print(f"  hash mismatch ({digest}); not written. Use --update to accept a new model version.")
            status = 1
            continue
        target.write_bytes(data)
        print(f"  ok {len(data)} bytes sha256={digest}")
    return status


if __name__ == "__main__":
    sys.exit(main("--update" in sys.argv))
