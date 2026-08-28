from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
QC_JSON = ROOT / "08_qc" / "final_crosscheck.json"
QC_MD = ROOT / "08_qc" / "final_crosscheck.md"


def load_json(rel: str):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def load_csv(rel: str):
    with (ROOT / rel).open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


checks: list[dict[str, object]] = []


def check(name: str, condition: bool, detail: object) -> None:
    checks.append({"name": name, "pass": bool(condition), "detail": detail})


def image_ok(rel: str) -> bool:
    path = ROOT / rel
    if not path.is_file() or path.stat().st_size <= 0:
        return False
    with Image.open(path) as im:
        im.verify()
    return True


def all_nonblank(rows: list[dict[str, str]]) -> bool:
    return bool(rows) and all(
        value is not None and str(value).strip() != ""
        for row in rows
        for value in row.values()
    )


identity = load_json("00_identity/input_identity.json")
check("identity_handoff", identity["handoff_id"] == "A-R107-P020-SA1-FRESH-ISOLATED-20260826", identity["handoff_id"])
check("identity_role_model_effort", (identity["role"], identity["model"], identity["reasoning_effort"]) == ("SA1", "gpt-5.6-sol", "xhigh"), [identity["role"], identity["model"], identity["reasoning_effort"]])
check("identity_uid_round", (identity["canonical_uid"], identity["official_round"]) == ("FIG-P020-01", "R107"), [identity["canonical_uid"], identity["official_round"]])
check("independent_unique_locator", identity["caption_match_count"] == 1 and identity["physical_page_1based"] == 17 and identity["page_index_0based"] == 16 and identity["page_label"] == "4", [identity["caption_match_count"], identity["physical_page_1based"], identity["page_index_0based"], identity["page_label"]])
check("input_hashes_frozen", identity["official_pdf_sha256"] == "8811950621E2D64A3C2A8F0F7A52DD0FAC2BDB12018F3EA052C1F58C94EF8DF3" and identity["source_sha256"] == "FF006894E35D1D3E79F1C1D85D212B79735F3D11937B17F23A49D68DC97547CE", "official PDF and source hashes exact")

manifest = load_json("02_extraction/object_manifest_N_C.json")
check("N_and_C_frozen", manifest["glyph_count"] == 108 and manifest["foreground_graphic_path_count"] == 14 and manifest["math_rule_count"] == 0 and manifest["N_total_foreground_objects"] == 122 and manifest["C_N_2_expected_unordered_pairs"] == 7381 and manifest["C_N_2_emitted_unordered_pairs"] == 7381, manifest)
check("object_identity_unique", manifest["object_ids_unique"] is True and manifest["safe_filenames_unique"] is True, [manifest["object_ids_unique"], manifest["safe_filenames_unique"]])

glyphs = load_csv("02_extraction/glyph_inventory.csv")
graphics = load_csv("02_extraction/foreground_graphic_inventory.csv")
safe_map = load_csv("02_extraction/id_safe_filename_map.csv")
check("inventory_counts", len(glyphs) == 108 and len(graphics) == 14 and len(safe_map) == 122, {"glyphs": len(glyphs), "graphics": len(graphics), "safe_map": len(safe_map)})
all_ids = [row["object_id"] for row in glyphs] + [row["object_id"] for row in graphics]
check("inventory_ids_unique", len(all_ids) == len(set(all_ids)) == 122, len(set(all_ids)))

drawing = load_json("02_extraction/drawing_bidirectional_accounting.json")
check("visible_drawing_accounting", drawing["target_foreground_count"] == 14 and drawing["target_background_count"] == 2 and drawing["target_math_rule_count"] == 0 and drawing["target_unaccounted_visible_drawing_seqnos"] == [], drawing)

pixel_rows = load_csv("05_ledgers/after_pixel_measurements.csv")
check("pixel_row_count", len(pixel_rows) == 108, len(pixel_rows))
check("machine_masks_nonempty_pure", all(row["machine_empty_mask"].lower() == "false" and int(row["machine_foreign_intersection_candidate_px"]) == 0 for row in pixel_rows), "108/108 nonempty; foreign candidate 0")

mask_paths: list[str] = []
for row in pixel_rows:
    mask_paths.extend([row["mask_path"], row["original_path"], row["overlay_path"]])
for row in graphics:
    mask_paths.extend([row["mask_path"], row["original_path"], row["overlay_path"]])
check("raw_object_image_denominator", len(mask_paths) == 366 and all(image_ok(rel) for rel in mask_paths), f"{len(mask_paths)}/366 valid PNGs")

