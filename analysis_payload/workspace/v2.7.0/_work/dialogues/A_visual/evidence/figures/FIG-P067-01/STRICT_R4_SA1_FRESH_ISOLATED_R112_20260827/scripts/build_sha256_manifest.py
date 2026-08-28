from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R4_SA1_FRESH_ISOLATED_R112_20260827")
OUT = ROOT / "sha256_manifest.csv"
EXCLUDED = {"sha256_manifest.csv", "WRITE_STOPPED"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    paths = sorted(
        (
            path
            for path in ROOT.rglob("*")
            if path.is_file() and path.name not in EXCLUDED
        ),
        key=lambda path: str(path.relative_to(ROOT)).replace("\\", "/"),
    )
    with OUT.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=["relative_path", "bytes", "sha256"])
        writer.writeheader()
        for path in paths:
            writer.writerow(
                {
                    "relative_path": str(path.relative_to(ROOT)).replace("\\", "/"),
                    "bytes": path.stat().st_size,
                    "sha256": sha256(path),
                }
            )
    record = {
        "manifested_file_count": len(paths),
        "manifest_bytes": OUT.stat().st_size,
        "manifest_sha256": sha256(OUT),
        "excluded_future_marker": "WRITE_STOPPED",
        "self_excluded": True,
    }
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
