from __future__ import annotations

import csv
import itertools
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent


def rows(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def add_error(errors: list[str], condition: bool, message: str) -> None:
    if condition:
        errors.append(message)


def main() -> None:
    errors: list[str] = []
    inventory = json.loads((ROOT / "candidate_inventory.json").read_text(encoding="utf-8"))
    objects = rows("object_manifest.csv")
    pairs = rows("all_unordered_pairs.csv")
    glyphs = rows("after_pixel_measurements.csv")
    glyph_map = rows("glyph_contact_map.csv")
    glyph_manual = rows("manual_glyph_review.csv")
    drawings = rows("drawing_path_ledger.csv")
    rule_map = rows("math_rule_contact_map.csv")
    rule_manual = rows("manual_math_rule_review.csv")
    relations = rows("manual_relationship_review.csv")
    endpoints = rows("manual_endpoint_clip_review.csv")
    views = rows("visual_view_ledger.csv")
    font_audit = rows("after_font_audit.csv")
    role_ledger = rows("panel_role_script_ledger.csv")
    overlap_report = rows("after_overlap_report.csv")
    semantic = json.loads((ROOT / "semantic_recomputation.json").read_text(encoding="utf-8"))
    result_json = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))
    result_txt = (ROOT / "RESULT.txt").read_text(encoding="utf-8")
    report_md = (ROOT / "SA3_REPORT.md").read_text(encoding="utf-8")
    acceptance_md = (ROOT / "after_visual_acceptance.md").read_text(encoding="utf-8")

    object_ids = [r["object_id"] for r in objects]
    pair_ids = [r["pair_id"] for r in pairs]
    add_error(errors, len(objects) != 128, f"object count {len(objects)} != 128")
    add_error(errors, len(set(object_ids)) != len(object_ids), "duplicate object ID")
    add_error(errors, len(pairs) != 8128, f"pair count {len(pairs)} != 8128")
    add_error(errors, len(set(pair_ids)) != len(pair_ids), "duplicate pair ID")

    actual_pairs = {tuple(sorted((r["object_a"], r["object_b"]))) for r in pairs}
    expected_pairs = {tuple(sorted(p)) for p in itertools.combinations(object_ids, 2)}
    add_error(errors, actual_pairs != expected_pairs, "unordered pair set is incomplete or contains extras")

    glyph_ids = {r["object_id"] for r in glyphs}
    add_error(errors, len(glyphs) != 68 or len(glyph_ids) != 68, "glyph denominator mismatch")
    add_error(errors, {r["object_id"] for r in glyph_map} != glyph_ids, "glyph contact map mismatch")
    add_error(errors, {r["object_id"] for r in glyph_manual} != glyph_ids, "manual glyph ledger mismatch")
    add_error(errors, any(r["manual_decision"] != "PASS" for r in glyph_manual), "manual glyph ledger contains non-PASS")
    add_error(errors, any(r["original_match"] != "true" for r in glyph_manual), "glyph original-match gap")
    add_error(errors, any(r["overlay_complete"] != "true" for r in glyph_manual), "glyph overlay-complete gap")
    add_error(errors, any(r["mask_only_pure"] != "true" for r in glyph_manual), "glyph mask-purity gap")
    add_error(errors, any(int(r["missing_stroke_px"]) != 0 for r in glyph_manual), "glyph missing strokes")
    add_error(errors, any(int(r["foreign_pixel_px"]) != 0 for r in glyph_manual), "glyph foreign pixels")
    add_error(errors, any(int(r["ink_area_px"]) <= 0 for r in glyphs), "empty glyph mask")

    rule_ids = {r["object_id"] for r in drawings if r["object_type"] == "MATH_RULE"}
    add_error(errors, len(rule_ids) != 6, "math rule denominator mismatch")
    add_error(errors, {r["object_id"] for r in rule_map} != rule_ids, "math rule contact map mismatch")
    add_error(errors, {r["object_id"] for r in rule_manual} != rule_ids, "manual math rule ledger mismatch")
    add_error(errors, any(r["manual_decision"] != "PASS" for r in rule_manual), "manual math rule ledger contains non-PASS")
    add_error(errors, any(int(r["mask_pixel_count"]) <= 0 for r in drawings), "empty drawing mask")

    safe_paths = [r["safe_filename"] for r in objects]
    add_error(errors, len(set(safe_paths)) != len(safe_paths), "duplicate safe filename")
    add_error(errors, any(":" in Path(p).name for p in safe_paths), "unsafe colon filename")
    png_open_count = 0
    for rel in safe_paths:
        path = ROOT / rel
        add_error(errors, not path.is_file(), f"missing evidence file {rel}")
        if path.is_file():
            with Image.open(path) as image:
                image.verify()
            png_open_count += 1

    intersecting = [r for r in pairs if r["raw_intersection_px"] and int(r["raw_intersection_px"]) > 0]
    text_intersections = [r for r in intersecting if r["type_a"] == "TEXT_GLYPH" or r["type_b"] == "TEXT_GLYPH"]
    add_error(errors, len(intersecting) != 71, f"intersection inventory changed: {len(intersecting)}")
    add_error(errors, len(text_intersections) != 0, "text participates in an intersection")
    add_error(errors, any(r["manual_decision"] not in {"PASS", "NA"} for r in relations), "relationship ledger has unresolved row")
    add_error(errors, any(int(r["illegal_overlap_px"]) != 0 for r in relations), "illegal overlap reported")
    add_error(errors, any(r["manual_decision"] != "PASS" for r in endpoints), "endpoint/clip ledger contains non-PASS")
    add_error(errors, any(int(r["clip_pixel_count"]) != 0 for r in endpoints), "clip pixels reported")
    add_error(errors, any(r["manual_decision"] != "PASS" for r in views), "visual view ledger contains non-PASS")
    add_error(errors, any(r["manual_decision"] != "PASS" for r in font_audit), "font audit contains non-PASS")
    add_error(errors, any(r["manual_decision"] != "PASS" for r in role_ledger), "panel/role/script ledger contains non-PASS")
    add_error(errors, any(r["manual_decision"] not in {"PASS", "NA"} for r in overlap_report), "overlap report has unresolved row")

    add_error(errors, semantic["trace_point_count"] != 20, "trace point count mismatch")
    add_error(errors, semantic["retained_point_count"] != 15, "retained point count mismatch")
    add_error(errors, semantic["running_mean_point_count"] != 15, "running-mean point count mismatch")
    add_error(errors, semantic["final_recomputed_mean"] != 2.0, "final recomputed mean mismatch")
    add_error(errors, semantic["max_rounded_difference"] > 0.00005, "running means exceed 4-decimal rounding tolerance")
    add_error(errors, not all(semantic["source_semantic_strings_present"].values()), "source semantic string missing")

    required_views = {
        "full_page_200dpi.png",
        "figure_crop_300dpi.png",
        "standalone_300dpi.png",
        "grayscale_300dpi.png",
        "after_text_measurement_overlay_300dpi.png",
        "counterevidence_native1x_sheet.png",
        "counterevidence_8x_nearest_sheet.png",
        "math_rule_contact_sheet.png",
    }
    for name in required_views:
        path = ROOT / name
        add_error(errors, not path.is_file(), f"missing required view {name}")
        if path.is_file():
            with Image.open(path) as image:
                image.verify()

    add_error(errors, inventory["total_object_denominator"] != len(objects), "inventory object total mismatch")
    add_error(errors, inventory["unordered_pair_denominator"] != len(pairs), "inventory pair total mismatch")
    add_error(errors, inventory["glyph_contact_row_count"] != len(glyph_map), "inventory glyph contact total mismatch")
    add_error(errors, inventory["math_rule_contact_row_count"] != len(rule_map), "inventory rule contact total mismatch")

    expected_decision = "SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE"
    add_error(errors, result_json.get("decision") != expected_decision, "RESULT.json decision mismatch")
    add_error(errors, result_json.get("central_a_local_pass_claimed") is not False, "RESULT.json central claim must be false")
    add_error(errors, result_json.get("object_denominator") != len(objects), "RESULT.json object total mismatch")
    add_error(errors, result_json.get("unordered_pair_denominator") != len(pairs), "RESULT.json pair total mismatch")
    add_error(errors, result_json.get("overlap_pixel_count") != 0, "RESULT.json overlap mismatch")
    add_error(errors, result_json.get("clip_pixel_count") != 0, "RESULT.json clip mismatch")
    for required in (
        f"DECISION={expected_decision}",
        "CENTRAL_A_LOCAL_PASS_CLAIMED=false",
        "OVERLAP_PIXEL_COUNT=0",
        "CLIP_PIXEL_COUNT=0",
        "OBJECT_DENOMINATOR=128",
        "UNORDERED_PAIR_DENOMINATOR=8128",
    ):
        add_error(errors, required not in result_txt, f"RESULT.txt missing {required}")
    add_error(errors, expected_decision not in report_md, "SA3_REPORT.md decision mismatch")
    add_error(errors, "All `128 choose 2 = 8,128`" not in report_md, "SA3_REPORT.md denominator mismatch")
    add_error(errors, "FONT_VISUAL_HARMONY_PASS=true" not in acceptance_md, "visual acceptance harmony field missing")
    add_error(errors, expected_decision not in acceptance_md, "visual acceptance decision mismatch")

    payload = {
        "integrity_error_count": len(errors),
        "integrity_errors": errors,
        "object_count": len(objects),
        "unique_object_id_count": len(set(object_ids)),
        "unordered_pair_count": len(pairs),
        "expected_unordered_pair_count": len(expected_pairs),
        "glyph_count": len(glyphs),
        "glyph_manual_row_count": len(glyph_manual),
        "glyph_mask_files_opened": sum(1 for p in safe_paths if p.startswith("glyph_masks/")),
        "drawing_and_rule_count": len(drawings),
        "math_rule_count": len(rule_ids),
        "math_rule_manual_row_count": len(rule_manual),
        "ordinary_mask_png_open_count": png_open_count,
        "intersecting_pair_count": len(intersecting),
        "text_intersection_count": len(text_intersections),
        "illegal_overlap_count_from_manual_ledger": sum(int(r["illegal_overlap_px"]) for r in relations),
        "clip_pixel_count_from_manual_ledger": sum(int(r["clip_pixel_count"]) for r in endpoints),
        "manual_relationship_row_count": len(relations),
        "manual_endpoint_row_count": len(endpoints),
        "manual_visual_view_row_count": len(views),
        "manual_font_audit_row_count": len(font_audit),
        "manual_panel_role_script_row_count": len(role_ledger),
        "manual_overlap_report_row_count": len(overlap_report),
        "result_artifact_count_checked": 4,
        "semantic_final_mean": semantic["final_recomputed_mean"],
        "semantic_max_rounded_difference": semantic["max_rounded_difference"],
    }
    (ROOT / "machine_crosscheck.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