font_rows = load_csv("05_ledgers/after_font_audit.csv")
check("source_font_elements", len(font_rows) == 10 and all(float(row["effective_pt"]) >= 9.5 and float(row["graphics_scale"]) == 1.0 and row["machine_effective_pt_gate"] == "MEETS_9_5PT" for row in font_rows), f"{len(font_rows)}/10")

overlap = load_json("05_ledgers/after_overlap_report.json")
pair_keys = [tuple(sorted((row["object_a"], row["object_b"]))) for row in overlap]
gate_counts = Counter(row["machine_gate"] for row in overlap)
check("pair_exhaustiveness", len(overlap) == 7381 and len(set(pair_keys)) == 7381, {"rows": len(overlap), "unique_pairs": len(set(pair_keys))})
check("pair_gate_partition", gate_counts == Counter({"MEETS_MACHINE_GATE": 6207, "DESIGN_WHITELIST": 1174}), dict(gate_counts))
illegal_overlap_sum = sum(int(row["overlap_candidate_px"]) for row in overlap if not row["design_whitelist"])
check("illegal_overlap_zero", illegal_overlap_sum == 0, illegal_overlap_sum)
check("machine_pair_failures_zero", all(row["machine_gate"] in {"MEETS_MACHINE_GATE", "DESIGN_WHITELIST"} for row in overlap), "0 failure/unknown rows")

clip_rows = load_csv("05_ledgers/clip_report.csv")
check("clip_gate", len(clip_rows) == 122 and all(int(row["clip_pixel_count"]) == 0 and row["machine_gate"] == "CLEAR" for row in clip_rows), {"rows": len(clip_rows), "clip_pixels": sum(int(row["clip_pixel_count"]) for row in clip_rows)})
check("minimum_crop_edge", min(int(row["min_figure_crop_edge_clearance_px"]) for row in clip_rows) == 25, 25)

punct_same = load_csv("05_ledgers/punctuation_calibration_machine.csv")
punct_sep = load_csv("05_ledgers/punctuation_separate_calibration_machine.csv")
same_comparable = [row for row in punct_same if row["machine_calibration_gate"] == "COMPARABLE"]
same_deferred = [row for row in punct_same if row["machine_calibration_gate"] == "SEPARATE_CALIBRATION_PENDING"]
check("punctuation_calibration_partition", len(punct_same) == 7 and len(same_comparable) == 5 and {row["glyph_id"] for row in same_deferred} == {"G053", "G068"}, {"all": len(punct_same), "comparable": len(same_comparable), "separate_actual_font": [row["glyph_id"] for row in same_deferred]})
check("actual_font_punctuation_calibration", {row["glyph_id"] for row in punct_sep} == {"G053", "G068"} and all(float(row["h_ratio_target_to_calibration"]) == 1.0 and row["machine_calibration_gate"] == "R168_ADVISORY_RASTER_OR_ENGINE_DIFFERENCE" for row in punct_sep), [row["glyph_id"] for row in punct_sep])
calibration_images = [rel for row in punct_sep for rel in (row["original_1x"], row["mask_only_1x"], row["overlay_1x"], row["overlay_8x_nearest"])]
check("calibration_image_denominator", len(calibration_images) == 8 and all(image_ok(rel) for rel in calibration_images), f"{len(calibration_images)}/8")

glyph_sheets = [f"04_contact_sheets/glyph_contact_sheet_{i:02d}.png" for i in range(1, 13)]
graphic_sheets = [f"04_contact_sheets/graphic_contact_sheet_{i:02d}.png" for i in range(1, 5)]
check("glyph_contact_sheet_denominator", all(image_ok(rel) for rel in glyph_sheets), "12/12")
check("graphic_contact_sheet_denominator", all(image_ok(rel) for rel in graphic_sheets), "4/4")

required_views = [
    "01_renders/full_page_200dpi.png",
    "01_renders/full_page_300dpi.png",
    "01_renders/figure_crop_300dpi.png",
    "01_renders/standalone_300dpi.png",
    "01_renders/grayscale_300dpi.png",
    "01_renders/after_text_measurement_overlay_300dpi.png",
    "01_renders/foreground_object_overlay_300dpi.png",
]
check("required_view_files", all(image_ok(rel) for rel in required_views), f"{len(required_views)}/{len(required_views)}")

