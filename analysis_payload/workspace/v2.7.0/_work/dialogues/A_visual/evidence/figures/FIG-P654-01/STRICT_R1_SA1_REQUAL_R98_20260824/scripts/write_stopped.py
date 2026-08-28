from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEAL = ROOT / "seal"
terminal = json.loads((SEAL / "terminal_check.json").read_text(encoding="utf-8"))
manifest = json.loads((SEAL / "MANIFEST.json").read_text(encoding="utf-8"))
if terminal.get("terminal_check") != "PASS" or manifest.get("terminal_check") != "PASS":
    raise RuntimeError("terminal or manifest is not PASS")
if manifest.get("route") != "FAIL_TO_SA2":
    raise RuntimeError("manifest route mismatch")
marker = SEAL / "WRITE_STOPPED"
if marker.exists():
    raise RuntimeError("WRITE_STOPPED already exists")
marker.write_text("FAIL_TO_SA2\nA-R130-P654-SA1-RESUME-20260824\n", encoding="utf-8")
print(json.dumps({"write_stopped": True, "route": "FAIL_TO_SA2", "manifest_file_count": manifest["file_count"]}, ensure_ascii=False))
