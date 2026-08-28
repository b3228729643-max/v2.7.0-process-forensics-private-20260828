from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r114_fullbook\main_full.pdf")
SOURCE = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C04\fig_v1_c04_cdf.tex")
AUDIT_PATH = ROOT / "00_control" / "PRESEAL_AUDIT.json"
MANIFEST_PATH = ROOT / "00_control" / "ROOT_MANIFEST_SHA256.csv"
CONTROL_PATH = ROOT / "00_control" / "ROOT_MANIFEST_CONTROL.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    required = [
        "EVIDENCE_INDEX.md",
        "00_control/build_mechanical_evidence.py",
        "00_control/input_identity.json",
        "00_control/mechanical_summary.json",
        "00_control/visible_object_denominator_mechanical.csv",
        "00_control/all_unordered_pairs_mechanical.csv",
        "01_locator/fullbook_layout.txt",
        "01_locator/physical_page_derived_bbox.xhtml",
        "01_locator/locator_record.md",
        "01_locator/text_bbox_mechanical.csv",
        "02_page/page_300dpi.png",
        "02_page/full_page_200dpi.png",
        "03_figure/figure_native1x_300dpi.png",
        "03_figure/figure_nearest8x.png",
        "03_figure/figure_grayscale_300dpi.png",
        "03_figure/text_bbox_overlay_300dpi.png",
        "04_critical/critical_contact_sheet_native1x.png",
        "04_critical/roi01_upper_note_axis_native1x.png",
        "04_critical/roi02_jump_markers_labels_native1x.png",
        "04_critical/roi03_lower_pmf_annotation_native1x.png",
        "05_manual/manual_visible_object_ledger.csv",
        "05_manual/manual_pair_adjudication.md",
        "05_manual/manual_math_geometry_caption_page_ledger.md",
        "05_manual/manual_r168_visual_acceptance.md",
    ]
    required_exists = {item: (ROOT / item).is_file() for item in required}

    denominator = csv_rows(ROOT / "00_control" / "visible_object_denominator_mechanical.csv")
    pairs = csv_rows(ROOT / "00_control" / "all_unordered_pairs_mechanical.csv")
    manual = csv_rows(ROOT / "05_manual" / "manual_visible_object_ledger.csv")
    denominator_ids = [row["OBJECT_ID"] for row in denominator]
    manual_ids = [row["OBJECT_ID"] for row in manual]
    pair_keys = [tuple(sorted((row["OBJECT_ID_A"], row["OBJECT_ID_B"]))) for row in pairs]
    pair_ids = [row["PAIR_ID"] for row in pairs]
    manual_pair_text = (ROOT / "05_manual" / "manual_pair_adjudication.md").read_text(encoding="utf-8")
    listed_legal_pair_ids = re.findall(r"PAIR-\d{4}", manual_pair_text)
    acceptance_text = (ROOT / "05_manual" / "manual_r168_visual_acceptance.md").read_text(encoding="utf-8")

    image_dimensions = {}
    for item in required:
        if item.lower().endswith(".png"):
            with Image.open(ROOT / item) as image:
                image_dimensions[item] = [image.width, image.height, image.mode]

    checks = {
        "required_files_all_exist": all(required_exists.values()),
        "pdf_bytes_match": PDF.stat().st_size == 4967122,
        "pdf_sha256_match": sha256(PDF) == "C3BB9B1C7FC9D7AF9178CD33F227F24899AA505FAB81840DB6E3AD8BD6CE78A6",
        "source_bytes_match": SOURCE.stat().st_size == 4014,
        "source_sha256_match": sha256(SOURCE) == "11BF3681D069F6A38C479B3074F39F93E8EB6144FF155AC543508E3589A51144",
        "denominator_count_63": len(denominator) == 63,
        "denominator_ids_unique": len(set(denominator_ids)) == 63,
        "text_formula_count_21": sum(row["OBJECT_KIND"] == "TEXT_OR_FORMULA" for row in denominator) == 21,
        "graphic_count_42": sum(row["OBJECT_KIND"] == "GRAPHIC" for row in denominator) == 42,
        "pair_count_1953": len(pairs) == 1953,
        "pair_ids_unique": len(set(pair_ids)) == 1953,
        "pair_keys_unique": len(set(pair_keys)) == 1953,
        "pair_self_count_zero": all(a != b for a, b in pair_keys),
        "pair_refs_complete": all(a in denominator_ids and b in denominator_ids for a, b in pair_keys),
        "manual_rows_63": len(manual) == 63,
        "manual_ids_unique": len(set(manual_ids)) == 63,
        "manual_ids_exactly_match_denominator": set(manual_ids) == set(denominator_ids),
        "manual_reviewer_exact": {row["REVIEWER"] for row in manual} == {"SA3_FRESH_ISOLATED"},
        "manual_decisions_all_pass": {row["MANUAL_DECISION"] for row in manual} == {"PASS"},
        "manual_legal_pair_ids_68_unique": len(listed_legal_pair_ids) == 68 and len(set(listed_legal_pair_ids)) == 68,
        "manual_legal_pair_ids_in_universe": set(listed_legal_pair_ids).issubset(set(pair_ids)),
        "resolved_return_code_present": "SA3_PASS_AWAIT_MAIN_A_LOCAL_PASS_ACCEPTANCE" in acceptance_text,
        "native_300_dimensions_correct": image_dimensions.get("03_figure/figure_native1x_300dpi.png") == [1646, 584, "RGB"],
        "nearest8x_dimensions_exact": image_dimensions.get("03_figure/figure_nearest8x.png") == [13168, 4672, "RGB"],
        "grayscale_dimensions_correct": image_dimensions.get("03_figure/figure_grayscale_300dpi.png") == [1646, 584, "L"],
        "page_300_dimensions_correct": image_dimensions.get("02_page/page_300dpi.png") == [2481, 3508, "RGB"],
        "page_200_dimensions_correct": image_dimensions.get("02_page/full_page_200dpi.png") == [1654, 2339, "RGB"],
    }
    audit = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(ROOT),
        "required_files": required_exists,
        "image_dimensions": image_dimensions,
        "counts": {
            "denominator": len(denominator),
            "text_formula": sum(row["OBJECT_KIND"] == "TEXT_OR_FORMULA" for row in denominator),
            "graphic": sum(row["OBJECT_KIND"] == "GRAPHIC" for row in denominator),
            "unordered_pairs": len(pairs),
            "manual_object_rows": len(manual),
            "manual_legal_pair_ids": len(set(listed_legal_pair_ids)),
        },
        "checks": checks,
        "all_checks_pass": all(checks.values()),
        "manual_fields_generated_or_overwritten": False,
    }
    if not audit["all_checks_pass"]:
        raise SystemExit(json.dumps(audit, ensure_ascii=False, indent=2))
    AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    excluded = {
        MANIFEST_PATH.relative_to(ROOT).as_posix(),
        CONTROL_PATH.relative_to(ROOT).as_posix(),
        "WRITE_STOPPED",
    }
    manifest_rows = []
    for path in sorted((item for item in ROOT.rglob("*") if item.is_file()), key=lambda item: item.relative_to(ROOT).as_posix()):
        relative = path.relative_to(ROOT).as_posix()
        if relative in excluded:
            continue
        stat = path.stat()
        manifest_rows.append(
            {
                "RELATIVE_PATH": relative,
                "BYTES": stat.st_size,
                "SHA256": sha256(path),
                "LAST_WRITE_TIME_UTC": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
            }
        )
    with MANIFEST_PATH.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(manifest_rows[0]))
        writer.writeheader()
        writer.writerows(manifest_rows)

    control = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "root": str(ROOT),
        "manifest_path": str(MANIFEST_PATH),
        "manifest_sha256": sha256(MANIFEST_PATH),
        "manifest_entry_count": len(manifest_rows),
        "manifest_scope_excludes": sorted(excluded),
        "preseal_audit_path": str(AUDIT_PATH),
        "preseal_audit_sha256": sha256(AUDIT_PATH),
        "expected_root_file_count_before_marker": len(manifest_rows) + 2,
        "expected_root_file_count_after_marker": len(manifest_rows) + 3,
        "expected_root_directory_count_including_root": sum(1 for item in ROOT.rglob("*") if item.is_dir()) + 1,
        "resolved_result": "PASS",
        "resolved_return_code": "SA3_PASS_AWAIT_MAIN_A_LOCAL_PASS_ACCEPTANCE",
        "manual_fields_generated_or_overwritten": False,
    }
    CONTROL_PATH.write_text(json.dumps(control, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"audit": audit["all_checks_pass"], "manifest_entries": len(manifest_rows), "control": control}, ensure_ascii=False))


if __name__ == "__main__":
    main()
