"""Final integrity check and write-stop seal for FIG-P020-01 R6 R111 SA1."""

from __future__ import annotations

import csv
import json
import os
import re
import stat
import subprocess
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
TERMINAL = ROOT / "terminal"


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise RuntimeError(f"CSV header missing/duplicated: {path}")
        return list(reader)


def write_json(path: Path, object_: object) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(object_, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def write_text(path: Path, text: str) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def safe_rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def ads_count() -> int:
    root_ps = str(ROOT).replace("'", "''")
    command = (
        "$ErrorActionPreference='Stop';"
        f"$root='{root_ps}';"
        "$n=0;"
        "Get-ChildItem -Path $root -Recurse -File | ForEach-Object {"
        "Get-Item -Path $_.FullName -Stream * | Where-Object {$_.Stream -ne ':$DATA'} | ForEach-Object {$n++}"
        "};"
        "[Console]::Write($n)"
    )
    process = subprocess.run(
        ["powershell.exe", "-NoProfile", "-Command", command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError(f"ADS enumeration failed: {process.stderr}")
    return int(process.stdout.strip() or "0")


def expected_paths() -> tuple[set[str], set[str], set[str], set[str]]:
    manifest = read_csv(ROOT / "glyph_id_filename_manifest.csv")
    graphic = read_csv(ROOT / "relations" / "graphic_manifest.csv")
    expected_png: set[str] = {
        "full_page_200dpi.png",
        "figure_crop_300dpi.png",
        "standalone_300dpi.png",
        "grayscale_300dpi.png",
        "after_text_measurement_overlay_300dpi.png",
        "views/figure_crop_300dpi.png",
        "raw/r95_page_017_native300.png",
        "raw/r95_page_017_200dpi.png",
        "occlusion/g_return_arrow_pre_occlusion_mask_1x.png",
        "occlusion/g_return_arrow_final_visible_mask_1x.png",
        "occlusion/g_return_arrow_x_opaque_ground_intersection_1x.png",
        "occlusion/g_return_label_white_opaque_ground_vector_coverage_1x.png",
        "occlusion/return_label_ground_paint_order_overlay_1x.png",
        "occlusion/return_label_ground_paint_order_overlay_8x_nearest.png",
        "calibration/colon_form_calibrator_page_native300.png",
        "calibration/r95_page_048_dot_reference_native300.png",
        "calibration/cal_colon_r95_form_original_1x.png",
        "calibration/cal_colon_r95_form_target_overlay_1x.png",
        "calibration/cal_colon_r95_form_mask_only_1x.png",
        "calibration/cal_colon_r95_form_triad_8x_nearest.png",
        "calibration/cal_dot_r95_page048_original_1x.png",
        "calibration/cal_dot_r95_page048_target_overlay_1x.png",
        "calibration/cal_dot_r95_page048_mask_only_1x.png",
        "calibration/cal_dot_r95_page048_triad_8x_nearest.png",
    }
    for row in manifest:
        safe = row["SAFE_FILENAME"]
        for suffix in ("_original_1x.png", "_target_overlay_1x.png", "_mask_only_1x.png", "_triad_8x_nearest.png"):
            expected_png.add(f"glyphs/{safe}{suffix}")
    for start in range(0, len(manifest), 6):
        batch = manifest[start : start + 6]
        expected_png.add(
            f"contact_sheets/CS{start // 6 + 1:03d}_{batch[0]['SAFE_FILENAME']}_to_{batch[-1]['SAFE_FILENAME']}_8x.png"
        )
    expected_png.update(row["FINAL_VISIBLE_MASK_1X"] for row in graphic)

    expected_csv = {
        "after_font_audit_precalibration.csv",
        "after_font_audit.csv",
        "after_overlap_report.csv",
        "after_pixel_measurements.csv",
        "glyph_id_filename_manifest.csv",
        "sa1_findings.csv",
        "calibration/low_profile_punctuation_calibration.csv",
        "ledger/de_actual_baselines.csv",
        "ledger/glyph_manual_review_ledger.csv",
        "ledger/semantic_parent_manifest.csv",
        "ledger/visual_harmony_ledger.csv",
        "occlusion/occlusion_ledger.csv",
        "relations/graphic_manifest.csv",
        "relations/text_figure_edge_relations.csv",
        "relations/text_graphic_relations.csv",
    }
    expected_json = {
        "R95_AUTHORITY_AND_SCOPE.json",
        "generation_counts.json",
        "final_table_summary.json",
        "calibration/low_profile_punctuation_calibration.json",
        "terminal/TERMINAL_MANIFEST.json",
        "terminal/MACHINE_INTEGRITY.json",
    }
    expected_other = {
        "ROLE_AND_WRITE_SCOPE.md",
        "after_visual_acceptance.md",
        "calibration/CALIBRATION_METHOD.md",
        "calibration/colon_same_font_same_pt.tex",
        "calibration/colon_same_font_same_pt.log",
        "calibration/colon_r95_form_rerender_calibrator.pdf",
        "calibration/extracted_r95_notoserifsc_extralight.ttf",
        "occlusion/PAINT_ORDER_AND_OCCLUSION_SCOPE.md",
        "raw/generator_stdout.txt",
        "scripts/generate_fig_p020_r111.py",
        "scripts/calibrate_low_profile_punctuation.py",
        "scripts/build_final_tables.py",
        "scripts/verify_and_seal_terminal.py",
        "terminal/SA1_FINAL_VERDICT.md",
        "terminal/WRITE_STOPPED.md",
    }
    return expected_png, expected_csv, expected_json, expected_other


def open_and_validate(expected_png: set[str], expected_csv: set[str], expected_json: set[str], expected_other: set[str]) -> dict:
    expected = expected_png | expected_csv | expected_json | expected_other
    actual = {safe_rel(path) for path in ROOT.rglob("*") if path.is_file()}
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing or unexpected:
        raise RuntimeError(f"Expected/actual mismatch; missing={missing}; unexpected={unexpected}")
    if len(expected_png) != 488:
        raise RuntimeError(f"Unexpected PNG design count: {len(expected_png)}")
    for relative in sorted(expected):
        path = ROOT / relative
        st = path.stat()
        if not stat.S_ISREG(st.st_mode):
            raise RuntimeError(f"Not a regular file: {relative}")
        if st.st_size <= 0:
            raise RuntimeError(f"Zero-byte file: {relative}")
        if re.search(r'[:*?"<>|]', path.name):
            raise RuntimeError(f"Unsafe filename: {relative}")
    image_sizes: dict[str, list[int]] = {}
    for relative in sorted(expected_png):
        with Image.open(ROOT / relative) as image:
            size = list(image.size)
            image.verify()
        if min(size) <= 0:
            raise RuntimeError(f"Bad PNG dimensions: {relative}")
        image_sizes[relative] = size
    csv_rows: dict[str, int] = {}
    for relative in sorted(expected_csv):
        csv_rows[relative] = len(read_csv(ROOT / relative))
    for relative in sorted(expected_json):
        with (ROOT / relative).open("r", encoding="utf-8") as handle:
            json.load(handle)
    for relative in sorted(expected_other):
        with (ROOT / relative).open("rb") as handle:
            if not handle.read(1):
                raise RuntimeError(f"Cannot open non-data evidence: {relative}")
    return {
        "expected_file_count": len(expected),
        "actual_file_count": len(actual),
        "expected_png_count": len(expected_png),
        "opened_png_count": len(image_sizes),
        "expected_csv_count": len(expected_csv),
        "parsed_csv_count": len(csv_rows),
        "expected_json_count": len(expected_json),
        "parsed_json_count": len(expected_json),
        "expected_other_count": len(expected_other),
        "opened_other_count": len(expected_other),
        "png_dimensions": image_sizes,
        "csv_rows": csv_rows,
        "expected_files": sorted(expected),
        "actual_files": sorted(actual),
    }


def main() -> None:
    TERMINAL.mkdir(parents=True, exist_ok=True)
    font_rows = read_csv(ROOT / "after_font_audit.csv")
    pixel_rows = read_csv(ROOT / "after_pixel_measurements.csv")
    manual_rows = read_csv(ROOT / "ledger" / "glyph_manual_review_ledger.csv")
    visual_rows = read_csv(ROOT / "ledger" / "visual_harmony_ledger.csv")
    relation_rows = read_csv(ROOT / "relations" / "text_graphic_relations.csv")
    edge_rows = read_csv(ROOT / "relations" / "text_figure_edge_relations.csv")
    calibration_rows = read_csv(ROOT / "calibration" / "low_profile_punctuation_calibration.csv")
    findings = read_csv(ROOT / "sa1_findings.csv")
    font_fails = [row for row in font_rows if row["FONT_GATE_FINAL"] == "FAIL"]
    if [row["ELEMENT_ID"] for row in font_fails] != ["F020_G091"]:
        raise RuntimeError(f"Unexpected final font failures: {[row['ELEMENT_ID'] for row in font_fails]}")
    if any(row["PIXEL_DECISION"] != "PASS" for row in pixel_rows):
        raise RuntimeError("Pixel table contains a non-pass mask result")
    if any(row["DECISION"] != "PASS" for row in manual_rows) or len(manual_rows) != 108:
        raise RuntimeError("Manual glyph ledger is incomplete or non-pass")
    if any(row["REVIEWER_DECISION"] != "PASS" for row in visual_rows) or len(visual_rows) != 64:
        raise RuntimeError("Visual ledger is incomplete or non-pass")
    if any(row["RESULT"] != "PASS" for row in relation_rows + edge_rows):
        raise RuntimeError("A geometry relationship failed")
    if any(row["RESULT"] != "PASS" for row in calibration_rows):
        raise RuntimeError("A low-profile punctuation calibration failed")
    if len(findings) != 1 or findings[0]["ELEMENT_ID"] != "F020_G091":
        raise RuntimeError("The terminal finding set is not the single verified G091 failure")
    final_required_csv = [
        ROOT / "after_font_audit.csv",
        ROOT / "after_pixel_measurements.csv",
        ROOT / "after_overlap_report.csv",
        ROOT / "glyph_id_filename_manifest.csv",
        ROOT / "sa1_findings.csv",
        ROOT / "calibration" / "low_profile_punctuation_calibration.csv",
        ROOT / "ledger" / "glyph_manual_review_ledger.csv",
        ROOT / "ledger" / "visual_harmony_ledger.csv",
        ROOT / "occlusion" / "occlusion_ledger.csv",
        ROOT / "relations" / "text_figure_edge_relations.csv",
        ROOT / "relations" / "text_graphic_relations.csv",
    ]
    unresolved = []
    for path in final_required_csv:
        text = path.read_text(encoding="utf-8")
        if "UNKNOWN" in text or "PENDING" in text:
            unresolved.append(safe_rel(path))
    if unresolved:
        raise RuntimeError(f"Terminal-required table has unresolved marker: {unresolved}")

    expected_png, expected_csv, expected_json, expected_other = expected_paths()
    verdict_path = TERMINAL / "SA1_FINAL_VERDICT.md"
    stop_path = TERMINAL / "WRITE_STOPPED.md"
    manifest_path = TERMINAL / "TERMINAL_MANIFEST.json"
    integrity_path = TERMINAL / "MACHINE_INTEGRITY.json"
    write_text(
        verdict_path,
        "# FIG-P020-01 R6 R111 SA1 final verdict\n\n"
        "## SA1 RESULT: FAIL\n\n"
        "The sole verified figure-gate failure is `F020_G091` (caption CJK `一`): direct R95 page-17 native 300 dpi raw mask has `H_INK_PX=5`, below the revision-111 CJK/fullheight minimum of `30px`. Its 1× original, unique red overlay, mask-only image, 8× nearest triad, and CS016 contact cell are retained. This is not a low-profile-punctuation exception.\n\n"
        "All 108 glyph masks were manually reviewed and are complete/pure; all 45 unordered text-text pairs, 140 text-graphic relations, 12 cross-panel relations, and 10 crop-edge relations passed. The real opaque white return-label ground has a closed pre/ground/final reversal with zero covered return-arrow pixels. Low-profile punctuation calibration passed 7/7. D/E and the four-view font visual harmony ledger passed. Those pass results do not waive the G091 hard threshold.\n\n"
        "## Required route\n\n"
        "Route only to SA2. Suggested fix: replace or rework the one-stroke caption wording/typography so every retained CJK glyph reaches `H_INK_PX>=30` at native 300 dpi while retaining `effective_pt>=9.5`, clearance, and visual harmony. Rebuild the frozen candidate and regenerate a wholly new audit. No SA3 handoff is authorized from this FAIL verdict.\n",
    )
    write_text(
        stop_path,
        "# WRITE_STOPPED\n\n"
        "SA1 R111 evidence generation is sealed after the terminal integrity check. No further files in this evidence root may be altered by this reviewer. The outcome is FAIL and the only authorized next route is SA2 remediation followed by new evidence.\n",
    )
    pre_manifest = {
        "figure_uid": "FIG-P020-01",
        "audit_round": "STRICT_R6_REQUAL_R111_SA1_20260824",
        "schema_revision": 111,
        "frozen_pdf": "R95 main_full.pdf physical page 17",
        "figure_gate_result": "FAIL",
        "evidence_integrity_result": "PENDING_FINAL_OPEN",
        "single_figure_gate_failure": {
            "element_id": "F020_G091",
            "char": "一",
            "h_ink_px": 5,
            "threshold_px": 30,
            "route": "SA2_ONLY",
        },
        "nonterminal_superseded_inputs": ["after_font_audit_precalibration.csv"],
        "expected_png_count": len(expected_png),
        "expected_csv_count": len(expected_csv),
        "expected_json_count": len(expected_json),
        "expected_other_count": len(expected_other),
        "expected_files": sorted(expected_png | expected_csv | expected_json | expected_other),
    }
    write_json(manifest_path, pre_manifest)
    # The fixed expected set includes the integrity record itself.  Create a
    # parseable, explicitly nonterminal placeholder before the first all-file
    # reopening pass; it is overwritten by the final PASS record below.
    write_json(
        integrity_path,
        {
            "result": "PROVISIONAL_NOT_TERMINAL",
            "scope": "bootstrap record required only for the first complete reopen",
            "figure_gate_result": "FAIL",
        },
    )
    # The paths now exist; first full reopen validates every fixed expected file.
    opened = open_and_validate(expected_png, expected_csv, expected_json, expected_other)
    ads = ads_count()
    if ads != 0:
        raise RuntimeError(f"ADS count is nonzero: {ads}")
    integrity = {
        "result": "PASS",
        "scope": "evidence completeness and parse/open integrity; distinct from figure gate",
        "figure_gate_result": "FAIL",
        "expected_actual_match": True,
        "zero_byte_files": 0,
        "ads_count": ads,
        "unsafe_filename_count": 0,
        "glyph_count": 108,
        "manual_glyph_ledger_rows": len(manual_rows),
        "visual_harmony_rows": len(visual_rows),
        "text_text_pair_count": 45,
        "text_graphic_matrix_count": 140,
        "cross_panel_pair_count": 12,
        "text_figure_edge_count": 10,
        "font_failures": ["F020_G091"],
        "relation_failures": 0,
        "pixel_mask_failures": 0,
        "low_profile_calibration_failures": 0,
        "opening_summary": opened,
    }
    write_json(integrity_path, integrity)
    # Re-open every expected byte once more, now including this integrity file.
    opened_final = open_and_validate(expected_png, expected_csv, expected_json, expected_other)
    pre_manifest["evidence_integrity_result"] = "PASS"
    pre_manifest["opening_summary"] = {
        key: opened_final[key]
        for key in (
            "expected_file_count",
            "actual_file_count",
            "expected_png_count",
            "opened_png_count",
            "expected_csv_count",
            "parsed_csv_count",
            "expected_json_count",
            "parsed_json_count",
            "expected_other_count",
            "opened_other_count",
        )
    }
    write_json(manifest_path, pre_manifest)
    # Confirm the just-updated manifest remains parseable and the whole set is unchanged.
    open_and_validate(expected_png, expected_csv, expected_json, expected_other)
    print(json.dumps({"integrity": "PASS", "figure_gate": "FAIL", "files": opened_final["actual_file_count"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
