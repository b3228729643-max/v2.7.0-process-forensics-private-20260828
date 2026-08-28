from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P680-01\sa3_r114_fresh_isolated_v1")
MANIFEST = ROOT / "manifest.json"
MARKER = ROOT / "meta" / "WRITE_STOPPED.txt"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def main() -> None:
    if MARKER.exists():
        raise RuntimeError("WRITE_STOPPED already exists; manifest must precede the final marker")
    entries = []
    for path in sorted(ROOT.rglob("*"), key=lambda p: p.as_posix()):
        if not path.is_file() or path == MANIFEST or path == MARKER:
            continue
        entries.append(
            {
                "relative_path": path.relative_to(ROOT).as_posix(),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    manifest = {
        "handoff_id": "C-FIG-P680-01-R114-SA3-FRESH-ISOLATED-V1",
        "uid": "FIG-P680-01",
        "root": str(ROOT),
        "generated_at_asia_shanghai": datetime.now(timezone(timedelta(hours=8))).isoformat(),
        "manifest_completed_before_final_marker": True,
        "listed_file_count_excluding_manifest_and_marker": len(entries),
        "expected_total_file_count_after_manifest_and_marker": len(entries) + 2,
        "listed_files": entries,
        "self_entry": {
            "relative_path": "manifest.json",
            "hash_excluded_to_avoid_self_reference": True,
        },
        "planned_final_marker": {
            "relative_path": "meta/WRITE_STOPPED.txt",
            "must_be_multiline": True,
            "must_be_unique": True,
            "must_be_last_content_write": True,
        },
        "sealed_return_token": "SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE",
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
