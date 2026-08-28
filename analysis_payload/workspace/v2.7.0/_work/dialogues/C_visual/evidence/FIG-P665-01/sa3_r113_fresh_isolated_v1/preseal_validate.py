from __future__ import annotations

import ast
import csv
import itertools
import json
import os
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\C_visual\evidence\FIG-P665-01\sa3_r113_fresh_isolated_v1")
OUT = ROOT / "preseal_validation.json"
MARKER = ROOT / "FINAL_SEAL_MARKER.txt"
MANIFEST = ROOT / "manifest.csv"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


require(ROOT.is_dir(), "assigned root missing")
require(not MARKER.exists(), "final marker already exists")
require(not MANIFEST.exists(), "manifest unexpectedly exists before preseal validation")
require(not OUT.exists(), "preseal validation must be created exactly once")

required = {
    "full_page_300dpi.png",
    "full_page_grayscale_native_300dpi.png",
    "full_page_figure_location_overlay_300dpi.png",
    "figure_caption_native_300dpi.png",
    "figure_caption_grayscale_native_300dpi.png",
    "object_bbox_overlay_300dpi.png",
    "semantic_role_overlay_300dpi.png",
    "text_measurement_overlay_300dpi.png",
    "reading_order_overlay_300dpi.png",
    "closest_pair_numeric_risk_overlay_300dpi.png",
    "object_denominator_frozen.csv",
    "all_unordered_pairs_machine.csv",
    "codepoint_audit_machine.csv",
    "clip_check_machine.csv",
    "near_threshold_mask_gaps_machine.csv",
    "manual_object_ledger.md",
    "manual_codepoint_ledger.md",
    "manual_pair_and_overlap_adjudication.md",
    "manual_math_semantics_recompute.md",
    "manual_visual_acceptance.md",
    "manual_view_ledger.md",
    "sa3_report.md",
}
missing = sorted(name for name in required if not (ROOT / name).is_file())
require(not missing, f"required evidence missing: {missing}")

cache_names = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
cache_items = []
reparse_like = []
parse_errors = []
parsed_counts = {"csv": 0, "json": 0, "python": 0, "text": 0}

for path in sorted(ROOT.rglob("*")):
    rel = path.relative_to(ROOT).as_posix()
    if path.name in cache_names or path.suffix.lower() in {".pyc", ".pyo"}:
        cache_items.append(rel)
    if path.is_symlink():
        reparse_like.append(rel)
    if not path.is_file():
        continue
    try:
        suffix = path.suffix.lower()
        if suffix == ".csv":
            with path.open("r", encoding="utf-8", newline="") as f:
                rows = list(csv.reader(f))
            require(bool(rows), f"empty CSV: {rel}")
            width = len(rows[0])
            require(width > 0 and all(len(row) == width for row in rows), f"ragged CSV: {rel}")
            parsed_counts["csv"] += 1
        elif suffix == ".json":
            json.loads(path.read_text(encoding="utf-8"))
            parsed_counts["json"] += 1
        elif suffix == ".py":
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            parsed_counts["python"] += 1
        elif suffix in {".md", ".txt", ".ps1"}:
            text = path.read_text(encoding="utf-8")
            require("\x00" not in text, f"NUL in text file: {rel}")
            parsed_counts["text"] += 1
    except Exception as exc:
        parse_errors.append(f"{rel}: {exc}")

require(not cache_items, f"cache/pyc hygiene failure: {cache_items}")
require(not reparse_like, f"symlink/reparse-like hygiene failure: {reparse_like}")
require(not parse_errors, f"parse failures: {parse_errors}")

with (ROOT / "object_denominator_frozen.csv").open("r", encoding="utf-8", newline="") as f:
    objects = list(csv.DictReader(f))
object_ids = [row["OBJECT_ID"] for row in objects]
expected_ids = [f"O{i:02d}" for i in range(1, 23)]
require(object_ids == expected_ids, f"object denominator mismatch: {object_ids}")

with (ROOT / "all_unordered_pairs_machine.csv").open("r", encoding="utf-8", newline="") as f:
    pairs = list(csv.DictReader(f))
