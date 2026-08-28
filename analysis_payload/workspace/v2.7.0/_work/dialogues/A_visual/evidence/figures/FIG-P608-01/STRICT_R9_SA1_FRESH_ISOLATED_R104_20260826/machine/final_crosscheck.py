from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P608-01\STRICT_R9_SA1_FRESH_ISOLATED_R104_20260826")


def rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def all_true(row: dict[str, str], fields: list[str]) -> bool:
    return all(row[field].upper() == "TRUE" for field in fields)


def main() -> None:
    summary = json.loads((ROOT / "machine" / "machine_summary.json").read_text(encoding="utf-8"))
    glyphs = rows(ROOT / "after_pixel_measurements.csv")
    fonts = rows(ROOT / "after_font_audit.csv")
    pairs = rows(ROOT / "after_overlap_report.csv")
    objects = json.loads((ROOT / "machine" / "all_objects.json").read_text(encoding="utf-8"))
    glyph_manual = rows(ROOT / "manual" / "glyph_manual_reviewer_ledger.csv")
    rule_manual = rows(ROOT / "manual" / "math_rule_manual_reviewer_ledger.csv")
    roi_index = rows(ROOT / "machine" / "critical_relation_roi_index.csv")
    relation_manual = rows(ROOT / "manual" / "relation_roi_manual_reviewer_ledger.csv")
    view_manual = rows(ROOT / "manual" / "view_manual_reviewer_ledger.csv")
    role_manual = rows(ROOT / "manual" / "panel_role_script_manual_reviewer_ledger.csv")
    drawing_map = rows(ROOT / "machine" / "drawing_to_object_map.csv")
    safe_map = rows(ROOT / "machine" / "id_safe_filename_map.csv")

    require(summary["machine_crosscheck"] == "PASS", "upstream machine summary failed")
    require(len(objects) == 89 and len({x["element_id"] for x in objects}) == 89, "object denominator/uniqueness failed")
    require(len(glyphs) == 68 and all(x["threshold_status"] == "PASS" for x in glyphs), "glyph machine ledger failed")
    require(len(pairs) == 3916 and len({x["pair_id"] for x in pairs}) == 3916, "pair denominator/uniqueness failed")
    require(all(x["machine_threshold"] == "PASS" for x in pairs), "pair machine threshold failed")
    require(sum(int(x["overlap_px"]) for x in pairs if x["overlap_whitelisted"] == "NO") == 0, "non-whitelisted overlap found")
    require(len(drawing_map) == 58 and len({x["drawing_index"] for x in drawing_map}) == 58, "drawing mapping failed")
    require(len(safe_map) == 89 and len({x["safe_filename"] for x in safe_map}) == 89, "safe filename map failed")

    mask_files = [p for p in (ROOT / "masks").iterdir() if p.is_file() and p.suffix.lower() == ".png"]
    require(len(mask_files) == 89, f"mask ordinary file count failed: {len(mask_files)}")
    require(all((ROOT / x["mask_path"]).is_file() for x in safe_map), "referenced mask missing")

    glyph_by_id = {x["element_id"]: x for x in glyphs}
    require(len(glyph_manual) == 68 and len({x["element_id"] for x in glyph_manual}) == 68, "manual glyph denominator failed")
    require(set(glyph_by_id) == {x["element_id"] for x in glyph_manual}, "manual glyph ID coverage failed")
    require(all(glyph_by_id[x["element_id"]]["char"] == x["char"] for x in glyph_manual), "manual glyph character mapping failed")
    glyph_bools = ["original_match", "overlay_complete", "mask_only_pure"]
    require(all(all_true(x, glyph_bools) and x["missing_stroke_px"] == "0" and x["foreign_pixel_px"] == "0" and x["decision"] == "PASS" and x["note"].strip() for x in glyph_manual), "manual glyph review failed")

    rule_ids = {x["element_id"] for x in objects if x["kind"] == "MATH_RULE"}
    require(len(rule_ids) == 6 and {x["element_id"] for x in rule_manual} == rule_ids, "manual math rule coverage failed")
    rule_bools = ["original_match", "overlay_complete", "mask_only_pure", "nonempty", "semantic_parent_match"]
    require(all(all_true(x, rule_bools) and x["missing_stroke_px"] == "0" and x["foreign_pixel_px"] == "0" and x["decision"] == "PASS" and x["note"].strip() for x in rule_manual), "manual math rule review failed")

    roi_ids = {x["pair_id"] for x in roi_index}
    require(len(roi_index) == 23 and {x["pair_id"] for x in relation_manual} == roi_ids, "manual relation ROI coverage failed")
    roi_bools = ["raw_1x_opened", "mask_A_1x_opened", "mask_B_1x_opened", "intersection_1x_opened", "overlay_1x_opened", "overlay_8x_opened", "object_A_match", "object_B_match", "overlap_verified", "clearance_verified"]
    require(all(all_true(x, roi_bools) and x["decision"] == "PASS" and x["note"].strip() for x in relation_manual), "manual relation review failed")
    for row in roi_index:
        rel = ROOT / row["directory"]
        for name in ("raw_1x.png", "mask_A_1x.png", "mask_B_1x.png", "intersection_1x.png", "overlay_1x.png", "overlay_8x_nearest.png"):
            require((rel / name).is_file(), f"missing ROI file {row['pair_id']}/{name}")

    view_bools = ["content_complete", "glyphs_readable", "no_visible_tofu_or_wrong_codepoint", "no_visible_crop", "no_illegal_overlap", "font_visual_harmony_pass"]
    require(len(view_manual) == 5 and all(all_true(x, view_bools) and x["decision"] == "PASS" and x["note"].strip() for x in view_manual), "manual view review failed")
    require(len(role_manual) == 23 and all(x["D_status"] == "PASS" and x["E_status"] == "PASS" and x["crowding_status"] == "UNCROWDED" and x["font_visual_harmony_pass"] == "TRUE" and x["decision"] == "PASS" and x["note"].strip() for x in role_manual), "manual panel/role/script review failed")

    require(all(x["machine_threshold"] not in {"FAIL", "UNKNOWN", "PENDING", ""} for x in fonts), "source font audit failed")
    require(json.loads((ROOT / "machine" / "data_semantics.json").read_text(encoding="utf-8"))["all_machine_thresholds"] == "PASS", "data semantics failed")

    required_pairs = [x for x in pairs if x["required_clearance_px"] != "N/A"]
    relation_mins = {}
    for relation in sorted({x["relation_class"] for x in required_pairs}):
        group = [float(x["clearance_px"]) for x in required_pairs if x["relation_class"] == relation]
        relation_mins[relation] = min(group)
    require(relation_mins["INDEPENDENT_TEXT_TEXT"] >= 4, "text-text clearance failed")
    require(relation_mins["CROSS_PANEL_TEXT"] >= 8, "cross-panel clearance failed")
    require(relation_mins["TEXT_OR_FORMULA_TO_GRAPHIC"] >= 3, "text-graphic clearance failed")

    sx0, sy0, sx1, sy1 = summary["standalone_crop_px"]
    text_objects = [x for x in objects if x["kind"] == "TEXT_GLYPH"]
    edge_clearances = []
    for obj in text_objects:
        x0, y0, x1, y1 = obj["tight_bbox_px"]
        edge_clearances.append(min(x0 - sx0, sx1 - x1, y0 - sy0, sy1 - y1))
    min_text_edge = min(edge_clearances)
    require(min_text_edge >= 6, "text to standalone edge clearance failed")

    outputs = {
        "crosscheck_status": "PASS",
        "object_denominator": 89,
        "text_glyph_denominator": 68,
        "graphic_object_denominator": 21,
        "drawing_record_denominator": 58,
        "all_unordered_pair_denominator": 3916,
        "ordinary_mask_png_count": 89,
        "glyph_manual_rows": 68,
        "math_rule_manual_rows": 6,
        "relation_roi_manual_rows": 23,
        "view_manual_rows": 5,
        "panel_role_script_manual_rows": 23,
        "manual_decision_counts": {
            "glyph": dict(Counter(x["decision"] for x in glyph_manual)),
            "math_rule": dict(Counter(x["decision"] for x in rule_manual)),
            "relation_roi": dict(Counter(x["decision"] for x in relation_manual)),
            "view": dict(Counter(x["decision"] for x in view_manual)),
            "panel_role_script": dict(Counter(x["decision"] for x in role_manual)),
        },
        "nonwhitelisted_overlap_pixel_count": 0,
        "clip_pixel_count": summary["clip_pixel_count"],
        "minimum_clearance_px_by_relation": relation_mins,
        "minimum_text_to_standalone_edge_px": min_text_edge,
        "data_semantics": "PASS",
        "font_source_hard_gate": "PASS",
        "manual_visual_ledgers": "PASS",
        "advisory_only": [
            "R168: PDF-reported sizes 9.564/10.760 versus source 9.6/10.8 are subpixel transform metadata differences only",
            "R168: mixed glyph-shape height ratios for low-profile punctuation and natural scripts were not treated as same-contour failures; same-codepoint calibration is exact",
        ],
    }
    (ROOT / "machine" / "final_crosscheck.json").write_text(json.dumps(outputs, ensure_ascii=False, indent=2), encoding="utf-8")
    (ROOT / "machine" / "final_crosscheck.txt").write_text("CROSSCHECK_STATUS=PASS\nOBJECTS=89\nUNORDERED_PAIRS=3916\nGLYPH_MANUAL=68\nMATH_RULE_MANUAL=6\nRELATION_ROI_MANUAL=23\nVIEWS_MANUAL=5\nPANEL_ROLE_SCRIPT_MANUAL=23\n", encoding="ascii")
    print(json.dumps(outputs, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
