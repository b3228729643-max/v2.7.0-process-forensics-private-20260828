from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path

from PIL import Image

ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P654-01\STRICT_R23_SA3_FRESH_ISOLATED_R103_20260825")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r103_fullbook\main_full.pdf")


def read_csv(rel: str):
    with (ROOT / rel).open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest().upper()


checks = []


def check(name: str, condition: bool, detail):
    checks.append({"check": name, "status": "PASS" if condition else "FAIL", "detail": detail})


identity = json.loads((ROOT / "00_identity/official_candidate_identity.json").read_text(encoding="utf-8"))
summary = json.loads((ROOT / "02_machine/machine_summary.json").read_text(encoding="utf-8"))
objects = read_csv("02_machine/object_ledger.csv")
glyphs = read_csv("02_machine/glyph_ledger.csv")
graphics = read_csv("02_machine/graphic_ledger.csv")
pairs = read_csv("05_pairs/all_unordered_pairs.csv")
relations = read_csv("06_relations/seven_relations.csv")
critical = read_csv("08_critical_rois/critical_machine_index.csv")
manual_glyphs = read_csv("09_manual/manual_glyph_reviewer_ledger.csv")
manual_graphics = read_csv("09_manual/manual_graphic_reviewer_ledger.csv")
manual_pair_classes = read_csv("09_manual/manual_pair_class_reviewer_ledger.csv")
manual_critical = read_csv("09_manual/manual_critical_reviewer_ledger.csv")
manual_views = read_csv("09_manual/manual_view_reviewer_ledger.csv")
id_map = read_csv("02_machine/id_safe_filename_map.csv")

check("pdf_identity_size", PDF.stat().st_size == 4967184 == identity["file_size_bytes"], PDF.stat().st_size)
check("pdf_identity_hash", sha256(PDF) == identity["sha256"] == "9379A489E0C2A57A7DA670C98029BB27B3F1A385BF8E4C3BD14FE9B606AA0F23", identity["sha256"])
check("page_identity", identity["physical_page"] == 704 and identity["page_count"] == 817 and identity["page_format"] == "A4", [identity["physical_page"], identity["page_count"], identity["page_format"]])

object_ids = [r["object_id"] for r in objects]
glyph_ids = [r["object_id"] for r in glyphs]
graphic_ids = [r["object_id"] for r in graphics]
check("object_denominator", len(objects) == 114 and len(glyphs) == 93 and len(graphics) == 21 and len(set(object_ids)) == 114, [len(glyphs), len(graphics), len(objects)])
check("object_partition", set(object_ids) == set(glyph_ids) | set(graphic_ids) and not (set(glyph_ids) & set(graphic_ids)), "disjoint_complete")
check("math_rule_denominator", sum(r["object_type"] == "MATH_RULE" for r in graphics) == 1, sum(r["object_type"] == "MATH_RULE" for r in graphics))
check("empty_masks", all(int(r["mask_pixel_count"]) > 0 and int(r["empty_mask_count"]) == 0 for r in objects), sum(int(r["empty_mask_count"]) for r in objects))

expected_pairs = len(objects) * (len(objects) - 1) // 2
actual_pair_keys = {tuple(sorted((r["object_a"], r["object_b"]))) for r in pairs}
expected_pair_keys = set(itertools.combinations(sorted(object_ids), 2))
check("pair_denominator", len(pairs) == expected_pairs == 6441 and len(actual_pair_keys) == 6441, [len(pairs), expected_pairs, len(actual_pair_keys)])
check("pair_complete_set", actual_pair_keys == expected_pair_keys, [len(actual_pair_keys - expected_pair_keys), len(expected_pair_keys - actual_pair_keys)])
check("pair_machine_hard_gate", all(r["machine_relation"] == "NO_MACHINE_HARD_FAILURE" for r in pairs), sorted({r["machine_relation"] for r in pairs}))
check("overlap_zero_independent", all(int(r["overlap_pixel_count"]) == 0 for r in pairs if r["semantic_pair_class"] == "INDEPENDENT"), sum(int(r["overlap_pixel_count"]) for r in pairs if r["semantic_pair_class"] == "INDEPENDENT"))
check("clearance_hard_gate", all(r["clearance_hard_eval"] != "FAIL" for r in pairs), sum(r["clearance_hard_eval"] == "FAIL" for r in pairs))
check("clip_zero", summary["clip_pixel_count"] == 0, summary["clip_pixel_count"])
check("text_edge_clearance", summary["minimum_text_to_body_edge_clearance_px"] >= 6, summary["minimum_text_to_body_edge_clearance_px"])

check("seven_relations", len(relations) == 7 and {r["relation_id"] for r in relations} == {f"R{i}" for i in range(1, 8)} and all(r["machine_structure_status"] == "COMPLETE" for r in relations), len(relations))
check("glyph_numeric_gate", len(glyphs) == 93 and all(r["threshold_eval"] == "MEETS" for r in glyphs), sum(r["threshold_eval"] == "MEETS" for r in glyphs))

