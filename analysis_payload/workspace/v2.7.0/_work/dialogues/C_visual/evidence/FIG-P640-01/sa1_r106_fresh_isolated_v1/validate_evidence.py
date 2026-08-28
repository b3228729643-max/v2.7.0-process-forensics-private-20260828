import csv
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
OUT = ROOT / "validation.json"


def rows(name):
    with (ROOT / name).open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


checks = []


def check(name, condition, observed):
    checks.append({"check": name, "pass": bool(condition), "observed": observed})


identity = json.loads((ROOT / "resolved_identity.json").read_text(encoding="utf-8"))
summary = json.loads((ROOT / "machine_summary.json").read_text(encoding="utf-8"))
expected_identity = {
    "uid": "FIG-P640-01",
    "handoff_id": "C-FIG-P640-01-R106-SA1-FRESH-ISOLATED-V1",
    "physical_page": 690,
    "printed_page": 677,
    "figure_number": "33.7",
    "pdf_pages": 817,
    "pdf_bytes": 4967249,
    "pdf_sha256": "0FA4A5A0B35D2566D71B5472B49E9B4A8A60CBAE76B3FA744B92783AFC6BC31A",
}
for key, value in expected_identity.items():
    check(f"identity.{key}", identity.get(key) == value, identity.get(key))

expected_counts = {
    "machine_span_inventory.csv": 74,
    "machine_glyph_inventory.csv": 242,
    "machine_drawing_inventory.csv": 20,
    "machine_object_inventory.csv": 94,
    "machine_all_pairs.csv": 4371,
    "machine_critical_candidates.csv": 71,
    "machine_role_metrics.csv": 43,
    "id_safe_filename.csv": 262,
    "manual_glyph_review.csv": 242,
    "manual_object_review.csv": 94,
    "manual_critical_relation_review.csv": 71,
    "manual_role_peer_review.csv": 49,
    "manual_view_review.csv": 27,
    "manual_hard_gate_review.csv": 20,
}
loaded = {}
for name, expected in expected_counts.items():
    loaded[name] = rows(name)
    check(f"rows.{name}", len(loaded[name]) == expected, len(loaded[name]))

object_ids = [row["object_id"] for row in loaded["machine_object_inventory.csv"]]
glyph_ids = [row["glyph_id"] for row in loaded["machine_glyph_inventory.csv"]]
pair_ids = [row["pair_id"] for row in loaded["machine_all_pairs.csv"]]
critical_ids = [row["pair_id"] for row in loaded["machine_critical_candidates.csv"]]
manual_object_ids = [row["object_id"] for row in loaded["manual_object_review.csv"]]
manual_glyph_ids = [row["glyph_id"] for row in loaded["manual_glyph_review.csv"]]
manual_critical_ids = [row["pair_id"] for row in loaded["manual_critical_relation_review.csv"]]

for label, ids in (("objects", object_ids), ("glyphs", glyph_ids), ("pairs", pair_ids), ("critical", critical_ids)):
    check(f"unique.{label}", len(ids) == len(set(ids)), f"{len(set(ids))}/{len(ids)}")
