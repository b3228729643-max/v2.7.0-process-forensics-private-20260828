from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P605-01\sa3_r104_fresh_isolated_v1")
MANIFEST = ROOT / "MANIFEST.csv"
EXCLUDED = {"MANIFEST.csv", "WRITE_STOPPED"}
WINDOWS_EPOCH_100NS = 116444736000000000


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> None:
    files = [p for p in ROOT.rglob("*") if p.is_file() and p.relative_to(ROOT).as_posix() not in EXCLUDED]
    rows = []
    for path in sorted(files, key=lambda p: p.relative_to(ROOT).as_posix().lower()):
        st = path.stat()
        rows.append(
            {
                "relative_path": path.relative_to(ROOT).as_posix(),
                "resolved_path": str(path.resolve()),
                "bytes": st.st_size,
                "sha256": digest(path),
                "utc_mtime": datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z"),
                "filetime_100ns": st.st_mtime_ns // 100 + WINDOWS_EPOCH_100NS,
            }
        )
    with MANIFEST.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["relative_path", "resolved_path", "bytes", "sha256", "utc_mtime", "filetime_100ns"])
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
