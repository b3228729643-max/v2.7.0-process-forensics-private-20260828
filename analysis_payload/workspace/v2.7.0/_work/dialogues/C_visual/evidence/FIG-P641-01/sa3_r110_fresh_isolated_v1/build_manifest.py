from __future__ import annotations

import csv
import hashlib
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "MANIFEST.sha256.csv"
EXCLUDED = {"MANIFEST.sha256.csv", "WRITE_STOPPED.json"}

paths = sorted(
    (
        path
        for path in ROOT.rglob("*")
        if path.is_file() and path.name not in EXCLUDED
    ),
    key=lambda path: path.relative_to(ROOT).as_posix(),
)

with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
    writer = csv.writer(handle, lineterminator="\n")
    writer.writerow(["relative_path", "bytes", "sha256"])
    for path in paths:
        payload = path.read_bytes()
        writer.writerow(
            [
                path.relative_to(ROOT).as_posix(),
                len(payload),
                hashlib.sha256(payload).hexdigest().upper(),
            ]
        )

print(f"manifest_rows={len(paths)}")