check("manual_glyph_ids", len(manual_glyphs) == 93 and {r["element_id"] for r in manual_glyphs} == set(glyph_ids), len(manual_glyphs))
check("manual_glyph_pass", all(r["decision"] == "PASS" and r["original_match"] == "true" and r["overlay_complete"] == "true" and r["mask_only_pure"] == "true" and int(r["missing_stroke_px"]) == 0 and int(r["foreign_pixel_px"]) == 0 for r in manual_glyphs), sum(r["decision"] == "PASS" for r in manual_glyphs))
check("manual_graphic_ids", len(manual_graphics) == 21 and {r["element_id"] for r in manual_graphics} == set(graphic_ids), len(manual_graphics))
check("manual_graphic_pass", all(r["decision"] == "PASS" and r["original_match"] == "true" and r["overlay_complete"] == "true" and r["mask_only_pure"] == "true" and int(r["missing_stroke_px"]) == 0 and int(r["foreign_pixel_px"]) == 0 for r in manual_graphics), sum(r["decision"] == "PASS" for r in manual_graphics))
class_rows = [r for r in manual_pair_classes if r["manual_class_id"] != "TOTAL"]
check("manual_pair_class_denominator", sum(int(r["covered_pair_count"]) for r in class_rows) == 6441 and all(r["decision"] == "PASS" for r in manual_pair_classes), [len(class_rows), sum(int(r["covered_pair_count"]) for r in class_rows)])
check("critical_denominator", len(critical) == 14 and len(manual_critical) == 14 and {r["critical_id"] for r in critical} == {r["critical_id"] for r in manual_critical}, [len(critical), len(manual_critical)])
check("manual_critical_opened", all(r["decision"] == "PASS" and all(r[k] == "true" for k in ("original_opened", "overlay_opened", "mask_panel_opened", "view_1x", "view_8x")) for r in manual_critical), sum(r["decision"] == "PASS" for r in manual_critical))
check("manual_view_coverage", len(manual_views) == 11 and all(r["actually_opened"] == "true" and r["decision"] == "PASS" for r in manual_views), len(manual_views))

check("id_safe_map", len(id_map) == 114 and len({r["safe_filename"] for r in id_map}) == 114 and {r["object_id"] for r in id_map} == set(object_ids), len(id_map))
pack_ok = True
for row in id_map:
    path = ROOT / row["pack_path"]
    if not path.is_file() or ":" in path.name:
        pack_ok = False
        break
    with Image.open(path) as im:
        im.verify()
check("ordinary_pack_files_open", pack_ok, 114)

image_paths = [
    "full_page_200dpi.png",
    "figure_crop_300dpi.png",
    "standalone_300dpi.png",
    "grayscale_300dpi.png",
    "after_text_measurement_overlay_300dpi.png",
    "05_pairs/pair_matrix_1x.png",
    "05_pairs/pair_matrix_8x_nearest.png",
    "06_relations/seven_relations_overlay_300dpi.png",
] + [f"07_contact_sheets/glyph_contact_sheet_{i:02d}.png" for i in range(1, 8)] + [f"07_contact_sheets/graphic_contact_sheet_{i:02d}.png" for i in range(1, 4)] + [f"08_critical_rois/CRITICAL_{i:04d}.png" for i in range(1, 15)]
images_ok = True
image_dimensions = {}
for rel in image_paths:
    path = ROOT / rel
    try:
        with Image.open(path) as im:
            image_dimensions[rel] = list(im.size)
            im.verify()
    except Exception:
        images_ok = False
        break
check("required_images_open", images_ok and len(image_dimensions) == len(image_paths), len(image_dimensions))
check("native_view_dimensions", image_dimensions.get("full_page_200dpi.png") == [1654, 2339] and image_dimensions.get("figure_crop_300dpi.png") == [1939, 796] and image_dimensions.get("standalone_300dpi.png") == [1939, 688] and image_dimensions.get("grayscale_300dpi.png") == [1939, 796], {k: image_dimensions.get(k) for k in image_paths[:4]})

required_files = [
    "after_font_audit.csv",
    "after_pixel_measurements.csv",
    "after_overlap_report.csv",
    "after_visual_acceptance.md",
    "02_machine/machine_summary.json",
    "02_machine/font_de_advisory.csv",
    "02_machine/font_role_summary.csv",
    "05_pairs/all_unordered_pairs.csv",
    "06_relations/seven_relations.csv",
]
check("required_artifacts", all((ROOT / rel).is_file() for rel in required_files), required_files)
check("no_manual_script_fields", summary["manual_fields_generated_by_script"] == 0, summary["manual_fields_generated_by_script"])

all_pass = all(r["status"] == "PASS" for r in checks)
result = {
    "validator": "validate_fresh_evidence.py",
    "uid": "FIG-P654-01",
    "handoff_id": "A-R103-P654-SA3-FRESH-ISOLATED-20260825",
    "check_count": len(checks),
    "failure_count": sum(r["status"] == "FAIL" for r in checks),
    "machine_cross_validation_status": "PASS" if all_pass else "FAIL",
    "checks": checks,
}
(ROOT / "10_validation/validation_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
with (ROOT / "10_validation/validation_checks.csv").open("w", encoding="utf-8-sig", newline="") as fh:
    writer = csv.DictWriter(fh, fieldnames=["check", "status", "detail"])
    writer.writeheader()
    writer.writerows(checks)
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if all_pass else 1)
