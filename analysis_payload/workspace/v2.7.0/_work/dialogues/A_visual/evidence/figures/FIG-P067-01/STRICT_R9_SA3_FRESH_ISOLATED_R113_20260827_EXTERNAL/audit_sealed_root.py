from __future__ import annotations

import csv
import hashlib
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R9_SA3_FRESH_ISOLATED_R113_20260827")
EXTERNAL = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R9_SA3_FRESH_ISOLATED_R113_20260827_EXTERNAL")
REPORT = EXTERNAL / "POST_SEAL_AUDIT.json"
HANDOFF = EXTERNAL / "HANDOFF_A-R113-P067-SA3-FRESH-ISOLATED-20260827.md"
EXPECTED_STATUS = "SA3_FAIL_RETURN_TO_SA2"


def is_readonly(path: Path) -> bool:
    attrs = getattr(os.stat(path, follow_symlinks=False), "st_file_attributes", 0)
    return bool(attrs & stat.FILE_ATTRIBUTE_READONLY)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


files = sorted((p for p in ROOT.rglob("*") if p.is_file()), key=lambda p: p.relative_to(ROOT).as_posix())
dirs = [ROOT] + sorted((p for p in ROOT.rglob("*") if p.is_dir()), key=lambda p: p.relative_to(ROOT).as_posix())
wstop = ROOT / "WRITE_STOPPED"
other_files = [p for p in files if p != wstop]
wstop_unique_latest = wstop.is_file() and all(wstop.stat().st_mtime_ns > p.stat().st_mtime_ns for p in other_files)
all_files_readonly = all(is_readonly(p) for p in files)
all_dirs_readonly = all(is_readonly(p) for p in dirs)
crosscheck = json.loads((ROOT / "07_validation/final_crosscheck.json").read_text(encoding="utf-8"))
manual_pairs = csv_rows(ROOT / "06_ledgers/manual_critical_pair_review.csv")
hard_fail_pairs = sorted(r["pair_id"] for r in manual_pairs if r["decision"].startswith("FAIL"))

tree = hashlib.sha256()
for path in files:
    rel = path.relative_to(ROOT).as_posix()
    tree.update(rel.encode("utf-8"))
    tree.update(b"\0")
    tree.update(str(path.stat().st_size).encode("ascii"))
    tree.update(b"\0")
    tree.update(sha256(path).encode("ascii"))
    tree.update(b"\n")

status = (ROOT / "RESULT.txt").read_text(encoding="utf-8").strip()
audit_ok = (
    ROOT.is_dir()
    and wstop_unique_latest
    and all_files_readonly
    and all_dirs_readonly
    and crosscheck.get("crosscheck_ok") is True
    and status == EXPECTED_STATUS
    and hard_fail_pairs == ["P01916", "P01917"]
)

audit = {
    "audit_identity": "ROOT_EXTERNAL_READ_ONLY_AUDITOR_R113_P067_SA3_FRESH",
    "audited_at_utc": datetime.now(timezone.utc).isoformat(),
    "root": str(ROOT),
    "root_external_auditor": str(Path(__file__).resolve()),
    "report": str(REPORT),
    "handoff": str(HANDOFF),
    "seal_attempt_count": 1,
    "seal_audit_ok": audit_ok,
    "write_stopped_exists": wstop.is_file(),
    "write_stopped_unique_strict_latest": wstop_unique_latest,
    "write_stopped_mtime_ns": wstop.stat().st_mtime_ns if wstop.is_file() else None,
    "next_latest_payload_mtime_ns": max((p.stat().st_mtime_ns for p in other_files), default=None),
    "all_payload_control_files_readonly": all_files_readonly,
    "all_directories_including_root_readonly": all_dirs_readonly,
    "root_file_count": len(files),
    "root_directory_count_including_root": len(dirs),
    "root_tree_sha256": tree.hexdigest().upper(),
    "crosscheck_ok": crosscheck.get("crosscheck_ok"),
    "status": status,
    "hard_fail_pair_ids": hard_fail_pairs,
    "root_read_only_only": True,
    "root_mutations_by_auditor": 0,
    "external_report_and_handoff_set_readonly_after_creation": True,
}

handoff_text = f"""# FIG-P067-01 SA3 fresh isolated handoff

- assigned_scope: Independently inspect only the frozen R113 official PDF Figure 4.1 / FIG-P067-01 and its current source under the strict R168 hard gates, without source, TeX, build, Git, process, or central-state mutation.
- completed: Fresh location; native 300dpi and 8x-nearest, grayscale, standalone, and full-page review; 130-object denominator; all 8,385 unordered relationships; 130 per-object manual rows; 71 per-critical-pair manual rows; typography and math/semantic review; terminal validation; one-way ReadOnly seal; external post-seal audit.
- files_changed: Evidence only under `{ROOT}` plus this external immutable report/handoff directory. Frozen PDF and current source remained unchanged.
- decisions: `{EXPECTED_STATUS}`. P01916 and P01917 are real final-visible 34px illegal overlaps of T016 (p in p4) with G008 and G009. Nine source-font and nine glyph numeric observations are advisory only and actually readable. Mathematics, semantics, page integration, grayscale, codepoints, and clipping checks otherwise pass.
- unresolved: The p4 label geometry must be corrected in a future official candidate; this SA3 role made no source patch.
- validation: `final_crosscheck.json` passed with zero errors; external seal audit ok={str(audit_ok).lower()}; WRITE_STOPPED unique-strict-latest={str(wstop_unique_latest).lower()}; all payload/control files ReadOnly={str(all_files_readonly).lower()}; all directories including root ReadOnly={str(all_dirs_readonly).lower()}; root tree SHA-256 `{audit['root_tree_sha256']}`.
- next_action: Return to SA2. Reposition p4 or increase/reposition its real background to provide at least 3px final-visible clearance from both G008 and G009, rebuild a new official candidate, then route through fresh SA1 and fresh SA3.
- sealed_root: `{ROOT}`
- root_external_auditor: `{Path(__file__).resolve()}`
- immutable_report: `{REPORT}`
- immutable_handoff: `{HANDOFF}`
"""

if not audit_ok:
    print(json.dumps(audit, ensure_ascii=False))
    raise SystemExit(1)

HANDOFF.write_text(handoff_text, encoding="utf-8")
REPORT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
os.chmod(HANDOFF, stat.S_IREAD)
os.chmod(REPORT, stat.S_IREAD)
immutable_ok = is_readonly(HANDOFF) and is_readonly(REPORT)
print(json.dumps({"seal_audit_ok": audit_ok, "external_immutable_ok": immutable_ok, "report": str(REPORT), "handoff": str(HANDOFF), "tree_sha256": audit["root_tree_sha256"]}, ensure_ascii=False))
raise SystemExit(0 if immutable_ok else 2)
