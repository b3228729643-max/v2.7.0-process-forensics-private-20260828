from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P639-01\sa3_r105_fresh_isolated_v3_main_20260826")
MANIFEST = ROOT / "manifest.json"
WSTOP = ROOT / "WSTOP"
if MANIFEST.exists() or WSTOP.exists():
    raise SystemExit("single-seal invariant violated: manifest.json or WSTOP already exists")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


entries = []
for path in sorted((p for p in ROOT.rglob("*") if p.is_file()), key=lambda p: p.relative_to(ROOT).as_posix()):
    rel = path.relative_to(ROOT).as_posix()
    entries.append({"path": rel, "bytes": path.stat().st_size, "sha256": sha256(path)})

manifest_payload = {
    "uid": "FIG-P639-01",
    "handoff_id": "MAIN-R105-P639-SA3-FRESH-ISOLATED-20260826",
    "verdict": "PASS",
    "generated_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "entry_count_excluding_manifest_and_wstop": len(entries),
    "expected_final_ordinary_file_count": len(entries) + 2,
    "entries": entries,
}
with MANIFEST.open("x", encoding="utf-8", newline="\n") as f:
    json.dump(manifest_payload, f, ensure_ascii=False, indent=2)
    f.write("\n")
    f.flush()
    os.fsync(f.fileno())

manifest_sha = sha256(MANIFEST)
wstop_text = (
    "HANDOFF_ID=MAIN-R105-P639-SA3-FRESH-ISOLATED-20260826\n"
    "UID=FIG-P639-01\n"
    "VERDICT=PASS\n"
    f"MANIFEST_SHA256={manifest_sha}\n"
    f"MANIFEST_ENTRY_COUNT={len(entries)}\n"
    f"FINAL_ORDINARY_FILE_COUNT={len(entries) + 2}\n"
    "WRITE_SEQUENCE=manifest.json_then_WSTOP\n"
    "WSTOP_IS_ABSOLUTE_LAST_WRITE=true\n"
)
with WSTOP.open("x", encoding="ascii", newline="\n") as f:
    f.write(wstop_text)
    f.flush()
    os.fsync(f.fileno())
print(json.dumps({"manifest_entries": len(entries), "final_ordinary_files": len(entries) + 2, "manifest_sha256": manifest_sha, "wstop_last": True}))
