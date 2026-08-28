from __future__ import annotations

import csv
import hashlib
import os
import stat
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P605-01\sa1_r104_fresh_isolated_v1").resolve()
MANIFEST = ROOT / "MANIFEST.csv"
MARKER = ROOT / "WRITE_STOPPED"
HANDOFF_ID = "C-FIG-P605-01-R104-SA1-FRESH-ISOLATED-V1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def utc_iso_100ns(mtime_ns: int) -> str:
    seconds, remainder_ns = divmod(mtime_ns, 1_000_000_000)
    prefix = datetime.fromtimestamp(seconds, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    return f"{prefix}.{remainder_ns // 100:07d}Z"


def filetime_100ns(mtime_ns: int) -> int:
    return mtime_ns // 100 + 116_444_736_000_000_000


if not ROOT.is_dir():
    raise SystemExit("fresh evidence root missing")
if MANIFEST.exists() or MARKER.exists():
    raise SystemExit("refusing to reseal an existing manifest or marker")
if any(ROOT.rglob("*.pyc")) or any(p.name == "__pycache__" for p in ROOT.rglob("*")):
    raise SystemExit("cache or pyc found before sealing")

files = sorted(
    (
        path.resolve()
        for path in ROOT.rglob("*")
        if path.is_file() and path.resolve() not in {MANIFEST, MARKER}
    ),
    key=lambda path: str(path).casefold(),
)

rows = []
for path in files:
    info = path.stat()
    rows.append(
        {
            "relative_path": path.relative_to(ROOT).as_posix(),
            "resolved_path": str(path),
            "bytes": info.st_size,
            "sha256": sha256_file(path),
            "utc_mtime": utc_iso_100ns(info.st_mtime_ns),
            "filetime_100ns": filetime_100ns(info.st_mtime_ns),
        }
    )

with MANIFEST.open("x", encoding="utf-8", newline="") as handle:
    writer = csv.DictWriter(
        handle,
        fieldnames=[
            "relative_path",
            "resolved_path",
            "bytes",
            "sha256",
            "utc_mtime",
            "filetime_100ns",
        ],
    )
    writer.writeheader()
    writer.writerows(rows)

for path in [*files, MANIFEST]:
    os.chmod(path, stat.S_IREAD)

with MARKER.open("x", encoding="utf-8", newline="\n") as handle:
    handle.write(f"HANDOFF_ID={HANDOFF_ID}\n")
    handle.write("SEALED=TRUE\n")
    handle.write("WRITE_STOPPED=TRUE\n")
    handle.write("POST_SEAL_WRITES_ALLOWED=NO\n")
os.chmod(MARKER, stat.S_IREAD)

print(f"SEALED files_listed={len(rows)} manifest={MANIFEST} marker={MARKER}")
