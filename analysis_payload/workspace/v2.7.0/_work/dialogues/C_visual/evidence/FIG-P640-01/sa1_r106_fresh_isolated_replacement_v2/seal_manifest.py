from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST_NAME = "MANIFEST.csv"
WRITE_STOPPED_NAME = "WRITE_STOPPED"
CONTROL_FILES = {
    "HANDOFF.md",
    "REPORT.md",
    "RESULT.txt",
    "after_overlap_adjudication.md",
    "after_visual_acceptance.md",
    "build_evidence.py",
    "generate_machine_exports.py",
    "identity.json",
    "machine_counts.json",
    "preseal_environment_check.json",
    "preseal_validation_machine.json",
    "seal_manifest.py",
    "seal_summary.json",
    "validate_evidence.py",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main() -> None:
    manifest_path = ROOT / MANIFEST_NAME
    write_stopped_path = ROOT / WRITE_STOPPED_NAME
    if write_stopped_path.exists():
        raise RuntimeError("refusing to manifest a root that already contains WRITE_STOPPED")
    if manifest_path.exists():
        raise RuntimeError("refusing to overwrite an existing MANIFEST.csv")

    files = sorted(
        (
            path
            for path in ROOT.rglob("*")
            if path.is_file() and path.name not in {MANIFEST_NAME, WRITE_STOPPED_NAME}
        ),
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )
    with manifest_path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["relative_path", "bytes", "sha256", "mtime_utc", "manifest_scope"],
            lineterminator="\n",
        )
        writer.writeheader()
        for path in files:
            stat = path.stat()
            writer.writerow(
                {
                    "relative_path": path.relative_to(ROOT).as_posix(),
                    "bytes": stat.st_size,
                    "sha256": sha256(path),
                    "mtime_utc": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                    "manifest_scope": "CONTROL" if path.relative_to(ROOT).as_posix() in CONTROL_FILES else "PAYLOAD",
                }
            )


if __name__ == "__main__":
    main()
