from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
EXCLUDED = {"payload_manifest.json", "payload_manifest.sha256", "WRITE_STOPPED"}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


files = []
for path in sorted(ROOT.rglob("*")):
    if not path.is_file() or path.name in EXCLUDED:
        continue
    files.append(
        {
            "relative_path": path.relative_to(ROOT).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        }
    )

manifest = {
    "handoff_id": "A-R110-P582-SA1-FRESH-ISOLATED-20260827",
    "figure_uid": "FIG-P582-01",
    "round": "R110",
    "role": "SA1_FRESH_ISOLATED",
    "result": "PASS",
    "manifest_scope": "all sealed payload files except payload_manifest.json, payload_manifest.sha256, and WRITE_STOPPED",
    "file_count": len(files),
    "total_size_bytes": sum(item["size_bytes"] for item in files),
    "files": files,
}
manifest_path = ROOT / "payload_manifest.json"
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
(ROOT / "payload_manifest.sha256").write_text(f"{sha256(manifest_path)}  payload_manifest.json\n", encoding="ascii")
print(json.dumps({"file_count": manifest["file_count"], "total_size_bytes": manifest["total_size_bytes"], "manifest_sha256": sha256(manifest_path)}, indent=2))
