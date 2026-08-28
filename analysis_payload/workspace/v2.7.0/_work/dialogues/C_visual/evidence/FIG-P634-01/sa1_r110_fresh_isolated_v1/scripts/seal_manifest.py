from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P634-01\sa1_r110_fresh_isolated_v1")
MANIFEST = ROOT / "MANIFEST.json"
MARKER = ROOT / "WRITE_STOPPED"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> None:
    if MANIFEST.exists() or MARKER.exists():
        raise SystemExit("Refusing to overwrite existing manifest or marker")
    entries = []
    for path in sorted(ROOT.rglob("*"), key=lambda p: p.as_posix().lower()):
        if not path.is_file() or path in {MANIFEST, MARKER}:
            continue
        stat = path.stat()
        entries.append({
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": stat.st_size,
            "sha256": sha256(path),
            "mtime_utc": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
        })
    directories = [
        p.relative_to(ROOT).as_posix()
        for p in sorted(ROOT.rglob("*"), key=lambda p: p.as_posix().lower())
        if p.is_dir()
    ]
    payload = {
        "schema": "fresh_isolated_sa1_manifest_v1",
        "handoff_id": "C-FIG-P634-01-R110-SA1-FRESH-ISOLATED-V1",
        "uid": "FIG-P634-01",
        "result": "SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3",
        "root": str(ROOT),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "payload_file_count": len(entries),
        "payload_total_bytes": sum(e["bytes"] for e in entries),
        "directories": directories,
        "entries": entries,
        "exclusions": [
            {"path": "MANIFEST.json", "reason": "manifest self-hash exclusion"},
            {"path": "WRITE_STOPPED", "reason": "unique marker is created strictly last after manifest completion"}
        ]
    }
    with MANIFEST.open("x", encoding="utf-8", newline="\n") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"manifest_entries={len(entries)} payload_bytes={payload['payload_total_bytes']}")


if __name__ == "__main__":
    main()
