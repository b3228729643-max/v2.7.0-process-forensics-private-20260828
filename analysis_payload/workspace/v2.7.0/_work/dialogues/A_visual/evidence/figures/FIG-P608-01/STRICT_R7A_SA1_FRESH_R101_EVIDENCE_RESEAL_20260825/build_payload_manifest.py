from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MANIFEST = ROOT / "PAYLOAD_MANIFEST.json"
CONTROL_NAMES = {"PAYLOAD_MANIFEST.json", "WRITE_STOPPED", "SEAL.json"}


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


entries = []
for path in sorted((p for p in ROOT.rglob("*") if p.is_file() and p.name not in CONTROL_NAMES), key=lambda p: p.relative_to(ROOT).as_posix()):
    st = path.stat()
    entries.append(
        {
            "relative_path": path.relative_to(ROOT).as_posix(),
            "absolute_path": str(path),
            "bytes": st.st_size,
            "sha256": digest(path),
            "mtime_ns": st.st_mtime_ns,
            "ordinary_file": True,
        }
    )

payload = {
    "schema": "R7A_COMPLETE_PAYLOAD_MANIFEST_V1",
    "root": str(ROOT),
    "handoff_id": "A-R101-P608-SA1-FRESH-R7A-EVIDENCE-RESEAL-20260825",
    "route": "SA1=gpt-5.6-sol/xhigh",
    "scope": "all ordinary payload files recursively; excludes only this manifest and terminal controls WRITE_STOPPED/SEAL.json",
    "payload_file_count": len(entries),
    "payload_total_bytes": sum(e["bytes"] for e in entries),
    "max_payload_mtime_ns": max(e["mtime_ns"] for e in entries),
    "entries": entries,
}
MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: payload[k] for k in ("payload_file_count", "payload_total_bytes", "max_payload_mtime_ns")}))
