from __future__ import annotations

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "MANIFEST.json"
WRITE_STOPPED = ROOT / "WRITE_STOPPED"
EXCLUDED = {MANIFEST.resolve(), WRITE_STOPPED.resolve()}

files = []
for path in sorted((p for p in ROOT.rglob("*") if p.is_file()), key=lambda p: p.relative_to(ROOT).as_posix()):
    if path.resolve() in EXCLUDED:
        continue
    data = path.read_bytes()
    files.append(
        {
            "relative_path": path.relative_to(ROOT).as_posix(),
            "bytes": len(data),
            "sha256": hashlib.sha256(data).hexdigest().upper(),
        }
    )

payload = {
    "schema": "C-FIG-P634-01-R110-SA2-R168-READONLY-MANIFEST-V1",
    "root": str(ROOT),
    "hash_algorithm": "SHA256",
    "manifested_file_count": len(files),
    "exclusions": [
        {
            "relative_path": "MANIFEST.json",
            "reason": "self-hash exclusion",
        },
        {
            "relative_path": "WRITE_STOPPED",
            "reason": "seal marker is created after the complete payload and manifest",
        },
    ],
    "files": files,
}
MANIFEST.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"manifested_file_count": len(files)}, ensure_ascii=False))
