from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
JSON_MANIFEST = ROOT / "MANIFEST_FILES.json"
CSV_MANIFEST = ROOT / "MANIFEST_SHA256.csv"
EXCLUDED = {"MANIFEST_FILES.json", "MANIFEST_SHA256.csv", "WRITE_STOPPED"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def main() -> None:
    payload = sorted(
        (path for path in ROOT.rglob("*") if path.is_file() and path.name not in EXCLUDED),
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )
    entries = [
        {
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
        for path in payload
    ]
    JSON_MANIFEST.write_text(
        json.dumps(
            {
                "handoff_id": "A-R107-P715-SA1-FRESH-ISOLATED-20260826",
                "generated_utc": datetime.now(timezone.utc).isoformat(),
                "scope": "all evidence-root files except both manifests and WRITE_STOPPED",
                "payload_file_count": len(entries),
                "entries": entries,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    csv_entries = entries + [
        {
            "path": JSON_MANIFEST.relative_to(ROOT).as_posix(),
            "bytes": JSON_MANIFEST.stat().st_size,
            "sha256": sha256(JSON_MANIFEST),
        }
    ]
    with CSV_MANIFEST.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("path", "bytes", "sha256", "manifest_scope"))
        writer.writeheader()
        for entry in csv_entries:
            writer.writerow({**entry, "manifest_scope": "excludes MANIFEST_SHA256.csv and WRITE_STOPPED"})
    print(json.dumps({
        "json_payload_count": len(entries),
        "csv_hashed_count": len(csv_entries),
        "json_manifest_sha256": sha256(JSON_MANIFEST),
        "csv_manifest_sha256": sha256(CSV_MANIFEST),
    }))


if __name__ == "__main__":
    main()
