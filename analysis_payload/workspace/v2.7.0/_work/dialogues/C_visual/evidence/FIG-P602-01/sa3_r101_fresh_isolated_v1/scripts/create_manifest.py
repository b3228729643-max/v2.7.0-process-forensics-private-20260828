from __future__ import annotations

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "evidence_manifest.csv"
MARKER = ROOT / "WRITE_STOPPED.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_100ns(mtime_ns: int) -> str:
    seconds, remainder_ns = divmod(mtime_ns, 1_000_000_000)
    base = datetime.fromtimestamp(seconds, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    return f"{base}.{remainder_ns // 100:07d}Z"


def main() -> None:
    if MARKER.exists():
        raise SystemExit("refusing to rebuild manifest after WRITE_STOPPED.json exists")

    files = sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file() and path not in {MANIFEST, MARKER}
    )

    with MANIFEST.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "relative_path",
                "bytes",
                "sha256",
                "mtime_utc_100ns",
                "mtime_unix_100ns",
                "mtime_ns",
            ],
            lineterminator="\n",
        )
        writer.writeheader()
        for path in files:
            stat = path.stat()
            if stat.st_mtime_ns % 100:
                raise RuntimeError(f"mtime is not exactly representable at NTFS 100-ns precision: {path}")
            writer.writerow(
                {
                    "relative_path": path.relative_to(ROOT).as_posix(),
                    "bytes": stat.st_size,
                    "sha256": sha256(path),
                    "mtime_utc_100ns": utc_100ns(stat.st_mtime_ns),
                    "mtime_unix_100ns": stat.st_mtime_ns // 100,
                    "mtime_ns": stat.st_mtime_ns,
                }
            )


if __name__ == "__main__":
    main()
