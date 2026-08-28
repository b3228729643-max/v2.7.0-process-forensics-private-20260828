from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P583-01\STRICT_R1_SA1_FRESH_R103_R168_20260825")
REPORT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\reports\P583_R1_R103_FRESH_SA1_REPORT.md")
HANDOFF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\handoff\A\A-R103-P583-SA1-FRESH-20260825.md")


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def main() -> None:
    objects = json.loads((ROOT / "machine" / "object_inventory.json").read_text(encoding="utf-8"))
    glyph_ids = {o["element_id"] for o in objects if o["kind"] == "GLYPH"}
    graphic_ids = {o["element_id"] for o in objects if o["kind"] == "GRAPHIC"}
    glyph_manual = read_csv(ROOT / "manual" / "glyph_manual_review.csv")
    graphic_manual = read_csv(ROOT / "manual" / "graphic_manual_review.csv")
    pair_manual = read_csv(ROOT / "manual" / "pair_visual_groups.csv")
    pairs = read_csv(ROOT / "pairs" / "all_unordered_pairs.csv")
    cross = json.loads((ROOT / "machine" / "machine_crosscheck.json").read_text(encoding="utf-8"))
    geometry = json.loads((ROOT / "machine" / "geometry_summary.json").read_text(encoding="utf-8"))

    expected_views = {
        "full_page_200dpi.png": (1654, 2339),
        "figure_crop_300dpi.png": (1930, 805),
        "standalone_300dpi.png": (1272, 663),
        "grayscale_300dpi.png": (1272, 663),
        "after_text_measurement_overlay_300dpi.png": (1272, 663),
    }
    view_dims = {name: list(Image.open(ROOT / name).size) for name in expected_views}
    critical = [r for r in pairs if r["critical"].lower() == "true"]
    critical_1x = sorted((ROOT / "critical").glob("PAIR-*_1x.png"))
    critical_8x = sorted((ROOT / "critical").glob("PAIR-*_8x_nearest.png"))
    ordinary_file_names = [p.name for p in ROOT.rglob("*") if p.is_file()]
    acceptance_text = (ROOT / "after_visual_acceptance.md").read_text(encoding="utf-8")
    report_text = REPORT.read_text(encoding="utf-8")
    handoff_text = HANDOFF.read_text(encoding="utf-8")
    duplicate_ids = len({o["element_id"] for o in objects}) != len(objects)
    duplicate_safe = len({o["safe_filename"] for o in objects}) != len(objects)

    checks = {
        "machine_hard_gates_pass": cross["machine_hard_gates_pass"] is True and geometry["machine_hard_gates_pass"] is True,
        "object_denominator_90": len(objects) == 90 and len(glyph_ids) == 71 and len(graphic_ids) == 19,
        "unordered_pairs_complete": len(pairs) == 4005 == 90*89//2,
        "critical_pair_count_18": len(critical) == 18,
        "critical_pair_files_complete": len(critical_1x) == 19 and len(critical_8x) == 19,
        "manual_glyph_ids_exact": len(glyph_manual) == 71 and {r["element_id"] for r in glyph_manual} == glyph_ids,
        "manual_graphic_ids_exact": len(graphic_manual) == 19 and {r["element_id"] for r in graphic_manual} == graphic_ids,
        "manual_glyph_rows_pass": all(r["original_match"] == "TRUE" and r["overlay_complete"] == "TRUE" and r["mask_only_pure"] == "TRUE" and r["missing_stroke_px"] == "0" and r["foreign_pixel_px"] == "0" and r["decision"] == "PASS" for r in glyph_manual),
        "manual_graphic_rows_pass": all(r["original_match"] == "TRUE" and r["overlay_complete"] == "TRUE" and r["mask_only_pure"] == "TRUE" and r["missing_stroke_px"] == "0" and r["foreign_pixel_px"] == "0" and r["decision"] == "PASS" for r in graphic_manual),
        "manual_pair_breakdown_complete": sum(int(r["pair_count"]) for r in pair_manual if r["group_id"] != "PVG-01" and r["group_id"] != "PVG-09") == 4005 and all(r["manual_decision"] == "PASS" for r in pair_manual),
        "canonical_view_dimensions": all(view_dims[name] == list(size) for name, size in expected_views.items()),
        "canonical_csvs_present": all((ROOT / name).is_file() for name in ("after_font_audit.csv", "after_pixel_measurements.csv", "after_overlap_report.csv")),
        "no_duplicate_object_or_safe_ids": not duplicate_ids and not duplicate_safe,
        "portable_file_names": all(":" not in name for name in ordinary_file_names),
        "no_illegal_overlap_or_clip": geometry["illegal_overlap_pixel_count"] == 0 and geometry["clip_pixel_count"] == 0 and geometry["clearance_fail_count"] == 0,
        "math_rule_reconciled": geometry["math_rule_object_count"] == 0 and geometry["math_rule_reconciliation"].startswith("PASS"),
        "scripts_do_not_generate_manual_fields": cross["manual_fields_generated_by_script"] is False,
        "manual_acceptance_complete": all(token in acceptance_text for token in ("FONT_VISUAL_HARMONY_PASS=true", "SEMANTICS_PASS=true", "Final fresh isolated SA1 verdict: **PASS**", "SA1_PASS_AWAIT_FRESH_ISOLATED_SA3")),
        "formal_report_complete": "正式 fresh isolated SA1 verdict：**PASS**" in report_text and "SA1_PASS_AWAIT_FRESH_ISOLATED_SA3" in report_text,
        "handoff_complete": "SA1_VERDICT=PASS" in handoff_text and "SA1_PASS_AWAIT_FRESH_ISOLATED_SA3" in handoff_text,
    }
    result = {
        "machine_final_crosscheck_pass": all(checks.values()),
        "checks": checks,
        "counts": {
            "glyph_objects": len(glyph_ids), "graphic_objects": len(graphic_ids), "total_objects": len(objects),
            "unordered_pairs": len(pairs), "critical_pairs": len(critical),
            "manual_glyph_rows": len(glyph_manual), "manual_graphic_rows": len(graphic_manual),
            "manual_pair_group_rows": len(pair_manual), "key_or_critical_1x_files": len(critical_1x), "key_or_critical_8x_files": len(critical_8x),
        },
        "view_dimensions": view_dims,
        "manual_fields_generated_by_validator": False,
    }
    (ROOT / "machine" / "final_crosscheck.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "machine" / "FINAL_MACHINE_RESULT.txt").write_text(("MACHINE_FINAL_CROSSCHECK=PASS\n" if result["machine_final_crosscheck_pass"] else "MACHINE_FINAL_CROSSCHECK=FAIL\n") + json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["machine_final_crosscheck_pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
