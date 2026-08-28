from __future__ import annotations

import csv
import hashlib
import itertools
import json
from datetime import datetime, timezone
from pathlib import Path

import fitz
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r107_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C07\web_random_walk.tex")
EXPECTED_PDF_SHA = "8811950621E2D64A3C2A8F0F7A52DD0FAC2BDB12018F3EA052C1F58C94EF8DF3"
EXPECTED_SOURCE_SHA = "900C3A8F72A7A6434101FEE9914019150D3D5F655A23FC5BF41EDB853C25EE87"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def read_csv(path: Path, delimiter: str = ",") -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=delimiter))


def png_ok(path: Path) -> bool:
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            return image.width > 0 and image.height > 0
    except Exception:
        return False


def all_true(rows: list[dict[str, str]], fields: list[str]) -> bool:
    return all(row.get(field) == "TRUE" for row in rows for field in fields)


def all_zero(rows: list[dict[str, str]], fields: list[str]) -> bool:
    return all(row.get(field) == "0" for row in rows for field in fields)


def main() -> None:
    checks: dict[str, object] = {}

    pdf_sha = sha256(PDF)
    source_sha = sha256(SOURCE)
    with fitz.open(PDF) as doc:
        pdf_pages = doc.page_count
    checks["pdf_identity"] = {
        "bytes": PDF.stat().st_size,
        "pages": pdf_pages,
        "sha256": pdf_sha,
        "pass": PDF.stat().st_size == 4_967_249 and pdf_pages == 817 and pdf_sha == EXPECTED_PDF_SHA,
    }
    checks["source_identity"] = {
        "bytes": SOURCE.stat().st_size,
        "sha256": source_sha,
        "pass": SOURCE.stat().st_size == 4_057 and source_sha == EXPECTED_SOURCE_SHA,
    }

    objects = read_csv(ROOT / "machine" / "object_ledger.csv")
    text = [row for row in objects if row["kind"] == "TEXT"]
    graphics = [row for row in objects if row["kind"] == "GRAPHIC"]
    ids = [row["id"] for row in objects]
    checks["object_denominator"] = {
        "text": len(text),
        "graphics": len(graphics),
        "N": len(objects),
        "unique_ids": len(set(ids)),
        "pass": len(text) == 216 and len(graphics) == 43 and len(objects) == 259 and len(set(ids)) == 259,
    }

    mask_open_failures = []
    mask_dimension_failures = []
    for row in objects:
        path = ROOT / row["mask_path"]
        if not path.is_file() or not png_ok(path):
            mask_open_failures.append(row["id"])
            continue
        box = json.loads(row["bbox_px"])
        expected_size = (int(box[2]) - int(box[0]), int(box[3]) - int(box[1]))
        with Image.open(path) as image:
            if image.size != expected_size:
                mask_dimension_failures.append(row["id"])
    checks["mask_files"] = {
        "expected": 259,
        "ordinary_openable": 259 - len(mask_open_failures),
        "open_failures": mask_open_failures,
        "dimension_failures": mask_dimension_failures,
        "empty_mask_rows": [row["id"] for row in objects if row["empty_mask"] != "False" or int(row["mask_pixel_count"]) <= 0],
        "clip_rows": [row["id"] for row in objects if int(row["clip_pixel_count"]) != 0],
        "tofu_or_decode_rows": [row["id"] for row in text if row["tofu_or_decode_candidate"] != "False"],
    }
    checks["mask_files"]["pass"] = not any((
        checks["mask_files"]["open_failures"],
        checks["mask_files"]["dimension_failures"],
        checks["mask_files"]["empty_mask_rows"],
        checks["mask_files"]["clip_rows"],
        checks["mask_files"]["tofu_or_decode_rows"],
    ))

    safe = read_csv(ROOT / "machine" / "id_safe_filename.csv")
    checks["safe_filename_map"] = {
        "rows": len(safe),
        "unique_ids": len({row["element_id"] for row in safe}),
        "unique_safe_filenames": len({row["safe_filename"] for row in safe}),
        "paths_exist": sum((ROOT / row["ordinary_path"]).is_file() for row in safe),
    }
    checks["safe_filename_map"]["pass"] = (
        checks["safe_filename_map"]["rows"] == 259
        and checks["safe_filename_map"]["unique_ids"] == 259
        and checks["safe_filename_map"]["unique_safe_filenames"] == 259
        and checks["safe_filename_map"]["paths_exist"] == 259
        and {row["element_id"] for row in safe} == set(ids)
    )

    pairs = read_csv(ROOT / "machine" / "all_unordered_pairs.csv")
    actual_pairs = {(row["object_a"], row["object_b"]) for row in pairs}
    expected_pairs = set(itertools.combinations(ids, 2))
    critical = [row for row in pairs if row["critical"] == "True"]
    intersections = [row for row in pairs if int(row["intersection_px"]) > 0]
    intersection_classes: dict[str, int] = {}
    for row in intersections:
        intersection_classes[row["relation"]] = intersection_classes.get(row["relation"], 0) + 1
    checks["all_unordered_pairs"] = {
        "rows": len(pairs),
        "unique_pair_ids": len({row["pair_id"] for row in pairs}),
        "unique_object_pairs": len(actual_pairs),
        "expected_pairs": len(expected_pairs),
        "missing_pairs": len(expected_pairs - actual_pairs),
        "unexpected_pairs": len(actual_pairs - expected_pairs),
        "critical_pairs": len(critical),
        "intersection_pairs": len(intersections),
        "intersection_classes": intersection_classes,
        "illegal_overlap_candidates": sum(row["illegal_overlap_candidate"] == "True" for row in pairs),
        "clearance_failure_candidates": sum(row["clearance_failure_candidate"] == "True" for row in pairs),
        "blank_core_fields": sum(
            any(not row[field] for field in ("pair_id", "object_a", "object_b", "relation", "clearance_px", "intersection_px"))
            for row in pairs
        ),
    }
    checks["all_unordered_pairs"]["pass"] = (
        len(pairs) == 33_411
        and len({row["pair_id"] for row in pairs}) == 33_411
        and actual_pairs == expected_pairs
        and len(critical) == 16
        and checks["all_unordered_pairs"]["intersection_classes"] == {
            "DESIGN_FOCUS_ON_CELL": 18,
            "DESIGN_INTERNAL_GRAPHIC": 4,
            "DESIGN_MATRIX_GRID": 60,
            "GRAPHIC_GRAPHIC": 4,
        }
        and checks["all_unordered_pairs"]["illegal_overlap_candidates"] == 0
        and checks["all_unordered_pairs"]["clearance_failure_candidates"] == 0
        and checks["all_unordered_pairs"]["blank_core_fields"] == 0
    )

    drawing = read_csv(ROOT / "machine" / "drawing_inventory.csv")
    checks["drawing_path_coverage"] = {
        "rows": len(drawing),
        "unique_ids": len({row["id"] for row in drawing}),
        "unique_drawing_seqno": len({row["drawing_seqno"] for row in drawing}),
        "math_rule_rows": sum(row["graphic_type"] == "MATH_RULE" for row in drawing),
        "pass": len(drawing) == 43
        and {row["id"] for row in drawing} == {row["id"] for row in graphics}
        and len({row["drawing_seqno"] for row in drawing}) == 43
        and not any(row["graphic_type"] == "MATH_RULE" for row in drawing),
    }

    glyph_manual = read_csv(ROOT / "review" / "manual_glyph_reviewer_ledger.tsv", "\t")
    graphic_manual = read_csv(ROOT / "review" / "manual_graphic_reviewer_ledger.tsv", "\t")
    critical_manual = read_csv(ROOT / "review" / "manual_critical_pair_reviewer_ledger.tsv", "\t")
    four_view_manual = read_csv(ROOT / "review" / "manual_four_view_ledger.tsv", "\t")
    panel_role_manual = read_csv(ROOT / "review" / "manual_panel_role_script_ledger.tsv", "\t")
    connection_manual = read_csv(ROOT / "review" / "manual_graphic_connection_ledger.tsv", "\t")
    checks["manual_ledgers"] = {
        "glyph_rows": len(glyph_manual),
        "graphic_rows": len(graphic_manual),
        "critical_pair_rows": len(critical_manual),
        "four_view_rows": len(four_view_manual),
        "panel_role_rows": len(panel_role_manual),
        "graphic_connection_rows": len(connection_manual),
        "pass": (
            len(glyph_manual) == 216
            and {row["id"] for row in glyph_manual} == {row["id"] for row in text}
            and len({row["id"] for row in glyph_manual}) == 216
            and all_true(glyph_manual, ["original_match", "overlay_complete", "mask_only_pure"])
            and all_zero(glyph_manual, ["missing_stroke_px", "foreign_pixel_px"])
            and all(row["decision"] == "PASS" and row["note"] for row in glyph_manual)
            and len(graphic_manual) == 43
            and {row["id"] for row in graphic_manual} == {row["id"] for row in graphics}
            and len({row["id"] for row in graphic_manual}) == 43
            and all_true(graphic_manual, ["original_match", "overlay_complete", "mask_only_pure"])
            and all_zero(graphic_manual, ["missing_path_px", "foreign_pixel_px"])
            and all(row["decision"] == "PASS" and row["note"] for row in graphic_manual)
            and len(critical_manual) == 16
            and {row["pair_id"] for row in critical_manual} == {row["pair_id"] for row in critical}
            and len({row["pair_id"] for row in critical_manual}) == 16
            and all_true(critical_manual, ["native1x_opened", "nearest8x_opened"])
            and all(row["illegal_overlap"] == "FALSE" and row["clearance_failure"] == "FALSE" and row["decision"] == "PASS" and row["note"] for row in critical_manual)
            and len(four_view_manual) == 6
            and all_true(four_view_manual, ["actual_opened", "content_legible", "no_clip", "no_illegal_overlap", "no_severe_imbalance"])
            and all(row["decision"] == "PASS" and row["note"] for row in four_view_manual)
            and len(panel_role_manual) == 9
            and all_true(panel_role_manual, ["actually_legible", "not_crowded", "not_jarring"])
            and all(row["decision"] == "PASS" and row["note"] and row["D_status"] and row["E_status"] and row["cross_panel_status"] for row in panel_role_manual)
            and len(connection_manual) == 4
            and all_true(connection_manual, ["geometry_correct"])
            and all(row["decision"] == "PASS" and row["note"] for row in connection_manual)
        ),
    }

    critical_file_failures = []
    for row in critical:
        for field in ("evidence_native1x", "evidence_8x"):
            path = ROOT / row[field]
            if not path.is_file() or not png_ok(path):
                critical_file_failures.append(f"{row['pair_id']}:{field}")
    checks["critical_evidence"] = {
        "expected_native1x": 16,
        "expected_8x": 16,
        "file_failures": critical_file_failures,
        "native1x_actual": len(list((ROOT / "review" / "critical_pairs" / "native1x").glob("*.png"))),
        "nearest8x_actual": len(list((ROOT / "review" / "critical_pairs" / "8x_nearest").glob("*.png"))),
        "pair_sheets_actual": len(list((ROOT / "review").glob("critical_pair_sheet_*.png"))),
    }
    checks["critical_evidence"]["pass"] = (
        not critical_file_failures
        and checks["critical_evidence"]["native1x_actual"] == 16
        and checks["critical_evidence"]["nearest8x_actual"] == 16
        and checks["critical_evidence"]["pair_sheets_actual"] == 2
    )

    sheet_groups = {
        "glyph": sorted((ROOT / "review").glob("glyph_contact_sheet_*.png")),
        "graphic": sorted((ROOT / "review").glob("graphic_contact_sheet_*.png")),
        "critical": sorted((ROOT / "review").glob("critical_pair_sheet_*.png")),
    }
    checks["contact_sheets"] = {
        "glyph": len(sheet_groups["glyph"]),
        "graphic": len(sheet_groups["graphic"]),
        "critical": len(sheet_groups["critical"]),
        "open_failures": [str(path.relative_to(ROOT)) for paths in sheet_groups.values() for path in paths if not png_ok(path)],
    }
    checks["contact_sheets"]["pass"] = (
        checks["contact_sheets"]["glyph"] == 18
        and checks["contact_sheets"]["graphic"] == 4
        and checks["contact_sheets"]["critical"] == 2
        and not checks["contact_sheets"]["open_failures"]
    )

    copies = {
        "full_page_200dpi.png": "renders/full_page_200dpi.png",
        "figure_crop_300dpi.png": "renders/figure_crop_300dpi.png",
        "standalone_300dpi.png": "renders/standalone_300dpi.png",
        "grayscale_300dpi.png": "renders/grayscale_300dpi.png",
        "after_text_measurement_overlay_300dpi.png": "renders/after_text_measurement_overlay_300dpi.png",
        "after_font_audit.csv": "machine/after_font_audit.csv",
        "after_pixel_measurements.csv": "machine/after_pixel_measurements.csv",
        "after_overlap_report.csv": "machine/all_unordered_pairs.csv",
    }
    copy_results = {}
    for canonical, source in copies.items():
        canonical_path = ROOT / canonical
        source_path = ROOT / source
        copy_results[canonical] = canonical_path.is_file() and source_path.is_file() and sha256(canonical_path) == sha256(source_path)
    checks["canonical_evidence_files"] = {"files": copy_results, "pass": all(copy_results.values())}

    required_manual_docs = [
        ROOT / "after_visual_acceptance.md",
        ROOT / "after_overlap_adjudication.md",
        ROOT / "review" / "manual_semantic_geometry_review.md",
        ROOT / "SA1_REPORT.md",
        ROOT / "RESULT.json",
    ]
    checks["required_reports"] = {
        "missing": [str(path.relative_to(ROOT)) for path in required_manual_docs if not path.is_file()],
    }
    checks["required_reports"]["pass"] = not checks["required_reports"]["missing"]

    result_path = ROOT / "RESULT.json"
    result_consistent = False
    if result_path.is_file():
        result = json.loads(result_path.read_text(encoding="utf-8"))
        result_consistent = (
            result.get("verdict") == "PASS"
            and result.get("callback") == "SA1_PASS_READY_FOR_FRESH_ISOLATED_SA3"
            and result.get("visible_object_denominator_N") == 259
            and result.get("all_unordered_pair_count_C_N_2") == 33_411
            and result.get("machine_hard_failure_count") == 0
            and result.get("manual_hard_failure_count") == 0
        )
    checks["result_consistency"] = {"pass": result_consistent}

    pass_values = [value["pass"] for value in checks.values() if isinstance(value, dict) and "pass" in value]
    output = {
        "handoff_id": "A-R107-P715-SA1-FRESH-ISOLATED-20260826",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "machine crosscheck only; manual reviewer decisions are read but never generated or overwritten",
        "checks": checks,
        "machine_crosscheck_pass": all(pass_values),
        "machine_crosscheck_failure_count": sum(not value for value in pass_values),
    }
    (ROOT / "machine" / "final_machine_crosscheck.json").write_text(
        json.dumps(output, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "machine_crosscheck_pass": output["machine_crosscheck_pass"],
        "machine_crosscheck_failure_count": output["machine_crosscheck_failure_count"],
    }))


if __name__ == "__main__":
    main()
