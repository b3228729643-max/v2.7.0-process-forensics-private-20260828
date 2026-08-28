from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R1_SA2_R168_READONLY_R111_20260827")
MANIFEST = ROOT / "audit" / "preseal_payload_manifest.csv"
SUMMARY = ROOT / "audit" / "preseal_manifest_summary.json"


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def main() -> None:
    if any(ROOT.rglob("WRITE_STOPPED*")):
        raise SystemExit("WRITE_STOPPED already exists")
    SUMMARY.write_text(
        json.dumps(
            {
                "manifest_self_exclusion_count": 1,
                "write_stopped_preseal_count": 0,
                "status_code": "PRESEAL_PAYLOAD_FROZEN",
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    files = sorted(
        p for p in ROOT.rglob("*")
        if p.is_file() and p != MANIFEST and p.name != "WRITE_STOPPED"
    )
    with MANIFEST.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=["relative_path", "bytes", "sha256", "last_write_time_ns"],
        )
        writer.writeheader()
        for path in files:
            stat = path.stat()
            writer.writerow(
                {
                    "relative_path": path.relative_to(ROOT).as_posix(),
                    "bytes": stat.st_size,
                    "sha256": digest(path),
                    "last_write_time_ns": stat.st_mtime_ns,
                }
            )


if __name__ == "__main__":
    main()
