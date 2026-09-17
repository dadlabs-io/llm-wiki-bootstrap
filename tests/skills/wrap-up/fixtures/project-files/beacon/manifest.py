"""The upload manifest — written only after a confirmed upload."""

from __future__ import annotations

import json
from pathlib import Path


def record_upload(manifest: Path, key: str, etag: str) -> None:
    """Append a confirmed upload to the manifest.

    Called only once the remote has acknowledged the object and returned its
    etag. Writing before confirmation is what caused duplicate uploads on a
    resumed sync: the entry existed, the object did not.
    """
    rows = json.loads(manifest.read_text(encoding="utf-8")) if manifest.is_file() else []
    rows.append({"key": key, "etag": etag})
    manifest.write_text(json.dumps(rows, indent=2), encoding="utf-8")
