from __future__ import annotations

import csv
import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P680-01\sa1_r114_fresh_isolated_v1")
MANIFEST = ROOT / "MANIFEST.csv"
EXCLUDED = {"MANIFEST.csv", "WRITE_STOPPED"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def role(path: Path) -> str:
    if path.suffix.lower() == ".png":
        return "VISUAL_EVIDENCE"
    if path.suffix.lower() == ".csv":
        return "LEDGER_OR_MACHINE_METRICS"
    if path.suffix.lower() == ".md":
        return "MANUAL_REVIEW_OR_ADJUDICATION"
    if path.suffix.lower() == ".py":
        return "REPRODUCIBILITY_SCRIPT"
    return "EVIDENCE_ARTIFACT"


def main() -> None:
    entries = list(os.scandir(ROOT))
    directories = [entry.name for entry in entries if entry.is_dir(follow_symlinks=False)]
    if directories:
        raise RuntimeError(f"unexpected directories: {directories}")
    files = sorted(
        [
            Path(entry.path)
            for entry in entries
            if entry.is_file(follow_symlinks=False) and entry.name not in EXCLUDED
        ],
        key=lambda path: path.name.casefold(),
    )
    rows = []
    for path in files:
        stat = path.stat()
        rows.append(
            {
                "RELATIVE_PATH": path.name,
                "BYTES": stat.st_size,
                "SHA256": sha256(path),
                "LAST_WRITE_UTC": datetime.fromtimestamp(
                    stat.st_mtime, tz=timezone.utc
                ).isoformat(timespec="microseconds").replace("+00:00", "Z"),
                "ROLE": role(path),
            }
        )
    with MANIFEST.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["RELATIVE_PATH", "BYTES", "SHA256", "LAST_WRITE_UTC", "ROLE"],
        )
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