check("set.manual_objects", set(manual_object_ids) == set(object_ids), f"{len(set(manual_object_ids))}/{len(set(object_ids))}")
check("set.manual_glyphs", set(manual_glyph_ids) == set(glyph_ids), f"{len(set(manual_glyph_ids))}/{len(set(glyph_ids))}")
check("set.manual_critical", set(manual_critical_ids) == set(critical_ids), f"{len(set(manual_critical_ids))}/{len(set(critical_ids))}")
check("pairs.C94_2", len(pair_ids) == 94 * 93 // 2, len(pair_ids))

manual_specs = {
    "manual_glyph_review.csv": ("glyph_id", ["reviewer", "contact_sheet", "cell", "original_match", "overlay_complete", "mask_only_pure", "missing_stroke_px", "foreign_pixel_px", "r168_hard_failure", "decision", "note"]),
    "manual_object_review.csv": ("object_id", ["reviewer", "evidence_view", "content_or_path_complete", "semantic_correct", "clip_free", "decision", "note"]),
    "manual_critical_relation_review.csv": ("pair_id", ["reviewer", "native_1x_opened", "nearest_8x_opened", "objects_correct", "intersection_px", "clearance_px", "relation_judgment", "illegal_overlap", "decision", "note"]),
    "manual_role_peer_review.csv": ("review_id", ["reviewer", "scope", "object_count_or_peer_ids", "views_opened", "numeric_observation", "r168_hard_scope_judgment", "decision", "note"]),
    "manual_view_review.csv": ("view_id", ["reviewer", "file", "native_dimensions_or_scope", "opened", "readability", "geometry", "grayscale_or_color", "page_integration", "decision", "note"]),
    "manual_hard_gate_review.csv": ("gate_id", ["reviewer", "hard_gate", "manual_evidence", "observed_count_or_state", "r168_classification", "decision", "note"]),
}
for name, (id_field, fields) in manual_specs.items():
    data = loaded[name]
    check(f"manual.{name}.no_blank_fields", all(all(str(row.get(field, "")).strip() for field in fields) for row in data), len(data))
    check(f"manual.{name}.all_pass", all(row["decision"] == "PASS" for row in data), len(data))
    check(f"manual.{name}.unique_ids", len({row[id_field] for row in data}) == len(data), len(data))
    check(f"manual.{name}.unique_notes", len({row["note"] for row in data}) == len(data), len(data))

glyph_manual = loaded["manual_glyph_review.csv"]
check("glyph.manual_booleans", all(row["original_match"] == "true" and row["overlay_complete"] == "true" and row["mask_only_pure"] == "true" for row in glyph_manual), len(glyph_manual))
check("glyph.manual_zero_defects", all(row["missing_stroke_px"] == "0" and row["foreign_pixel_px"] == "0" for row in glyph_manual), len(glyph_manual))
check("glyph.r168_hard_failure_zero", all(row["r168_hard_failure"] == "false" for row in glyph_manual), len(glyph_manual))
critical_manual = loaded["manual_critical_relation_review.csv"]
check("critical.manual_views", all(row["native_1x_opened"] == "true" and row["nearest_8x_opened"] == "true" and row["objects_correct"] == "true" for row in critical_manual), len(critical_manual))
check("critical.illegal_overlap_zero", all(row["illegal_overlap"] == "false" for row in critical_manual), len(critical_manual))

expected_core = [
    "full_page_200dpi.png", "full_page_300dpi.png", "figure_crop_300dpi.png", "standalone_300dpi.png",
    "grayscale_300dpi.png", "right_panel_300dpi.png", "right_panel_8x_nearest.png",
    "after_font_audit.csv", "after_pixel_measurements.csv", "after_overlap_report.csv",
    "after_text_measurement_overlay_300dpi.png", "after_visual_acceptance.md", "RESULT.json", "SA1_FRESH_HANDOFF.md",
]
check("files.required_core", all((ROOT / name).is_file() for name in expected_core), len(expected_core))

glyph_masks = sorted((ROOT / "masks" / "glyph").glob("*.png"))
object_masks = sorted((ROOT / "masks" / "object").glob("*.png"))
glyph_contacts = sorted((ROOT / "contacts").glob("glyph_contact_*.png"))
math_contacts = sorted((ROOT / "contacts").glob("math_rule_D020_*.png"))
roi_files = sorted((ROOT / "roi").glob("*.png"))
check("files.glyph_masks", len(glyph_masks) == 242, len(glyph_masks))
check("files.object_masks", len(object_masks) == 20, len(object_masks))
check("files.glyph_contacts", len(glyph_contacts) == 13, len(glyph_contacts))
check("files.math_contacts", len(math_contacts) == 2, len(math_contacts))
check("files.critical_roi", len(roi_files) == 142, len(roi_files))
expected_roi_names = {f"{pair_id}_{suffix}.png" for pair_id in critical_ids for suffix in ("1x", "8x_nearest")}
check("files.critical_roi_exact_set", {path.name for path in roi_files} == expected_roi_names, len(expected_roi_names))

pngs = sorted(ROOT.rglob("*.png"))
png_errors = []
for path in pngs:
    try:
        with Image.open(path) as image:
            image.verify()
    except Exception as exc:
        png_errors.append(f"{path.relative_to(ROOT)}:{type(exc).__name__}")
check("png.all_openable", not png_errors, {"count": len(pngs), "errors": png_errors})

check("summary.objects", summary["counts"]["objects"] == 94, summary["counts"]["objects"])
check("summary.pairs", summary["counts"]["all_unordered_pairs"] == 4371, summary["counts"]["all_unordered_pairs"])
check("summary.empty_masks", summary["counts"]["empty_glyph_masks"] == 0 and summary["counts"]["empty_object_masks"] == 0, [summary["counts"]["empty_glyph_masks"], summary["counts"]["empty_object_masks"]])

result = {
    "handoff_id": "C-FIG-P640-01-R106-SA1-FRESH-ISOLATED-V1",
    "validator": "validate_evidence.py",
    "checks": checks,
    "check_count": len(checks),
    "failed_check_count": sum(not item["pass"] for item in checks),
    "result": "PASS" if all(item["pass"] for item in checks) else "FAIL",
}
OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"result": result["result"], "check_count": result["check_count"], "failed": result["failed_check_count"]}))
raise SystemExit(0 if result["result"] == "PASS" else 1)
