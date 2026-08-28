from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "SEAL_MANIFEST.json"
EXCLUDED = {"SEAL_MANIFEST.json", "WRITE_STOPPED"}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def main() -> None:
    if OUTPUT.exists() or (ROOT / "WRITE_STOPPED").exists():
        raise RuntimeError("seal artifacts already exist; refusing a second seal preparation")
    entries = []
    for path in sorted((path for path in ROOT.rglob("*") if path.is_file()), key=lambda p: p.as_posix()):
        relative = path.relative_to(ROOT).as_posix()
        if relative in EXCLUDED:
            continue
        entries.append(
            {
                "path": relative,
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    manifest = {
        "schema": "FIGURE_SA1_SEAL_MANIFEST_V1",
        "uid": "FIG-P067-01",
        "handoff_id": "A-R114-P067-SA1-FRESH-ISOLATED-20260827",
        "prepared_utc": datetime.now(timezone.utc).isoformat(),
        "payload_file_count": len(entries),
        "payload_total_bytes": sum(entry["bytes"] for entry in entries),
        "excluded_future_files": sorted(EXCLUDED),
        "manual_fields_generated_or_overwritten": False,
        "entries": entries,
    }
    OUTPUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