actual_pairs = {(row["OBJECT_A"], row["OBJECT_B"]) for row in pairs}
expected_pairs = set(itertools.combinations(expected_ids, 2))
require(len(pairs) == 231, f"pair row count mismatch: {len(pairs)}")
require(actual_pairs == expected_pairs, "all-unordered-pairs coverage mismatch")
require(len(actual_pairs) == len(pairs), "duplicate pair rows")
require(sum(int(row["COLLISION_MASK_OVERLAP_PX"]) for row in pairs) == 0, "nonzero pair mask overlap")
require(sum(row["MACHINE_RISK_TRIGGER"] == "NUMERIC_CLEARANCE_RISK" for row in pairs) == 1, "unexpected numeric-risk count")

with (ROOT / "clip_check_machine.csv").open("r", encoding="utf-8", newline="") as f:
    clips = list(csv.DictReader(f))
require(len(clips) == 22, "clip row count mismatch")
require(all(int(row["VISIBLE_MASK_TOUCH_CROP_EDGE_2PX"]) == 0 for row in clips), "crop-edge touch detected")
require(all(int(row["BBOX_OUTSIDE_FULL_PAGE_PX_SUM"]) == 0 for row in clips), "bbox outside page detected")

with (ROOT / "codepoint_audit_machine.csv").open("r", encoding="utf-8", newline="") as f:
    codepoints = list(csv.DictReader(f))
require(len(codepoints) == 22, "codepoint denominator mismatch")
require(sum(int(row["REPLACEMENT_OR_TOFU_CODEPOINT_COUNT"]) for row in codepoints) == 0, "tofu/replacement candidate detected")

with (ROOT / "near_threshold_mask_gaps_machine.csv").open("r", encoding="utf-8", newline="") as f:
    near = list(csv.DictReader(f))
require(near, "near-threshold mask-gap table empty")
min_gap = min(float(row["RASTER_BLANK_PIXEL_GAP_ESTIMATE_PX"]) for row in near)
require(abs(min_gap - 7.0) < 1e-9, f"unexpected minimum raster gap: {min_gap}")

mask_files = sorted((ROOT / "masks").glob("O??_collision_mask.png"))
require(len(mask_files) == 22, f"mask count mismatch: {len(mask_files)}")
roi_files = sorted((ROOT / "rois").glob("*.png"))
require(len(roi_files) == 10, f"ROI file count mismatch: {len(roi_files)}")

manual_objects = (ROOT / "manual_object_ledger.md").read_text(encoding="utf-8")
for oid in expected_ids:
    require(f"| {oid} |" in manual_objects, f"manual object ledger missing {oid}")

acceptance = (ROOT / "manual_visual_acceptance.md").read_text(encoding="utf-8")
report = (ROOT / "sa3_report.md").read_text(encoding="utf-8")
verdict = "SA3_PASS_AWAIT_MAIN_C_LOCAL_PASS_ACCEPTANCE"
require(f"`VERDICT = {verdict}`" in acceptance, "acceptance verdict missing")
require(f"`RESULT: {verdict}`" in report, "report verdict missing")
require("`UNRESOLVED_COUNT = 0`" in acceptance, "unresolved count not closed")

payload = {
    "status": "PRESEAL_VALID",
    "handoff_id": "C-FIG-P665-01-R113-SA3-FRESH-ISOLATED-V1",
    "uid": "FIG-P665-01",
    "verdict": verdict,
    "object_rows": len(objects),
    "pair_rows": len(pairs),
    "mask_overlap_pixels": 0,
    "minimum_raster_blank_gap_px": min_gap,
    "clip_edge_touch_objects": 0,
    "tofu_replacement_candidates": 0,
    "mask_files": len(mask_files),
    "roi_files": len(roi_files),
    "parse_counts_before_validation_file": parsed_counts,
    "parse_errors": 0,
    "cache_pyc_items": 0,
    "symlink_reparse_like_items": 0,
    "ads_check_deferred_to_windows_seal_step": True,
    "windows_reparse_check_deferred_to_windows_seal_step": True,
}
OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
roundtrip = json.loads(OUT.read_text(encoding="utf-8"))
require(roundtrip == payload, "preseal validation JSON roundtrip mismatch")
print(json.dumps(payload, ensure_ascii=False))
