from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEAL = ROOT / "seal"
REPORTS = ROOT / "reports"
HANDOFF = "A-R130-P654-SA2-REPAIR-V2-20260824"
ROUTE = "LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1"
FINAL_SECTION = "## Terminal and seal-stage closure"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


terminal = json.loads((SEAL / "terminal_check.json").read_text(encoding="utf-8"))
if terminal.get("terminal_check") != "PASS" or terminal.get("failure_count") != 0:
    raise RuntimeError("terminal check is not PASS")
if terminal.get("handoff_id") != HANDOFF or terminal.get("route") != ROUTE:
    raise RuntimeError("terminal handoff/route mismatch")
if (SEAL / "WRITE_STOPPED").exists() or (ROOT / "WRITE_STOPPED").exists():
    raise RuntimeError("WRITE_STOPPED already exists")

# This is the final report write, deliberately after terminal and before manifest.
report_path = REPORTS / "SA2_REPAIR_REPORT.md"
report = report_path.read_text(encoding="utf-8")
if FINAL_SECTION in report:
    report = report.split(FINAL_SECTION, 1)[0].rstrip() + "\n\n"
report += f"""{FINAL_SECTION}

- Terminal check: PASS ({len(terminal['checks'])} checks, {terminal['referenced_png_opened']} referenced PNGs mechanically opened, 0 failures).
- Final seal order: terminal check -> this finalized report and manifest -> `WRITE_STOPPED` absolute last.
- Route remains `{ROUTE}`; official candidate construction and fresh isolated SA1 remain external work.
"""
report_path.write_text(report, encoding="utf-8")
(ROOT / "SA2_REPAIR_REPORT.md").write_text(report, encoding="utf-8")

seal_stage = {
    "figure_uid": "FIG-P654-01",
    "handoff_id": HANDOFF,
    "route": ROUTE,
    "terminal_check": "PASS",
    "terminal_check_count": len(terminal["checks"]),
    "terminal_failure_count": terminal["failure_count"],
    "referenced_png_opened": terminal["referenced_png_opened"],
    "report_finalized_after_terminal": True,
    "next_and_last_write_after_manifest": "seal/WRITE_STOPPED",
}
(REPORTS / "seal_stage_summary.json").write_text(
    json.dumps(seal_stage, ensure_ascii=False, indent=2), encoding="utf-8"
)

excluded = {"seal/MANIFEST.json", "seal/WRITE_STOPPED"}
entries: list[dict[str, object]] = []
for path in sorted(candidate for candidate in ROOT.rglob("*") if candidate.is_file()):
    relative = path.relative_to(ROOT).as_posix()
    if relative in excluded:
        continue
    entries.append(
        {"path": relative, "size": path.stat().st_size, "sha256": sha256(path)}
    )

identity = json.loads((REPORTS / "candidate_identity.json").read_text(encoding="utf-8"))
manifest = {
    "figure_uid": "FIG-P654-01",
    "handoff_id": HANDOFF,
    "route": ROUTE,
    "terminal_check": "PASS",
    "terminal_check_count": len(terminal["checks"]),
    "terminal_failure_count": 0,
    "source_normalized_sha256": identity["local_sa2_candidate_identity"]["source_normalized_sha256"],
    "base_head": identity["local_sa2_candidate_identity"]["base_head"],
    "official_r98_sha256": identity["official_r98_frozen_identity"]["sha256"],
    "manifest_scope": "all evidence-package files after final report, excluding MANIFEST.json itself and WRITE_STOPPED",
    "seal_order": [
        "seal/terminal_check.json",
        "reports/SA2_REPAIR_REPORT.md + root SA2_REPAIR_REPORT.md",
        "seal/MANIFEST.json",
        "seal/WRITE_STOPPED",
    ],
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "file_count": len(entries),
    "total_bytes_before_manifest_and_marker": sum(int(entry["size"]) for entry in entries),
    "files": entries,
}
(SEAL / "MANIFEST.json").write_text(
    json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
)
print(
    json.dumps(
        {
            "manifest": "PASS",
            "file_count": manifest["file_count"],
            "total_bytes_before_manifest_and_marker": manifest["total_bytes_before_manifest_and_marker"],
            "report": str(report_path),
        },
        ensure_ascii=False,
    )
)
