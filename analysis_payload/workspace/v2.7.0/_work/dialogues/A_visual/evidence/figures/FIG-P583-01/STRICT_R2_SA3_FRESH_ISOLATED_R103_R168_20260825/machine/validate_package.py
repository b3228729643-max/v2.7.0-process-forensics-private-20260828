from __future__ import annotations

import csv
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]


def read_csv(relative: str) -> list[dict[str, str]]:
    with (ROOT / relative).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def main() -> None:
    errors: list[str] = []
    summary = json.loads((ROOT / "machine/machine_summary.json").read_text(encoding="utf-8"))
    measurements = read_csv("machine/after_pixel_measurements.csv")
    graphics = read_csv("machine/graphic_object_ledger.csv")
    paths = read_csv("machine/path_item_ledger.csv")
    id_map = read_csv("machine/id_safe_filename_map.csv")
    pairs = read_csv("machine/after_overlap_report.csv")
    glyph_contacts = read_csv("machine/glyph_contact_map.csv")
    graphic_contacts = read_csv("machine/graphic_contact_map.csv")
    human = read_csv("manual/manual_per_id_adjudication.csv")
    opened = read_csv("manual/opened_artifact_ledger.csv")
    critical = read_csv("manual/manual_critical_relationship_adjudication.csv")
    view_role = read_csv("manual/manual_view_role_adjudication.csv")
    result = json.loads((ROOT / "RESULT.json").read_text(encoding="utf-8"))

    glyph_ids = [row["element_id"] for row in measurements]
    graphic_ids = [row["element_id"] for row in graphics]
    all_ids = glyph_ids + graphic_ids
    expected_pairs = len(all_ids) * (len(all_ids) - 1) // 2

    require(len(glyph_ids) == 119, "glyph count is not 119", errors)
    require(len(graphic_ids) == 23, "graphic count is not 23", errors)
    require(len(all_ids) == 142, "object count is not 142", errors)
    require(len(set(all_ids)) == len(all_ids), "object IDs are not unique", errors)
    require(len(id_map) == len(all_ids), "ID map denominator mismatch", errors)
    require({row["element_id"] for row in id_map} == set(all_ids), "ID map coverage mismatch", errors)
    require(len({row["safe_filename"] for row in id_map}) == len(id_map), "safe filenames are not unique", errors)

    require(len(pairs) == expected_pairs == 10011, "unordered pair denominator mismatch", errors)
    require(len({row["pair_id"] for row in pairs}) == len(pairs), "pair IDs are not unique", errors)
    pair_keys = {tuple(sorted((row["object_a"], row["object_b"]))) for row in pairs}
    require(len(pair_keys) == len(pairs), "unordered object pair duplication detected", errors)
    require(all(row["object_a"] != row["object_b"] for row in pairs), "self pair detected", errors)
    unacceptable_pair_rows = [
        row for row in pairs
        if row["machine_rule_result"] in {"FAIL", "HARD_FAIL"}
    ]
    require(not unacceptable_pair_rows, "pair hard failure detected", errors)
    require(sum(int(row["critical_or_relationship"]) for row in pairs) == 328, "critical pair-row count mismatch", errors)

    require(len(paths) == 340, "path-item row count is not 340", errors)
    require(len({(row["pdf_drawing_index"], row["pdf_seqno"]) for row in paths}) == 10, "figure drawing paint-op count is not 10", errors)
    require(all(row["assigned_graphic_id"] in set(graphic_ids) for row in paths), "unassigned path item detected", errors)
    require(all(int(row["clip_pixel_count"]) == 0 for row in measurements), "glyph clip pixel detected", errors)
    require(all(row["r168_machine_hard_flag"] == "NONE" for row in measurements), "glyph R168 machine hard flag detected", errors)
    require(all(int(row["empty_mask_count"]) == 0 for row in graphics), "empty graphic mask detected", errors)

    require(len(glyph_contacts) == 119, "glyph contact coverage mismatch", errors)
    require(len(graphic_contacts) == 23, "graphic contact coverage mismatch", errors)
    require({row["element_id"] for row in glyph_contacts} == set(glyph_ids), "glyph contact ID mismatch", errors)
    require({row["element_id"] for row in graphic_contacts} == set(graphic_ids), "graphic contact ID mismatch", errors)

    require(len(human) == 142, "human per-ID row count mismatch", errors)
    require(len({row["element_id"] for row in human}) == 142, "human per-ID duplicate detected", errors)
    require({row["element_id"] for row in human} == set(all_ids), "human per-ID coverage mismatch", errors)
    human_exceptions = [
        row for row in human
        if row["original_match"] != "TRUE"
        or row["overlay_complete"] != "TRUE"
        or row["mask_only_pure"] != "TRUE"
        or int(row["missing_stroke_px"]) != 0
        or int(row["foreign_pixel_px"]) != 0
        or row["decision"] != "PASS"
        or not row["reviewer"].strip()
        or not row["note"].strip()
    ]
    require(not human_exceptions, "human per-ID exception detected", errors)
    require(len(opened) == 34, "opened-artifact row count mismatch", errors)
    require(all(row["opened"] == "TRUE" and row["decision"] == "PASS" for row in opened), "opened-artifact exception detected", errors)
    require(len(critical) == 8, "critical adjudication row count mismatch", errors)
    require(all(row["decision"] == "PASS" for row in critical), "critical adjudication exception detected", errors)
    require(len(view_role) == 11, "view-role row count mismatch", errors)
    require(all(row["observed"] == "TRUE" and row["decision"] == "PASS" for row in view_role), "view-role exception detected", errors)

    png_paths = set()
    png_paths.update(row["mask_path"] for row in measurements)
    png_paths.update(row["raw_mask_path"] for row in graphics)
    png_paths.update(row["final_mask_path"] for row in graphics)
    png_paths.update(f"glyphs/{row['sheet']}" for row in glyph_contacts)
    png_paths.update(f"overlays/{row['sheet']}" for row in graphic_contacts)
    png_paths.update(row["artifact"] for row in opened if row["artifact"].lower().endswith(".png"))
    png_open_errors = []
    for relative in sorted(png_paths):
        path = ROOT / relative
        try:
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                if image.width <= 0 or image.height <= 0:
                    raise ValueError("nonpositive image dimensions")
        except Exception as exc:  # evidence validator must report every failed ordinary image
            png_open_errors.append(f"{relative}: {exc}")
    require(not png_open_errors, "one or more referenced PNG files failed to open", errors)

    required_files = [
        "views/full_page_200dpi.png",
        "views/full_page_300dpi.png",
        "views/figure_crop_300dpi.png",
        "views/standalone_300dpi.png",
        "views/grayscale_300dpi.png",
        "overlays/after_text_measurement_overlay_300dpi.png",
        "pairs/all_unordered_pairs_matrix.png",
        "pairs/semantic_relationship_matrix.png",
        "after_visual_acceptance.md",
        "RESULT.json",
        "RESULT.txt",
    ]
    require(all((ROOT / relative).is_file() for relative in required_files), "required evidence file missing", errors)

    require(summary["total_object_count_n"] == result["object_count_n"] == 142, "summary/result N mismatch", errors)
    require(summary["all_unordered_pair_count_c"] == result["unordered_pair_count_c"] == 10011, "summary/result C mismatch", errors)
    require(summary["critical_or_relationship_pair_rows"] == result["critical_or_relationship_pair_rows"] == 328, "summary/result critical count mismatch", errors)
    require(summary["hard_pair_failure_count"] == result["machine_hard_failures"] == 0, "summary/result hard-failure mismatch", errors)
    require(summary["overlap_pixel_count_illegal"] == result["illegal_overlap_pixels"] == 0, "summary/result overlap mismatch", errors)
    require(summary["clip_pixel_count"] == result["clip_pixels"] == 0, "summary/result clip mismatch", errors)
    require(result["verdict"] == "PASS", "RESULT verdict is not PASS", errors)
    require(result["route"] == "SA3_PASS_READY_FOR_MAIN_A_LOCAL_PASS_ACCEPTANCE", "RESULT route mismatch", errors)
    require(result["main_acceptance_written"] is False, "RESULT improperly claims main acceptance write", errors)

    output = {
        "uid": "FIG-P583-01",
        "crosscheck_status": "PASS" if not errors else "FAIL",
        "object_rows_observed": len(all_ids),
        "object_unique_count": len(set(all_ids)),
        "glyph_rows_observed": len(glyph_ids),
        "graphic_rows_observed": len(graphic_ids),
        "unordered_pair_rows_observed": len(pairs),
        "unordered_pair_unique_count": len(pair_keys),
        "nonzero_intersection_pair_rows": sum(int(row["intersection_px"]) > 0 for row in pairs),
        "unacceptable_intersection_pair_rows": len(unacceptable_pair_rows),
        "critical_pair_rows_observed": sum(int(row["critical_or_relationship"]) for row in pairs),
        "path_item_rows_observed": len(paths),
        "drawing_paint_ops_observed": len({(row["pdf_drawing_index"], row["pdf_seqno"]) for row in paths}),
        "human_per_id_rows_observed": len(human),
        "human_per_id_unique_count": len({row["element_id"] for row in human}),
        "human_per_id_exception_count": len(human_exceptions),
        "opened_artifact_rows_observed": len(opened),
        "critical_adjudication_rows_observed": len(critical),
        "view_role_rows_observed": len(view_role),
        "referenced_png_count": len(png_paths),
        "referenced_png_open_error_count": len(png_open_errors),
        "package_error_count": len(errors),
        "package_errors": errors,
        "route_observed": result["route"],
    }
    (ROOT / "machine/final_crosscheck.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if errors:
        raise SystemExit("; ".join(errors))


if __name__ == "__main__":
    main()
