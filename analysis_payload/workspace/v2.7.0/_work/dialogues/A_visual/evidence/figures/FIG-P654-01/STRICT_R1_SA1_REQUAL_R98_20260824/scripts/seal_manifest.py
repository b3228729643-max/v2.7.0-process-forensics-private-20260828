from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEAL = ROOT / "seal"
terminal = json.loads((SEAL / "terminal_check.json").read_text(encoding="utf-8"))
if terminal.get("terminal_check") != "PASS":
    raise RuntimeError("terminal check is not PASS")
if (SEAL / "WRITE_STOPPED").exists():
    raise RuntimeError("WRITE_STOPPED already exists")

excluded = {"seal/MANIFEST.json", "seal/WRITE_STOPPED"}
entries = []
for path in sorted(p for p in ROOT.rglob("*") if p.is_file()):
    rel = path.relative_to(ROOT).as_posix()
    if rel in excluded:
        continue
    data = path.read_bytes()
    entries.append({"path": rel, "size": len(data), "sha256": hashlib.sha256(data).hexdigest().upper()})
manifest = {
    "figure_uid": "FIG-P654-01",
    "handoff_id": "A-R130-P654-SA1-RESUME-20260824",
    "route": "FAIL_TO_SA2",
    "terminal_check": "PASS",
    "manifest_scope": "all package files before MANIFEST.json and WRITE_STOPPED",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "file_count": len(entries),
    "files": entries,
}
(SEAL / "MANIFEST.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({"manifest": "PASS", "file_count": len(entries)}, ensure_ascii=False))
