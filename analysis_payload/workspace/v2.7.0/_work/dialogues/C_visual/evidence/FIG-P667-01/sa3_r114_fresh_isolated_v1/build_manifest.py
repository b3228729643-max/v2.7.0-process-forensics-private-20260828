from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P667-01\sa3_r114_fresh_isolated_v1")
MANIFEST = ROOT / "MANIFEST.csv"
MARKER = ROOT / "WRITE_STOPPED"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


if MARKER.exists():
    raise RuntimeError("Refusing to rebuild manifest after WRITE_STOPPED exists")

files = sorted(
    (path for path in ROOT.rglob("*") if path.is_file() and path.name not in {MANIFEST.name, MARKER.name}),
    key=lambda path: path.relative_to(ROOT).as_posix().casefold(),
)
rows = [
    {
        "relative_path": path.relative_to(ROOT).as_posix(),
        "bytes": path.stat().st_size,
        "sha256": digest(path),
    }
    for path in files
]
with MANIFEST.open("w", encoding="utf-8-sig", newline="") as stream:
    writer = csv.DictWriter(stream, fieldnames=["relative_path", "bytes", "sha256"])
    writer.writeheader()
    writer.writerows(rows)

print(json.dumps({
    "manifest_rows": len(rows),
    "manifest_bytes": MANIFEST.stat().st_size,
    "manifest_sha256": digest(MANIFEST),
}, ensure_ascii=False))
