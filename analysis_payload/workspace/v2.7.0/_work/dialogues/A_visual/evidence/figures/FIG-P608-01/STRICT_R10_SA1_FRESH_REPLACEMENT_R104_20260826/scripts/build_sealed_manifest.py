from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R10_SA1_FRESH_REPLACEMENT_R104_20260826")
OUT = ROOT / "SEALED_MANIFEST.json"
EXCLUDED = {"SEALED_MANIFEST.json", "WSTOP.txt"}


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> None:
    files = []
    for path in sorted((p for p in ROOT.rglob("*") if p.is_file()), key=lambda p: p.relative_to(ROOT).as_posix()):
        rel = path.relative_to(ROOT).as_posix()
        if rel in EXCLUDED:
            continue
        stat = path.stat()
        files.append({
            "path": rel,
            "size": stat.st_size,
            "last_write_time_utc": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat().replace("+00:00", "Z"),
            "sha256": sha(path),
        })
    manifest = {
        "handoff_id": "A-R104-P608-SA1-FRESH-REPLACEMENT-20260826",
        "result": "FAIL_TO_SA2",
        "generated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "root": str(ROOT),
        "file_count_excluding_manifest_and_wstop": len(files),
        "excluded": sorted(EXCLUDED),
        "files": files,
    }
    OUT.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"manifest": str(OUT), "file_count": len(files), "manifest_sha256": sha(OUT)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
