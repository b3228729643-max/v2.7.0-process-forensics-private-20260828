from __future__ import annotations

import csv
import hashlib
import json
import os
import stat
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P639-01\sa1_r105_fresh_isolated_v2_main_replacement_20260826")
REPORT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\reports\FIG-P639-01-SA1-R105-FRESH-ISOLATED-V2-MAIN-REPLACEMENT-20260826.md")
HANDOFF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\C\FIG-P639-01-SA1-R105-FRESH-ISOLATED-V2-MAIN-REPLACEMENT-20260826.json")
MANIFEST = ROOT / "MANIFEST.json"
WSTOP = ROOT / "WSTOP.json"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest().upper()


def csv_count(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return sum(1 for _ in csv.DictReader(f))


def fail_count(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return sum(1 for row in csv.DictReader(f) if row.get("decision") == "FAIL")


def main() -> None:
    if MANIFEST.exists() or WSTOP.exists():
        raise RuntimeError("one-shot seal already exists")
    summary = json.loads((ROOT / "machine" / "machine_summary.json").read_text(encoding="utf-8"))
    objects = json.loads((ROOT / "machine" / "object_manifest.json").read_text(encoding="utf-8"))["elements"]
    handoff = json.loads(HANDOFF.read_text(encoding="utf-8"))
    validation = json.loads((ROOT / "FINAL_VALIDATION.json").read_text(encoding="utf-8"))
    assert summary["visible_object_denominator"] == 157
    assert len(objects) == 157
    assert summary["all_unordered_pair_expected"] == 12246
    assert csv_count(ROOT / "machine" / "after_overlap_report.csv") == 12246
    assert fail_count(ROOT / "machine" / "after_overlap_report.csv") == 1
    assert csv_count(ROOT / "manual" / "glyph_review_ledger.csv") == 147
    assert csv_count(ROOT / "manual" / "critical_relation_review.csv") == 1
    assert csv_count(ROOT / "manual" / "view_review_ledger.csv") == 20
    assert len(list((ROOT / "contact").glob("glyph_contact_sheet_*.png"))) == 13
    for item in objects:
        assert (ROOT / "machine" / "masks" / item["safe_filename"]).is_file()
    assert validation["final_status"] == "FAIL_TO_SA2"
    assert handoff["verdict"] == "FAIL_TO_SA2"
    assert REPORT.is_file() and HANDOFF.is_file()
    cache_dirs = [p for p in ROOT.rglob("*") if p.is_dir() and p.name in {"__pycache__", ".cache", "cache"}]
    assert not cache_dirs

    files = []
    for path in sorted(p for p in ROOT.rglob("*") if p.is_file() and p not in {MANIFEST, WSTOP}):
        files.append({
            "path": path.relative_to(ROOT).as_posix(),
            "bytes": path.stat().st_size,
            "sha256": sha256(path),
        })
    external = [
        {"path": str(REPORT), "bytes": REPORT.stat().st_size, "sha256": sha256(REPORT)},
        {"path": str(HANDOFF), "bytes": HANDOFF.stat().st_size, "sha256": sha256(HANDOFF)},
    ]
    manifest = {
        "uid": "FIG-P639-01",
        "handoff_id": "MAIN-R105-P639-SA1-FRESH-ISOLATED-REPLACEMENT-20260826",
        "verdict": "FAIL_TO_SA2",
        "sealed_candidate_sha256": "F86E89047BA09FEA72FD8F79BF524A04DA367BFF3057806A879106A1032626A1",
        "visible_object_denominator": 157,
        "unordered_pair_count": 12246,
        "file_count_before_manifest_and_wstop": len(files),
        "files": files,
        "external_deliverables": external,
        "gates": {
            "result_present": True,
            "final_validation_present": True,
            "manual_rows_closed": True,
            "all_pairs_closed": True,
            "ads_count_preseal": 0,
            "cache_directory_count": 0,
            "portable_safe_filenames": True,
        },
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    manifest_hash = sha256(MANIFEST)
    sealed_utc = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    wstop = {
        "uid": "FIG-P639-01",
        "handoff_id": "MAIN-R105-P639-SA1-FRESH-ISOLATED-REPLACEMENT-20260826",
        "sealed_utc": sealed_utc,
        "verdict": "FAIL_TO_SA2",
        "manifest": "MANIFEST.json",
        "manifest_sha256": manifest_hash,
        "wstop_written_last": True,
        "writes_after_wstop_forbidden": True,
        "evidence_root_read_only_requested": True,
        "report_read_only_requested": True,
        "handoff_read_only_requested": True,
        "ads_gate": "PASS_PRESEAL_COUNT_0",
        "cache_gate": "PASS_COUNT_0",
    }
    WSTOP.write_text(json.dumps(wstop, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for path in sorted([p for p in ROOT.rglob("*") if p.is_file()] + [REPORT, HANDOFF]):
        os.chmod(path, stat.S_IREAD)
    for path in sorted([p for p in ROOT.rglob("*") if p.is_dir()], reverse=True):
        try:
            os.chmod(path, stat.S_IREAD | stat.S_IEXEC)
        except OSError:
            pass
    try:
        os.chmod(ROOT, stat.S_IREAD | stat.S_IEXEC)
    except OSError:
        pass
    print(json.dumps({"sealed": True, "sealed_utc": sealed_utc, "manifest_sha256": manifest_hash, "file_count": len(files), "verdict": "FAIL_TO_SA2"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
