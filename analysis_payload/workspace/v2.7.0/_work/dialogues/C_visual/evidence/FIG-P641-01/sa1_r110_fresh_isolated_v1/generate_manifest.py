from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
EXCLUDED = {"MANIFEST.json", "WRITE_STOPPED"}


def sha256(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def main():
    entries = []
    for path in sorted((p for p in ROOT.rglob("*") if p.is_file()), key=lambda p: p.relative_to(ROOT).as_posix()):
        relative = path.relative_to(ROOT).as_posix()
        if relative in EXCLUDED:
            continue
        entries.append({"path": relative, "bytes": path.stat().st_size, "sha256": sha256(path)})
    directories = [
        path.relative_to(ROOT).as_posix()
        for path in sorted((p for p in ROOT.rglob("*") if p.is_dir()), key=lambda p: p.relative_to(ROOT).as_posix())
    ]
    manifest = {
        "schema": "FIG-P641-01-SA1-FRESH-ISOLATED-V1-MANIFEST-1",
        "handoff_id": "C-FIG-P641-01-R110-SA1-FRESH-ISOLATED-V1",
        "outcome": "SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(ROOT),
        "closure_rule": "After WRITE_STOPPED is created, exact ordinary-file set must equal entries plus MANIFEST.json plus WRITE_STOPPED; MANIFEST.json and WRITE_STOPPED are deliberately excluded from entries to avoid self-reference and post-manifest creation.",
        "excluded_paths": sorted(EXCLUDED),
        "entry_count": len(entries),
        "directory_count_excluding_root": len(directories),
        "total_entry_bytes": sum(entry["bytes"] for entry in entries),
        "directories": directories,
        "entries": entries,
    }
    (ROOT / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "entry_count": manifest["entry_count"],
        "directory_count_excluding_root": manifest["directory_count_excluding_root"],
        "total_entry_bytes": manifest["total_entry_bytes"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
