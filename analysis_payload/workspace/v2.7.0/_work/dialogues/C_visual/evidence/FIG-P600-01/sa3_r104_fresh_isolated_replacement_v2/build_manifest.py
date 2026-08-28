from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "MANIFEST.csv"
EXCLUDED = {"MANIFEST.csv", "WRITE_STOPPED"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


files = sorted(
    (p for p in ROOT.rglob("*") if p.is_file() and p.name not in EXCLUDED),
    key=lambda p: p.relative_to(ROOT).as_posix(),
)
rows = []
for path in files:
    stat = path.stat()
    utc = datetime.fromtimestamp(stat.st_mtime_ns / 1_000_000_000, timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")
    filetime100ns = stat.st_mtime_ns // 100 + 116444736000000000
    rows.append(
        {
            "relative_path": path.relative_to(ROOT).as_posix(),
            "bytes": stat.st_size,
            "sha256": sha256(path),
            "utc_mtime": utc,
            "filetime_100ns": filetime100ns,
        }
    )

with MANIFEST.open("w", encoding="utf-8-sig", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=("relative_path", "bytes", "sha256", "utc_mtime", "filetime_100ns"))
    writer.writeheader()
    writer.writerows(rows)

# Immediate self-check: manifest never lists itself or the final marker, and
# every current ordinary content file occurs exactly once.
with MANIFEST.open("r", encoding="utf-8-sig", newline="") as f:
    check_rows = list(csv.DictReader(f))
listed = [r["relative_path"] for r in check_rows]
expected = [p.relative_to(ROOT).as_posix() for p in files]
assert listed == expected
assert "MANIFEST.csv" not in listed
assert "WRITE_STOPPED" not in listed
assert len(listed) == len(set(listed))
print(f"MANIFEST_ENTRY_COUNT={len(listed)}")
print("MANIFEST_SELF_LISTED=false")
print("WRITE_STOPPED_LISTED=false")
