from __future__ import annotations

import csv
import json
from itertools import combinations
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent


def rows(name):
    with (ROOT / name).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


checks = {}


def check(name, condition, detail):
    checks[name] = {"pass": bool(condition), "detail": detail}


objects = rows("object_manifest_machine.csv")
object_ids = [r["OBJECT_ID"] for r in objects]
check("object_count_unique", len(objects) == 23 and len(set(object_ids)) == 23, {"count": len(objects), "unique": len(set(object_ids))})
check("object_masks_nonempty", all(r["EMPTY_MASK"] == "FALSE" and int(r["MASK_AREA_PX"]) > 0 for r in objects), {"empty": sum(r["EMPTY_MASK"] == "TRUE" for r in objects)})
check("object_mask_files", all((ROOT / "object_masks" / r["SAFE_FILENAME"]).is_file() for r in objects), {"expected": 23})

pairs = rows("all_pairs_machine.csv")
pair_ids = [r["PAIR_ID"] for r in pairs]
pair_keys = [tuple(sorted((r["OBJECT_A"], r["OBJECT_B"]))) for r in pairs]
expected_keys = list(combinations(sorted(object_ids), 2))
check("all_pairs_coverage", len(pairs) == 253 and len(set(pair_ids)) == 253 and sorted(pair_keys) == sorted(expected_keys), {"actual": len(pairs), "expected": 253})
check("machine_pair_fail_zero", sum(r["MACHINE_STATUS"] == "FAIL" for r in pairs) == 0, {"fail_count": sum(r["MACHINE_STATUS"] == "FAIL" for r in pairs)})

manual_pairs = rows("manual_pair_review.csv")
manual_pair_ids = [r["PAIR_ID"] for r in manual_pairs]
check("manual_pair_coverage", len(manual_pairs) == 253 and len(set(manual_pair_ids)) == 253 and set(manual_pair_ids) == set(pair_ids), {"actual": len(manual_pairs), "expected": 253})
check("manual_pair_fail_zero", all(r["DECISION"] in {"PASS", "PASS_INTENTIONAL"} for r in manual_pairs), {"nonpass": [r["PAIR_ID"] for r in manual_pairs if r["DECISION"] not in {"PASS", "PASS_INTENTIONAL"}]})

critical = rows("critical_relations_machine.csv")
manual_critical = rows("manual_critical_review.csv")
critical_ids = {r["PAIR_ID"] for r in critical}
manual_critical_ids = {r["PAIR_ID"] for r in manual_critical}
critical_assets_ok = True
for pid in critical_ids:
    d = ROOT / "critical_rois" / pid
    critical_assets_ok &= all((d / name).is_file() for name in ("raw_1x.png", "mask_A_1x.png", "mask_B_1x.png", "intersection_1x.png", "overlay_1x.png", "overlay_8x_nearest.png"))
check("critical_coverage_assets", len(critical) == 15 and len(manual_critical) == 15 and critical_ids == manual_critical_ids and critical_assets_ok, {"machine": len(critical), "manual": len(manual_critical)})
check("critical_manual_complete", all(all(r[k] == "TRUE" for k in ("RAW_1X_OPENED", "MASK_A_OPENED", "MASK_B_OPENED", "INTERSECTION_OPENED", "OVERLAY_1X_OPENED", "OVERLAY_8X_OPENED")) and r["DECISION"] in {"PASS", "PASS_INTENTIONAL"} for r in manual_critical), {"rows": len(manual_critical)})

glyphs = rows("after_pixel_measurements.csv")
glyph_ids = [r["GLYPH_ID"] for r in glyphs]
check("glyph_count_unique_nonempty", len(glyphs) == 197 and len(set(glyph_ids)) == 197 and all(int(r["MASK_AREA_PX"]) > 0 for r in glyphs), {"count": len(glyphs), "unique": len(set(glyph_ids))})
check("glyph_assets", all((ROOT / "glyph_masks" / r["SAFE_FILENAME"]).is_file() and (ROOT / r["EVIDENCE_8X"]).is_file() and (ROOT / r["CONTACT_SHEET"]).is_file() for r in glyphs), {"glyph_masks": len(list((ROOT / "glyph_masks").glob("*.png"))), "glyph_8x": len(list((ROOT / "glyph_8x_nearest").glob("*.png"))), "sheets": len(list((ROOT / "glyph_contact_sheets").glob("*.png")))})
manual_glyphs = rows("manual_glyph_review.csv")
manual_glyph_ids = [r["GLYPH_ID"] for r in manual_glyphs]
check("manual_glyph_coverage", len(manual_glyphs) == 197 and len(set(manual_glyph_ids)) == 197 and set(manual_glyph_ids) == set(glyph_ids), {"actual": len(manual_glyphs), "expected": 197})
check("manual_glyph_complete", all(r["ORIGINAL_MATCH"] == "TRUE" and r["OVERLAY_COMPLETE"] == "TRUE" and r["MASK_ONLY_PURE"] == "TRUE" and int(r["MISSING_STROKE_PX"]) == 0 and int(r["FOREIGN_PIXEL_PX"]) == 0 and r["DECISION"] == "PASS_R168_HARD" for r in manual_glyphs), {"rows": len(manual_glyphs)})
check("legacy_advisory_counts", sum(r["LEGACY_PIXEL_MACHINE_STATUS"] == "FAIL" for r in glyphs) == 30 and sum(r["LEGACY_PIXEL_MACHINE_STATUS"] == "CALIBRATION_REQUIRED" for r in glyphs) == 16, {"legacy_fail": sum(r["LEGACY_PIXEL_MACHINE_STATUS"] == "FAIL" for r in glyphs), "punct_calibration": sum(r["LEGACY_PIXEL_MACHINE_STATUS"] == "CALIBRATION_REQUIRED" for r in glyphs)})

