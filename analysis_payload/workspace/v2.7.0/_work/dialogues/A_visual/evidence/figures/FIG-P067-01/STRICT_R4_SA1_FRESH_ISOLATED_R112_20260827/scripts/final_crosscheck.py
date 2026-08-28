from __future__ import annotations

import csv
import hashlib
import itertools
import json
from pathlib import Path

from PIL import Image


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\dialogues\A_visual\evidence\figures\FIG-P067-01\STRICT_R4_SA1_FRESH_ISOLATED_R112_20260827")
PDF = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r112_fullbook\main_full.pdf")
TEX = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C04\fig_v1_c04_cdf.tex")


def rows(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open("r", encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def open_png(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        image.verify()
    with Image.open(path) as image:
        return image.size


def main() -> None:
    summary = json.loads((ROOT / "machine_summary.json").read_text(encoding="utf-8"))
    objects = rows("object_manifest.csv")
    pairs = rows("after_overlap_report.csv")
    critical = rows("critical_pair_inventory.csv")
    manual_objects = rows("manual_object_ledger.csv")
    manual_pairs = rows("manual_critical_pair_ledger.csv")
    manual_views = rows("manual_view_ledger.csv")
    fonts = rows("after_font_audit.csv")

    object_ids = [row["object_id"] for row in objects]
    manual_ids = [row["element_id"] for row in manual_objects]
    pair_ids = [row["pair_id"] for row in pairs]
    expected_pairs = {
        tuple(sorted(pair)) for pair in itertools.combinations(object_ids, 2)
    }
    actual_pairs = {tuple(sorted((row["a_id"], row["b_id"]))) for row in pairs}

    object_view_paths = []
    manifest_json = json.loads((ROOT / "object_manifest.json").read_text(encoding="utf-8"))
    for obj in manifest_json:
        object_view_paths.extend(obj["views"].values())
    object_view_dims = {name: open_png(ROOT / name) for name in object_view_paths}

    final_view_names = [
        "full_page_200dpi.png",
        "render/full_page_300dpi.png",
        "figure_crop_300dpi.png",
        "standalone_300dpi.png",
        "grayscale_300dpi.png",
        "figure_crop_300dpi_nearest8x.png",
        "after_text_measurement_overlay_300dpi.png",
    ]
    final_view_dims = {name: open_png(ROOT / name) for name in final_view_names}
    contact_names = [f"contact_sheets/glyph_contact_{index:02d}.png" for index in range(1, 9)]
    contact_dims = {name: open_png(ROOT / name) for name in contact_names}

    critical_evidence_paths = []
    for row in critical:
        safe = row["pair_id"].replace("-", "_")
        for suffix in (
            "raw_1x",
            "raw_nearest8x",
            "A_mask_1x",
            "B_mask_1x",
            "intersection_1x",
            "1x",
            "nearest8x",
        ):
            critical_evidence_paths.append(f"roi/{safe}__{suffix}.png")
    critical_dims = {name: open_png(ROOT / name) for name in critical_evidence_paths}
    actual_roi_paths = {
        str(path.relative_to(ROOT)).replace("\\", "/") for path in (ROOT / "roi").glob("*.png")
    }

    ordinary_files = [path for path in ROOT.rglob("*") if path.is_file()]
    colon_filename_count = sum(":" in path.name for path in ordinary_files)
    checks = {
        "pdf_identity_ok": PDF.stat().st_size == 4_967_100 and sha256(PDF) == "D4B4DDF5F127D107FB66BF2805F4637D39CDB861F7CBB47BB2CDBB72E4E28FA2",
        "tex_identity_ok": TEX.stat().st_size == 4_015 and sha256(TEX) == "C570597B72EEA4610380359A84EA078B24C810EC89039215BC9B42AB0F8AFFA0",
        "object_count_ok": len(objects) == summary["object_count"] == 150,
        "object_ids_unique": len(object_ids) == len(set(object_ids)) == 150,
        "manual_object_count_ok": len(manual_objects) == 150,
        "manual_object_ids_exact": set(manual_ids) == set(object_ids) and len(manual_ids) == len(set(manual_ids)),
        "manual_object_all_reviewed": all(row["reviewer"] and row["decision"] == "PASS_R168" for row in manual_objects),
        "manual_object_open_booleans_complete": all(row["original_match"] == "true" and row["overlay_complete"] == "true" for row in manual_objects),
        "pair_count_ok": len(pairs) == summary["unordered_pair_count"] == 11_175,
        "pair_ids_unique": len(pair_ids) == len(set(pair_ids)) == 11_175,
        "all_unordered_pairs_exact": actual_pairs == expected_pairs and len(actual_pairs) == 11_175,
        "critical_pair_count_ok": len(critical) == len(manual_pairs) == 12,
        "critical_pair_ids_exact": {row["pair_id"] for row in critical} == {row["pair_id"] for row in manual_pairs},
        "critical_pair_manual_all_opened": all(
            row[flag] == "true"
            for row in manual_pairs
            for flag in ("raw_1x_opened", "raw_nearest8x_opened", "overlay_nearest8x_opened", "a_mask_opened", "b_mask_opened", "intersection_opened")
        ),
        "critical_pair_manual_actual_hard_zero": all(
            row["actual_illegal_overlap"] == "false"
            and row["actual_clearance_failure"] == "false"
            and row["decision"] == "PASS_R168"
            for row in manual_pairs
        ),
        "manual_view_rows_ok": len(manual_views) == 9,
        "manual_views_all_opened_and_pass": all(
            row["actually_opened"] == "true" and row["decision"] == "PASS_R168" for row in manual_views
        ),
        "empty_mask_count_zero": summary["empty_mask_count"] == 0 and all(row["empty_mask"] == "False" for row in objects),
        "clip_pixel_count_zero": summary["clip_pixel_count"] == 0,
        "object_view_file_count_ok": len(object_view_paths) == 600 and len(set(object_view_paths)) == 600 and len(object_view_dims) == 600,
        "contact_sheet_count_ok": len(contact_dims) == 8,
        "critical_evidence_file_count_ok": len(critical_evidence_paths) == 84 and len(set(critical_evidence_paths)) == 84 and len(critical_dims) == 84,
        "critical_roi_directory_exact": actual_roi_paths == set(critical_evidence_paths),
        "final_view_dimensions_ok": final_view_dims["figure_crop_300dpi.png"] == (1622, 663)
        and final_view_dims["standalone_300dpi.png"] == (1622, 580)
        and final_view_dims["render/full_page_300dpi.png"] == (2481, 3508)
        and final_view_dims["full_page_200dpi.png"] == (1654, 2339),
        "font_audit_rows_ok": len(fonts) == 9 and all(row["r168_status"] == "ADVISORY_BELOW_9_5" for row in fonts),
        "portable_filenames_no_colon": colon_filename_count == 0,
        "acceptance_present": (ROOT / "after_visual_acceptance.md").is_file(),
        "result_present_and_pass": (ROOT / "RESULT").is_file()
        and "FINAL_DECISION=PASS_R168" in (ROOT / "RESULT").read_text(encoding="utf-8"),
    }
    failed = [name for name, passed in checks.items() if not passed]
    record = {
        "handoff_id": "A-R112-P067-SA1-FRESH-ISOLATED-20260827",
        "uid": "FIG-P067-01",
        "checks": checks,
        "failed_checks": failed,
        "counts": {
            "objects": len(objects),
            "manual_objects": len(manual_objects),
            "pairs": len(pairs),
            "critical_pairs": len(critical),
            "manual_critical_pairs": len(manual_pairs),
            "object_view_files_opened_by_validator": len(object_view_dims),
            "critical_evidence_files_opened_by_validator": len(critical_dims),
            "contact_sheets_opened_by_validator": len(contact_dims),
            "ordinary_files_before_crosscheck_write": len(ordinary_files),
        },
        "machine_candidate_count": summary["machine_hard_candidate_count"],
        "manual_actual_hard_count": 0,
        "crosscheck_pass": not failed,
    }
    (ROOT / "machine_crosscheck.json").write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(record, ensure_ascii=True, indent=2))
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