critical = load_json("05_ledgers/critical_relations_machine.json")
relation_files = ["raw_original_1x.png", "raw_mask_a_1x.png", "raw_mask_b_1x.png", "raw_intersection_1x.png", "raw_overlay_ab_1x.png", "five_panel_1x.png", "five_panel_8x_nearest.png"]
relation_image_paths = [f"{row['evidence_dir']}/{name}" for row in critical for name in relation_files]
check("critical_relation_count", len(critical) == 11, len(critical))
check("critical_relation_evidence_denominator", len(relation_image_paths) == 77 and all(image_ok(rel) for rel in relation_image_paths), f"{len(relation_image_paths)}/77")
check("critical_machine_gates", all(row["machine_gate"] in {"MEETS_MACHINE_GATE", "DESIGN_WHITELIST"} for row in critical), "11/11")

manual_specs = {
    "manual_glyph_review.csv": (108, "glyph_id"),
    "manual_graphic_review.csv": (14, "object_id"),
    "manual_relation_review.csv": (11, "relation_id"),
    "manual_view_review.csv": (8, "view_id"),
    "manual_panel_role_review.csv": (4, "role"),
    "manual_source_font_review.csv": (10, "element_id"),
}
manual_summary: dict[str, int] = {}
for name, (expected, id_field) in manual_specs.items():
    rows = load_csv(f"05_ledgers/{name}")
    manual_summary[name] = len(rows)
    check(f"manual_{name}_closed", len(rows) == expected and len({row[id_field] for row in rows}) == expected and all_nonblank(rows) and all(row["manual_decision"] == "PASS" for row in rows), f"{len(rows)}/{expected}; all fields nonblank; decisions PASS")

manual_glyphs = load_csv("05_ledgers/manual_glyph_review.csv")
manual_graphics = load_csv("05_ledgers/manual_graphic_review.csv")
manual_relations = load_csv("05_ledgers/manual_relation_review.csv")
manual_views = load_csv("05_ledgers/manual_view_review.csv")
check("manual_object_pixel_counts", all(row["original_match"] == "true" and row["overlay_complete"] == "true" and row["mask_only_pure"] == "true" and int(row["missing_stroke_px"]) == 0 and int(row["foreign_pixel_px"]) == 0 for row in manual_glyphs + manual_graphics), "122/122")
check("manual_relation_open_denominator", all(row["raw_1x_opened"] == "true" and row["nearest_8x_opened"] == "true" and int(row["canonical_illegal_overlap_px"]) == 0 for row in manual_relations), "11/11 raw 1x and nearest 8x")
check("manual_view_open_denominator", all(row["actually_opened"] == "true" and row["readability"] == "true" and row["clipping"] == "false" and row["harmony"] == "true" for row in manual_views), "8/8")

semantic_files = [
    "00_identity/semantic_context.md",
    "07_reports/after_overlap_adjudication.md",
    "07_reports/after_visual_acceptance.md",
    "07_reports/after_model_route.md",
    "07_reports/RESULT.txt",
]
check("hand_authored_reports_present", all((ROOT / rel).is_file() and (ROOT / rel).stat().st_size > 0 for rel in semantic_files), semantic_files)

failed = [row for row in checks if not row["pass"]]
result = {
    "handoff_id": "A-R107-P020-SA1-FRESH-ISOLATED-20260826",
    "canonical_uid": "FIG-P020-01",
    "role": "SA1",
    "model": "gpt-5.6-sol",
    "reasoning_effort": "xhigh",
    "R168": "Applied exactly; advisory categories cannot alone trigger FAIL/rebuild.",
    "N": 122,
    "C_N_2": 7381,
    "manual_denominators": manual_summary,
    "checks": checks,
    "check_count": len(checks),
    "failed_check_count": len(failed),
    "hard_fail_count": 0 if not failed else len(failed),
    "verdict": "PASS" if not failed else "FAIL",
    "route": "SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3" if not failed else "FAIL_TO_SA2",
}
QC_JSON.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

md = [
    "# Final crosscheck",
    "",
    f"- checks: {len(checks)}",
    f"- failed checks: {len(failed)}",
    f"- verdict: `{result['verdict']}`",
    f"- route: `{result['route']}`",
    "",
    "| Check | Result | Detail |",
    "|---|---:|---|",
]
for row in checks:
    detail = json.dumps(row["detail"], ensure_ascii=False, separators=(",", ":"))
    detail = detail.replace("|", "\\|")
    state = "PASS" if row["pass"] else "FAIL"
    md.append(f"| {row['name']} | {state} | {detail} |")
QC_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

print(json.dumps({"check_count": len(checks), "failed_check_count": len(failed), "verdict": result["verdict"], "route": result["route"]}, ensure_ascii=False))
raise SystemExit(0 if not failed else 1)
