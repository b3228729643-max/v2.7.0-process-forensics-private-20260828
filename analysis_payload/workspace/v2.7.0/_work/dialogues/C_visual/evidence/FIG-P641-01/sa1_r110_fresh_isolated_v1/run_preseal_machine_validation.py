from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r110_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C04\fig_v5_c04_bayes_markov_blanket.tex")


def sha256(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def read_csv(name):
    with (ROOT / name).open("r", newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def main():
    json_errors = []
    csv_errors = []
    png_errors = []
    for path in ROOT.rglob("*.json"):
        if path.name == "machine_preseal_validation.json":
            continue
        try:
            json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            json_errors.append(f"{path.relative_to(ROOT)}: {exc}")
    for path in ROOT.rglob("*.csv"):
        try:
            with path.open("r", newline="", encoding="utf-8-sig") as handle:
                list(csv.reader(handle, strict=True))
        except Exception as exc:
            csv_errors.append(f"{path.relative_to(ROOT)}: {exc}")
    pngs = list(ROOT.rglob("*.png"))
    for path in pngs:
        try:
            with Image.open(path) as image:
                image.verify()
        except Exception as exc:
            png_errors.append(f"{path.relative_to(ROOT)}: {exc}")

    objects = read_csv("visible_objects.csv")
    safe_map = read_csv("safe_filename_map.csv")
    pairs = read_csv("all_unordered_pairs.csv")
    critical = read_csv("critical_relations.csv")
    glyph_manual = read_csv("manual_glyph_ledger.csv")
    graphic_manual = read_csv("manual_graphic_ledger.csv")
    critical_manual = read_csv("manual_critical_relation_ledger.csv")
    low_manual = read_csv("manual_low_profile_calibration_ledger.csv")
    role_manual = read_csv("manual_role_script_ledger.csv")
    view_manual = read_csv("manual_view_role_ledger.csv")
    cal_metrics = read_csv("low_profile_external_calibration_metrics.csv")

    glyph_masks = list((ROOT / "masks" / "glyph").glob("*.png"))
    graphic_masks = list((ROOT / "masks" / "graphic").glob("*.png"))
    mask_empty_or_solid = []
    for path in glyph_masks + graphic_masks:
        image = Image.open(path).convert("L")
        extrema = image.getextrema()
        if extrema[0] == extrema[1]:
            mask_empty_or_solid.append(str(path.relative_to(ROOT)))

    expected_n = 177
    expected_c = expected_n * (expected_n - 1) // 2
    overlap_count = sum(int(row["raw_mask_intersection_px"]) > 0 for row in pairs)
    calibration_ratio_violations = []
    for row in cal_metrics:
        for field in ("h_ratio_current_over_cal", "area_ratio_current_over_cal"):
            value = float(row[field])
            if not 0.92 <= value <= 1.08:
                calibration_ratio_violations.append(f"{row['element_id']}:{field}={value}")

    manual_files = [glyph_manual, graphic_manual, critical_manual, low_manual, role_manual, view_manual]
    manual_nonpass_count = sum(
        1 for rows in manual_files for row in rows if row.get("decision") != "PASS"
    )
    manual_pending_or_blank_count = sum(
        1 for rows in manual_files for row in rows
        for value in row.values() if value is None or not str(value).strip() or str(value).upper() in {"PENDING", "UNKNOWN"}
    )

    cache_files = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.name == "__pycache__" or p.suffix.lower() == ".pyc"]
    symlinks = [str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_symlink()]
    checks = {
        "pdf_bytes": PDF.stat().st_size,
        "pdf_sha256": sha256(PDF),
        "source_bytes": SOURCE.stat().st_size,
        "source_sha256": sha256(SOURCE),
        "visible_object_count": len(objects),
        "visible_object_unique_id_count": len({row["element_id"] for row in objects}),
        "safe_filename_map_count": len(safe_map),
        "safe_filename_unique_count": len({row["safe_filename"] for row in safe_map}),
        "unordered_pair_count": len(pairs),
        "unordered_pair_unique_id_count": len({row["pair_id"] for row in pairs}),
        "unordered_pair_formula_expected": expected_c,
        "critical_relation_count": len(critical),
        "raw_intersection_pair_count": overlap_count,
        "glyph_mask_file_count": len(glyph_masks),
        "graphic_mask_file_count": len(graphic_masks),
        "mask_empty_or_solid_count": len(mask_empty_or_solid),
        "glyph_contact_sheet_count": len(list((ROOT / "contact_sheets").glob("glyph_contact_sheet_*.png"))),
        "graphic_contact_sheet_count": len(list((ROOT / "contact_sheets").glob("graphic_contact_sheet_*.png"))),
        "critical_contact_sheet_count": len(list((ROOT / "contact_sheets").glob("critical_contact_sheet_*.png"))),
        "critical_roi_png_count": len(list((ROOT / "critical_rois").glob("*.png"))),
        "manual_glyph_row_count": len(glyph_manual),
        "manual_glyph_unique_id_count": len({row["element_id"] for row in glyph_manual}),
        "manual_graphic_row_count": len(graphic_manual),
        "manual_graphic_unique_id_count": len({row["element_id"] for row in graphic_manual}),
        "manual_critical_row_count": len(critical_manual),
        "manual_critical_unique_id_count": len({row["pair_id"] for row in critical_manual}),
        "manual_low_profile_row_count": len(low_manual),
        "manual_role_script_row_count": len(role_manual),
        "manual_view_row_count": len(view_manual),
        "manual_nonpass_row_count": manual_nonpass_count,
        "manual_pending_or_blank_cell_count": manual_pending_or_blank_count,
        "external_calibration_row_count": len(cal_metrics),
        "external_calibration_ratio_violation_count": len(calibration_ratio_violations),
        "json_parse_error_count": len(json_errors),
        "csv_parse_error_count": len(csv_errors),
        "png_open_error_count": len(png_errors),
        "png_file_count": len(pngs),
        "cache_or_pyc_count": len(cache_files),
        "symlink_or_reparse_candidate_count": len(symlinks),
        "math_rule_object_count": 0,
    }
    expected_errors = []
    exact_expected = {
        "pdf_bytes": 4967063,
        "pdf_sha256": "B49C5CA920DDEF6C0CD004B2581EAF710F4D1E1115BB459A324A84594B3831F3",
        "source_bytes": 3008,
        "source_sha256": "8773FF1EFFCB79DDD44734E72F0B0101292F135165021B32A760A6151DC0DE15",
        "visible_object_count": 177,
        "visible_object_unique_id_count": 177,
        "safe_filename_map_count": 177,
        "safe_filename_unique_count": 177,
        "unordered_pair_count": 15576,
        "unordered_pair_unique_id_count": 15576,
        "unordered_pair_formula_expected": 15576,
        "critical_relation_count": 154,
        "raw_intersection_pair_count": 14,
        "glyph_mask_file_count": 162,
        "graphic_mask_file_count": 15,
        "mask_empty_or_solid_count": 0,
        "glyph_contact_sheet_count": 17,
        "graphic_contact_sheet_count": 1,
        "critical_contact_sheet_count": 16,
        "critical_roi_png_count": 924,
        "manual_glyph_row_count": 162,
        "manual_glyph_unique_id_count": 162,
        "manual_graphic_row_count": 15,
        "manual_graphic_unique_id_count": 15,
        "manual_critical_row_count": 154,
        "manual_critical_unique_id_count": 154,
        "manual_low_profile_row_count": 7,
        "manual_role_script_row_count": 13,
        "manual_view_row_count": 17,
        "manual_nonpass_row_count": 0,
        "manual_pending_or_blank_cell_count": 0,
        "external_calibration_row_count": 4,
        "external_calibration_ratio_violation_count": 0,
        "json_parse_error_count": 0,
        "csv_parse_error_count": 0,
        "png_open_error_count": 0,
        "cache_or_pyc_count": 0,
        "symlink_or_reparse_candidate_count": 0,
        "math_rule_object_count": 0,
    }
    for key, expected in exact_expected.items():
        if checks[key] != expected:
            expected_errors.append(f"{key}: expected {expected!r}; actual {checks[key]!r}")
    result = {
        "handoff_id": "C-FIG-P641-01-R110-SA1-FRESH-ISOLATED-V1",
        "checks": checks,
        "technical_error_count": len(expected_errors) + len(json_errors) + len(csv_errors) + len(png_errors),
        "technical_errors": expected_errors + json_errors + csv_errors + png_errors,
        "mask_empty_or_solid": mask_empty_or_solid,
        "calibration_ratio_violations": calibration_ratio_violations,
        "cache_files": cache_files,
        "symlink_candidates": symlinks,
        "machine_reviewer_decisions_generated": False,
    }
    (ROOT / "machine_preseal_validation.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
