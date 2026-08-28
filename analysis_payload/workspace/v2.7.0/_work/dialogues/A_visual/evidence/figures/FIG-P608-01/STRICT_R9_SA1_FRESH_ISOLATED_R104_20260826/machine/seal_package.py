from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R9_SA1_FRESH_ISOLATED_R104_20260826")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r104_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C03\fig_v5_c03_trace_running_mean.tex")
SEAL = ROOT / "seal"
SUMMARY = SEAL / "MANIFEST_SUMMARY.json"
MANIFEST = SEAL / "SEALED_FILES_MANIFEST.csv"
WSTOP = ROOT / "WSTOP.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    SEAL.mkdir(parents=True, exist_ok=True)
    if MANIFEST.exists() or WSTOP.exists():
        raise SystemExit("Refusing to reseal: manifest or WSTOP already exists")

    timestamp = datetime.now().astimezone().isoformat(timespec="seconds")
    summary = {
        "handoff_id": "A-R104-P608-SA1-FRESH-ISOLATED-20260826",
        "figure_uid": "FIG-P608-01",
        "candidate": "R104",
        "role": "fresh isolated read-only SA1",
        "decision": "PASS",
        "next_status": "SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3",
        "a_local_pass_claimed": False,
        "sa3_started": False,
        "sealed_at": timestamp,
        "identity": {
            "candidate_pdf": str(PDF),
            "candidate_pdf_sha256": sha256(PDF),
            "current_source": str(SOURCE),
            "current_source_sha256": sha256(SOURCE),
        },
        "denominators": {
            "objects": 89,
            "text_glyphs": 68,
            "graphics": 21,
            "unordered_pairs_expected": 3916,
            "unordered_pairs_checked": 3916,
            "raw_drawing_records_mapped": 58,
            "portable_masks": 89,
            "manual_glyph_cells": 68,
            "manual_math_rules": 6,
            "manual_relation_rois": 23,
            "manual_views": 5,
            "manual_role_script_rows": 23,
        },
        "hard_fail_counts": {
            "missing_tofu_wrong_glyph": 0,
            "semantic_error": 0,
            "unreadable": 0,
            "visible_size_imbalance": 0,
            "clip_pixels": 0,
            "illegal_overlap_pixels": 0,
            "machine_gate_failures": 0,
        },
        "manifest_policy": {
            "listed_scope": "all regular files under evidence root present before manifest creation, except the manifest path itself and WSTOP",
            "excluded": ["seal/SEALED_FILES_MANIFEST.csv", "WSTOP.json"],
        },
    }
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    excluded = {MANIFEST.resolve(), WSTOP.resolve()}
    payload = sorted(
        (path for path in ROOT.rglob("*") if path.is_file() and path.resolve() not in excluded),
        key=lambda path: path.relative_to(ROOT).as_posix(),
    )
    with MANIFEST.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["relative_path", "bytes", "sha256"])
        for path in payload:
            writer.writerow([path.relative_to(ROOT).as_posix(), path.stat().st_size, sha256(path)])

    manifest_hash = sha256(MANIFEST)
    wstop = {
        "handoff_id": "A-R104-P608-SA1-FRESH-ISOLATED-20260826",
        "figure_uid": "FIG-P608-01",
        "candidate": "R104",
        "role": "fresh isolated read-only SA1",
        "decision": "PASS",
        "next_status": "SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3",
        "a_local_pass_claimed": False,
        "sa3_started": False,
        "sealed_at": timestamp,
        "write_stop": True,
        "listed_payload_files": len(payload),
        "manifest_relative_path": "seal/SEALED_FILES_MANIFEST.csv",
        "manifest_sha256": manifest_hash,
        "manifest_excludes": ["seal/SEALED_FILES_MANIFEST.csv", "WSTOP.json"],
        "post_seal_rule": "No file below this evidence root may be changed by this role after WSTOP creation.",
    }
    WSTOP.write_text(json.dumps(wstop, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": "SEALED",
        "decision": "PASS",
        "next_status": "SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3",
        "listed_payload_files": len(payload),
        "manifest_sha256": manifest_hash,
        "pdf_sha256": summary["identity"]["candidate_pdf_sha256"],
        "source_sha256": summary["identity"]["current_source_sha256"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
