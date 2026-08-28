from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path

from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P582-01\STRICT_R8_SA3_FRESH_ISOLATED_R110_20260827")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C02\fig_v5_c02_running_mean.tex")
PDF_HASH = "B49C5CA920DDEF6C0CD004B2581EAF710F4D1E1115BB459A324A84594B3831F3"
SOURCE_HASH = "989E12DFD1B7A7F58A7953F36A8E8F24427A56154EED33325262045C17583A57"
HANDOFF_ID = "A-R110-P582-SA3-FRESH-ISOLATED-20260827"


def sha256(path: Path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest().upper()


def read_csv(name):
    with (ROOT / name).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    require(sha256(PDF) == PDF_HASH and PDF.stat().st_size == 4_967_063, "official PDF identity drift")
    require(sha256(SOURCE) == SOURCE_HASH, "source identity drift")
    require(not (ROOT / "WRITE_STOPPED").exists(), "audit must run before final WRITE_STOPPED")

    summary = json.loads((ROOT / "machine_summary.json").read_text(encoding="utf-8"))
    objects = json.loads((ROOT / "object_manifest.json").read_text(encoding="utf-8"))
    pairs = json.loads((ROOT / "unordered_pairs.json").read_text(encoding="utf-8"))
    critical = json.loads((ROOT / "critical_relations.json").read_text(encoding="utf-8"))
    require(summary["machine_hard_status"] == "PASS", "machine hard status is not PASS")
    require(summary["object_count"] == 156 and summary["glyph_count"] == 139 and summary["drawing_path_count"] == 17, "object denominator mismatch")
    require(summary["math_rule_count"] == 0, "math rule reconciliation mismatch")
    require(summary["unordered_pair_count"] == summary["expected_unordered_pair_count"] == 12090, "pair denominator mismatch")
    require(summary["illegal_overlap_pixel_count"] == 0 and summary["clip_pixel_count"] == 0, "overlap or clip hard gate failed")
    require(summary["empty_mask_count"] == summary["pair_hard_fail_count"] == summary["pixel_hard_fail_count"] == 0, "machine failure count nonzero")

    ids = [o["id"] for o in objects]
    require(len(ids) == len(set(ids)) == 156, "object IDs not unique")
    require(ids[:139] == [f"G{i:04d}" for i in range(1, 140)], "glyph ID denominator mismatch")
    require(ids[139:] == [f"D{i:04d}" for i in range(1, 18)], "drawing ID denominator mismatch")
    expected_pairs = {tuple(sorted(x)) for x in itertools.combinations(ids, 2)}
    actual_pairs = {tuple(sorted((p["a_id"], p["b_id"]))) for p in pairs}
    require(expected_pairs == actual_pairs and len(actual_pairs) == 12090, "unordered pair set not exact")
    require(len({p["pair_id"] for p in pairs}) == 12090, "pair IDs not unique")
    require(all(p["machine_status"] == "PASS" for p in pairs), "pair machine status contains FAIL")

    masks = sorted((ROOT / "objects").glob("*.png"))
    require(len(masks) == 156, "ordinary mask file count mismatch")
    require(all(":" not in p.name and p.stat().st_size > 0 for p in masks), "unsafe or empty mask path")
    for obj in objects:
        path = ROOT / obj["mask_path"]
        require(path.is_file(), f"missing mask {obj['id']}")
        with Image.open(path) as image:
            require(image.width > 0 and image.height > 0, f"bad mask dimensions {obj['id']}")
            require([image.width, image.height] == [obj["ink_width_px"], obj["ink_height_px"]], f"mask dimension metadata mismatch {obj['id']}")

    required_views = {
        "full_page_200dpi.png": (1654, 2339),
        "full_page_300dpi.png": (2481, 3508),
        "figure_crop_300dpi.png": tuple(summary["figure_crop_dimensions"]),
        "standalone_300dpi.png": tuple(summary["standalone_crop_dimensions"]),
        "grayscale_300dpi.png": tuple(summary["figure_crop_dimensions"]),
        "after_text_measurement_overlay_300dpi.png": tuple(summary["figure_crop_dimensions"]),
    }
    for name, dims in required_views.items():
        with Image.open(ROOT / name) as image:
            require(image.size == dims, f"view dimensions mismatch {name}: {image.size} vs {dims}")

    glyph_sheets = sorted((ROOT / "contact_sheets").glob("glyph_contact_*.png"))
    drawing_sheets = sorted((ROOT / "contact_sheets").glob("drawing_contact_*.png"))
    relation_sheets = sorted((ROOT / "relations").glob("critical_relations_*.png"))
    require((len(glyph_sheets), len(drawing_sheets), len(relation_sheets)) == (12, 2, 15), "sheet denominator mismatch")
    for path in glyph_sheets + drawing_sheets + relation_sheets:
        with Image.open(path) as image:
            image.verify()

    glyph_manual = read_csv("manual_glyph_review.csv")
    drawing_manual = read_csv("manual_drawing_review.csv")
    relation_manual = read_csv("manual_relation_review.csv")
    view_manual = read_csv("manual_view_review.csv")
    role_manual = read_csv("manual_role_visual_review.csv")
    require(len(glyph_manual) == 139 and {r["element_id"] for r in glyph_manual} == set(ids[:139]), "manual glyph ledger mismatch")
    require(len(drawing_manual) == 17 and {r["element_id"] for r in drawing_manual} == set(ids[139:]), "manual drawing ledger mismatch")
    require(len(relation_manual) == 89 and {r["pair_id"] for r in relation_manual} == {p["pair_id"] for p in critical}, "manual relation ledger mismatch")
    require(len(view_manual) == 5 and len(role_manual) == 18, "manual view/role ledger mismatch")
    for row in glyph_manual:
        require(row["reviewer"] == "SA3" and row["handoff_id"] == HANDOFF_ID, f"manual glyph reviewer identity mismatch {row['element_id']}")
        require(row["original_match"] == row["overlay_complete"] == row["mask_only_pure"] == "true", f"manual glyph boolean failure {row['element_id']}")
        require(row["missing_stroke_px"] == row["foreign_pixel_px"] == "0" and row["decision"] == "PASS" and row["note"].strip(), f"manual glyph failure {row['element_id']}")
        require((ROOT / row["sheet_path"]).is_file(), f"manual glyph sheet missing {row['element_id']}")
    for row in drawing_manual:
        require(row["reviewer"] == "SA3" and row["handoff_id"] == HANDOFF_ID, f"manual drawing reviewer identity mismatch {row['element_id']}")
        require(row["original_match"] == row["overlay_complete"] == row["mask_only_pure"] == "true", f"manual drawing boolean failure {row['element_id']}")
        require(row["empty_mask"] == "false" and row["decision"] == "PASS" and row["note"].strip(), f"manual drawing failure {row['element_id']}")
        require((ROOT / row["sheet_path"]).is_file(), f"manual drawing sheet missing {row['element_id']}")
    for row in relation_manual:
        require(row["reviewer"] == "SA3" and row["handoff_id"] == HANDOFF_ID, f"manual relation reviewer identity mismatch {row['pair_id']}")
        require(all(row[name] == "true" for name in ("raw_a_match", "raw_b_match", "intersection_verified", "one_x_opened", "eight_x_opened")), f"manual relation boolean failure {row['pair_id']}")
        require(row["decision"] == "PASS" and row["note"].strip(), f"manual relation failure {row['pair_id']}")
        require((ROOT / row["sheet_path"]).is_file(), f"manual relation sheet missing {row['pair_id']}")
    for row in view_manual:
        require(all(row[name] == "true" for name in ("opened_native_or_original", "legible", "balanced", "no_tofu", "no_clipping", "no_illegal_overlap")), f"manual view failure {row['view_id']}")
        require(row["decision"] == "PASS" and row["note"].strip() and (ROOT / row["path"]).is_file(), f"manual view incomplete {row['view_id']}")
    for row in role_manual:
        require(row["reviewer"] == "SA3" and row["crowding"] == row["protrusion"] == "false", f"manual role geometry failure {row['role']} {row['script']}")
        require(row["grayscale"] == row["page_fusion"] == "true" and row["decision"] == "PASS" and row["note"].strip(), f"manual role failure {row['role']} {row['script']}")

    font_rows = read_csv("after_font_audit.csv")
    pixel_rows = read_csv("after_pixel_measurements.csv")
    overlap_rows = read_csv("after_overlap_report.csv")
    edge_rows = read_csv("edge_clearance.csv")
    require(len(font_rows) == 139 and all(r["source_font_gate"] == "PASS" for r in font_rows), "source font audit not closed")
    require(len(pixel_rows) == 156 and not any(r["empty_mask"] == "True" or r["pixel_gate_status"] == "FAIL" for r in pixel_rows), "pixel ledger hard failure")
    advisory_ids = {r["id"] for r in pixel_rows if r["pixel_gate_status"].startswith("ADVISORY")}
    require(advisory_ids == {"G0032", "G0082", "G0114", "G0124"}, f"unexpected advisory set {sorted(advisory_ids)}")
    require(len(overlap_rows) == 12090 and all(r["machine_status"] == "PASS" for r in overlap_rows), "CSV pair ledger not closed")
    require(len(edge_rows) == 156 and min(int(r["edge_clearance_px"]) for r in edge_rows) >= 24, "edge clearance mismatch")

    result = (ROOT / "RESULT.txt").read_text(encoding="utf-8")
    acceptance = (ROOT / "after_visual_acceptance.md").read_text(encoding="utf-8")
    semantics = (ROOT / "semantic_audit.md").read_text(encoding="utf-8")
    source_audit = (ROOT / "source_font_audit.md").read_text(encoding="utf-8")
    for token in ("PASS", "OBJECTS=156", "UNORDERED_PAIRS=12090", "ILLEGAL_OVERLAP_PIXEL_COUNT=0", "CLIP_PIXEL_COUNT=0"):
        require(token in result, f"RESULT missing {token}")
    for token in ("SA3 verdict: `PASS`", "FONT_VISUAL_HARMONY_PASS=true", "MATH_TEXT_SEMANTICS_PASS=true"):
        require(token in acceptance, f"acceptance missing {token}")
    require("MATH_TEXT_SEMANTICS_PASS=true" in semantics and "SOURCE_FONT_GATE=PASS" in source_audit, "manual summary mismatch")

    required_files = [
        "full_page_200dpi.png", "full_page_300dpi.png", "figure_crop_300dpi.png", "standalone_300dpi.png", "grayscale_300dpi.png",
        "after_font_audit.csv", "after_pixel_measurements.csv", "after_overlap_report.csv", "after_text_measurement_overlay_300dpi.png",
        "after_visual_acceptance.md", "object_manifest.json", "unordered_pairs.json", "critical_relations.json", "manual_glyph_review.csv",
        "manual_drawing_review.csv", "manual_relation_review.csv", "manual_view_review.csv", "manual_role_visual_review.csv", "RESULT.txt",
    ]
    require(all((ROOT / name).is_file() and (ROOT / name).stat().st_size > 0 for name in required_files), "required artifact missing or empty")

    output = {
        "uid": "FIG-P582-01",
        "round": "R110",
        "handoff_id": HANDOFF_ID,
        "object_count": 156,
        "glyph_count": 139,
        "drawing_path_count": 17,
        "math_rule_count": 0,
        "unordered_pair_count": 12090,
        "critical_relation_count": 89,
        "manual_glyph_rows": 139,
        "manual_drawing_rows": 17,
        "manual_relation_rows": 89,
        "manual_view_rows": 5,
        "manual_role_rows": 18,
        "ordinary_mask_png_count": 156,
        "glyph_sheet_count": 12,
        "drawing_sheet_count": 2,
        "relation_sheet_count": 15,
        "illegal_overlap_pixel_count": 0,
        "clip_pixel_count": 0,
        "advisory_ids": sorted(advisory_ids),
        "machine_crosscheck_status": "PASS",
    }
    (ROOT / "final_crosscheck.json").write_text(json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