drawings = rows("drawing_map_machine.csv")
manual_drawings = rows("manual_drawing_review.csv")
check("drawing_coverage", len(drawings) == 18 and len(manual_drawings) == 18 and {r["DRAWING_SEQNO"] for r in drawings} == {r["DRAWING_SEQNO"] for r in manual_drawings}, {"machine": len(drawings), "manual": len(manual_drawings), "math_rules": sum(r["IS_MATH_RULE"] == "TRUE" for r in drawings)})
check("drawing_manual_pass", all(r["PATH_OPENED"] == "TRUE" and r["MAPPING_MATCH"] == "TRUE" and r["DECISION"] == "PASS" for r in manual_drawings), {"rows": len(manual_drawings)})

clip = rows("clip_report_machine.csv")
manual_clip = rows("manual_clip_review.csv")
check("clip_coverage_zero", len(clip) == 23 and len(manual_clip) == 23 and all(int(r["OUTSIDE_PIXEL_COUNT"]) == 0 and int(r["EDGE_TOUCH_PIXEL_COUNT"]) == 0 and r["MACHINE_CLIP_STATUS"] == "PASS" for r in clip) and all(int(r["OUTSIDE_PX"]) == 0 and int(r["EDGE_TOUCH_PX"]) == 0 and r["DECISION"] == "PASS" for r in manual_clip), {"machine": len(clip), "manual": len(manual_clip)})

view_roles = rows("manual_view_role_review.csv")
check("view_role_coverage", len(view_roles) == 32 and len({(r["VIEW"], r["ROLE"]) for r in view_roles}) == 32 and all(r["OPENED"] == "TRUE" and r["LEGIBLE"] == "TRUE" and r["HARMONIOUS"] == "TRUE" and r["NO_CROWDING"] == "TRUE" and r["GRAY_CONTRAST"] == "TRUE" and r["DECISION"] == "PASS" for r in view_roles), {"rows": len(view_roles)})

font = rows("manual_font_adjudication.csv")
check("r168_font_hard_gate", len(font) == 8 and all(r["R168_HARD_TOFU_WRONG_CODEPOINT"] == "FALSE" and r["R168_HARD_UNREADABLE"] == "FALSE" and r["R168_HARD_SEVERE_IMBALANCE"] == "FALSE" and r["R168_HARD_CLIP_OR_ILLEGAL_OVERLAP"] == "FALSE" and r["DECISION"] == "PASS_R168_HARD" for r in font), {"rows": len(font)})

sem = rows("manual_math_content_review.csv")
check("math_content_semantics", len(sem) == 12 and all(r["DECISION"] == "PASS" for r in sem), {"rows": len(sem)})

views = {
    "full_page_300dpi.png": (2481, 3508),
    "full_page_200dpi.png": (1654, 2339),
    "figure_crop_300dpi.png": (2000, 888),
    "standalone_300dpi.png": (1435, 740),
    "grayscale_300dpi.png": (2000, 888),
    "machine_native_full_page_300dpi.png": (2481, 3508),
}
actual_dims = {}
for name, expected in views.items():
    with Image.open(ROOT / name) as im:
        actual_dims[name] = im.size
check("native_view_dimensions", all(actual_dims[k] == v for k, v in views.items()), actual_dims)

for name in ("FINAL_REPORT.md", "SA3_CARD.md", "SA3_CARD.json", "RESULT.txt", "after_text_measurement_overlay_300dpi.png"):
    check(f"required_{name}", (ROOT / name).is_file() and (ROOT / name).stat().st_size > 0, {"bytes": (ROOT / name).stat().st_size if (ROOT / name).is_file() else 0})

bad_names = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file() and ":" in p.name]
cache_files = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file() and (p.suffix.lower() == ".pyc" or "__pycache__" in p.parts)]
check("portable_names_no_colon", not bad_names, bad_names)
check("cache_pyc_zero", not cache_files, cache_files)

machine_pass = all(v["pass"] for v in checks.values())
result = {
    "machine_validation_pass": machine_pass,
    "check_count": len(checks),
    "failed_checks": [k for k, v in checks.items() if not v["pass"]],
    "checks": checks,
    "manual_files_modified_by_validator": 0,
    "manual_decisions_generated_by_validator": 0,
}
(ROOT / "final_machine_validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
lines = ["# Final machine validation", "", f"- MACHINE_VALIDATION_PASS: `{str(machine_pass).lower()}`", f"- CHECK_COUNT: `{len(checks)}`", f"- FAILED_CHECKS: `{','.join(result['failed_checks']) if result['failed_checks'] else 'NONE'}`", "", "| Check | Pass | Detail |", "|---|---|---|"]
for key, value in checks.items():
    detail = json.dumps(value["detail"], ensure_ascii=False, separators=(",", ":")).replace("|", "\\|")
    lines.append(f"| {key} | {str(value['pass']).lower()} | `{detail}` |")
(ROOT / "final_machine_validation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
print(json.dumps(result, ensure_ascii=True, indent=2))
raise SystemExit(0 if machine_pass else 2)
