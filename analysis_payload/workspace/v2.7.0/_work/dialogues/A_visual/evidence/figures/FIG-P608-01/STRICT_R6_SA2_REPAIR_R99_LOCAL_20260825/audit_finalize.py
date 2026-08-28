#!/usr/bin/env python3
"""Bottom-up, write-once finalizer for FIG-P608-01 SA2 R6 local evidence.

This program validates already completed manual ledgers.  It never invents a
manual PASS row and never treats the local wrapper as an official candidate.
Use ``--preflight`` first; the sealing invocation requires
``--attest-manual-ledgers-complete`` and writes WRITE_STOPPED last.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
HANDOFF_ID = "A-R99-P608-SA2-NARROW-20260825"
SA2_ROUTE = "SA2=gpt-5.6-sol/max"
PASS_CODE = "LOCAL_SA2_PASS_AWAIT_OFFICIAL_CANDIDATE_AND_FRESH_SA1"
FAIL_CODE = "LOCAL_SA2_FAIL"
BASELINE_HEAD = "e392bd8e5f37dfd49f071f7251c281d46bb68ffd"
ALLOWED_SOURCE = "src/绘图源码/第05册_采样方法主题模型与图排序/V5-C03/fig_v5_c03_trace_running_mean.tex"
EXACT_INSERTIONS = (
    "+  ylabel style={rotate=-90,anchor=east,at={(axis description cs:-0.12,0.5)}},",
)
BASE_VIEWS = (
    "full_page_200dpi.png",
    "figure_crop_300dpi.png",
    "standalone_300dpi.png",
    "grayscale_300dpi.png",
)
COLOUR_VIEWS = (
    "colorblind_protanopia_300dpi.png",
    "colorblind_deuteranopia_300dpi.png",
    "colorblind_tritanopia_300dpi.png",
)
ALL_VIEWS = BASE_VIEWS + COLOUR_VIEWS
NON_ILLEGAL_CLASSES = {
    "INTRA_PARENT_TYPOGRAPHY",
    "MATH_RULE_INTRA_PARENT",
    "INTENTIONAL_SAME_SERIES",
}


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open("r", newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def read_json(name: str) -> dict[str, Any]:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def write_json(name: str, value: object) -> None:
    (ROOT / name).write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def exists_rel(value: str) -> bool:
    return bool(value) and (ROOT / value).is_file()


def truthy(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes", "pass"}


def float_or_none(value: object) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def norm(value: str) -> str:
    return value.replace("\\", "/")


def same_value(left: object, right: object) -> bool:
    return str(left).strip() == str(right).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--attest-manual-ledgers-complete", action="store_true")
    args = parser.parse_args()
    if args.preflight and args.attest_manual_ledgers_complete:
        raise RuntimeError("choose preflight or sealing, not both")
    if not args.preflight and not args.attest_manual_ledgers_complete:
        raise RuntimeError("use --preflight or --attest-manual-ledgers-complete")
    if (ROOT / "WRITE_STOPPED").exists():
        raise RuntimeError("WRITE_STOPPED exists; post-finalization writes are forbidden")

    preliminary = read_json("metadata/preliminary_machine_summary.json")
    freeze = read_json("LOCAL_CANDIDATE_FREEZE.json")
    build = read_json("BUILD_VALIDATION.json")
    source_scope = read_json("SOURCE_SCOPE_VALIDATION.json")
    attestation = read_json("MANUAL_REVIEW_ATTESTATION.json")

    objects = read_csv("object_ledger.csv")
    chars = read_csv("character_mapping.csv")
    paths = read_csv("drawing_path_inventory.csv")
    math_rows = read_csv("math_rule_ledger.csv")
    font_rows = read_csv("after_font_audit.csv")
    source_font_coverage = read_csv("source_font_coverage.csv")
    source_scale_scan = read_csv("source_scale_control_scan.csv")
    pixel_rows = read_csv("after_pixel_measurements.csv")
    pairs = read_csv("after_overlap_report.csv")
    contacts = read_csv("contact_sheet_ledger.csv")
    cal_rows = read_csv("punctuation_calibration.csv")
    semantic_rows = read_csv("semantic_consistency.csv")
    role_template = read_csv("role_panel_template.csv")
    manual = read_csv("manual_review_ledger.csv")
    critical_ledger = read_csv("critical_pair_review_ledger.csv")
    view_ledger = read_csv("visual_view_ledger.csv")
    role_ledger = read_csv("role_panel_ledger.csv")

    object_ids = [row["OBJECT_ID"] for row in objects]
    object_set = set(object_ids)
    glyph_ids = {row["OBJECT_ID"] for row in objects if row["TYPE"] == "GLYPH"}
    path_ids = {row["OBJECT_ID"] for row in objects if row["TYPE"] != "GLYPH"}
    char_ids = {row["ELEMENT_ID"] for row in chars}
    expected_pairs = len(objects) * (len(objects) - 1) // 2
    pair_ids = [row["PAIR_ID"] for row in pairs]
    pair_keys = [tuple(sorted((row["OBJECT_A"], row["OBJECT_B"]))) for row in pairs]
    contacts_by_id = {row["OBJECT_ID"]: row for row in contacts}
    pixels_by_id = {row["ELEMENT_ID"]: row for row in pixel_rows}
    cal_by_id = {row["CALIBRATION_ID"]: row for row in cal_rows}
    manual_by_id = {row["OBJECT_ID"]: row for row in manual}
    critical_pairs = [row for row in pairs if truthy(row["CRITICAL"])]
    critical_pair_ids = {row["PAIR_ID"] for row in critical_pairs}
    critical_by_id = {row["PAIR_ID"]: row for row in critical_ledger}
    views_by_name = {row["VIEW"]: row for row in view_ledger}
    role_key = lambda row: (row["PANEL"], row["ROLE"])
    role_templates = {role_key(row): row for row in role_template}
    role_manual = {role_key(row): row for row in role_ledger}

    pdf = Path(freeze["pdf"])
    source = Path(freeze["source"])
    wrapper = Path(freeze["wrapper"])
    checks: dict[str, bool] = {}

    checks["handoff_and_route_exact"] = (
        preliminary.get("handoff_id") == HANDOFF_ID
        and freeze.get("handoff_id") == HANDOFF_ID
        and attestation.get("handoff_id") == HANDOFF_ID
        and freeze.get("sa2_route") == SA2_ROUTE
        and attestation.get("sa2_route") == SA2_ROUTE
    )
    checks["frozen_local_identity_current"] = all((pdf.is_file(), source.is_file(), wrapper.is_file())) and (
        pdf.stat().st_size == int(freeze["pdf_bytes"])
        and source.stat().st_size == int(freeze["source_bytes"])
        and wrapper.stat().st_size == int(freeze["wrapper_bytes"])
        and sha256(pdf) == str(freeze["pdf_sha256"]).upper()
        and sha256(source) == str(freeze["source_sha256"]).upper()
        and sha256(wrapper) == str(freeze["wrapper_sha256"]).upper()
    )
    candidate = preliminary["candidate"]
    checks["extractor_used_frozen_local_pdf"] = (
        Path(candidate["pdf"]).resolve() == pdf.resolve()
        and int(candidate["bytes"]) == int(freeze["pdf_bytes"])
        and str(candidate["sha256"]).upper() == str(freeze["pdf_sha256"]).upper()
        and int(candidate["physical_page"]) == 1
        and candidate["printed_page"] == "LOCAL_WRAPPER_FIG_32.8"
    )
    checks["build_local_wrapper_pass"] = (
        int(build.get("exit_code", -1)) == 0
        and int(build.get("pdf_page_count", -1)) == 1
        and truthy(build.get("a4_page_size"))
        and int(build.get("hard_diagnostic_count", -1)) == 0
        and int(build.get("undefined_control_sequence_count", -1)) == 0
        and int(build.get("overfull_count", -1)) == 0
        and int(build.get("underfull_count", -1)) == 0
        and int(build.get("root_cache_line_count", 0)) >= 1
        and len(build.get("failed_cache_bootstrap_attempts", [])) == 4
        and all(int(item.get("exit_code", -1)) == 12 for item in build.get("failed_cache_bootstrap_attempts", []))
        and build.get("tex_processes_before") == "NONE"
        and build.get("build_scope") == "one_page_local_wrapper"
    )
    changed_paths = [norm(str(item)) for item in source_scope.get("changed_paths", [])]
    checks["source_scope_exact"] = (
        source_scope.get("baseline_head") == BASELINE_HEAD
        and source_scope.get("current_head") == BASELINE_HEAD
        and changed_paths == [ALLOWED_SOURCE]
        and int(source_scope.get("insertions", -1)) == 1
        and int(source_scope.get("deletions", -1)) == 0
        and tuple(source_scope.get("exact_inserted_lines", [])) == EXACT_INSERTIONS
        and truthy(source_scope.get("only_allowed_source_changed"))
        and not truthy(source_scope.get("common_files_changed"))
        and not truthy(source_scope.get("other_source_files_changed"))
    )

    checks["rawdict_to_texttrace_closed"] = (
        int(preliminary["rawdict_glyph_count"])
        == int(preliminary["texttrace_matched_count"])
        == len(glyph_ids)
        and int(preliminary["texttrace_unmatched_count"]) == 0
    )
    checks["object_universe_recomputed"] = (
        len(object_ids) == len(object_set)
        and len(objects) == int(preliminary["visible_foreground_object_count"])
        and len(glyph_ids) == int(preliminary["glyph_count"])
        and len(path_ids) == int(preliminary["path_count"])
        and not preliminary["empty_final_masks"]
    )
    checks["ordinary_safe_filenames"] = all(
        re.fullmatch(r"[a-z0-9_]+", row["SAFE_FILENAME"]) is not None
        and ":" not in row["SAFE_FILENAME"]
        for row in objects
    )
    checks["all_object_artifacts_exist"] = all(
        exists_rel(row["FINAL_RAW_MASK"])
        and exists_rel(row["PRE_RAW_MASK"])
        and exists_rel(row["NATIVE1X"])
        and exists_rel(row["NEAREST8X"])
        and int(row["FINAL_VISIBLE_INK_PX"]) > 0
        for row in objects
    )
    checks["character_mapping_closed"] = (
        glyph_ids == char_ids
        and len(chars) == len(glyph_ids)
        and all(row["STATUS"] == "MAPPED" for row in chars)
    )
    foreground_paths = {
        row["OBJECT_ID"]
        for row in paths
        if truthy(row["PAIR_UNIVERSE_INCLUDED"])
    }
    checks["all_foreground_paths_accounted"] = (
        foreground_paths == path_ids
        and all(
            row["STATUS"] == "PASS" and int(row["FINAL_VISIBLE_INK_PX"]) > 0
            for row in paths
            if truthy(row["PAIR_UNIVERSE_INCLUDED"])
        )
        and all(
            row["STATUS"] == "ACCOUNTED_BACKGROUND"
            for row in paths
            if row["TYPE"] == "BACKGROUND_PATTERN"
        )
    )
    checks["math_rules_accounted"] = bool(math_rows) and all(
        row["STATUS"] == "PASS"
        and truthy(row["PAIR_UNIVERSE_INCLUDED"])
        and row["RULE_ID"] in path_ids
        for row in math_rows
    )

    checks["pair_universe_complete"] = (
        len(pairs) == expected_pairs
        and int(preliminary["pair_count"]) == expected_pairs
        and int(preliminary["expected_pair_count"]) == expected_pairs
        and len(pair_ids) == len(set(pair_ids)) == expected_pairs
        and len(pair_keys) == len(set(pair_keys)) == expected_pairs
        and all(a in object_set and b in object_set and a != b for a, b in pair_keys)
    )
    checks["all_pairs_pass"] = bool(pairs) and all(row["PAIR_PASS"] == "PASS" for row in pairs)
    illegal_pairs = [row for row in pairs if row["RELATION_CLASS"] not in NON_ILLEGAL_CLASSES]
    final_illegal_overlap_pixels = sum(int(row["FINAL_VISIBLE_OVERLAP_PX"]) for row in illegal_pairs)
    pre_candidate_pixel_pair_sum = sum(int(row["PRE_OCCLUSION_SHARED_PX"]) for row in illegal_pairs)
    checks["zero_final_illegal_overlap"] = final_illegal_overlap_pixels == 0
    checks["zero_clip"] = int(preliminary["clip_pixel_count_page_edge"]) == 0
    checks["text_crop_edge_clearance"] = float(preliminary["crop_edge_min_text_px"]) >= 6.0

    checks["source_font_pass"] = bool(font_rows) and all(
        row["PASS_FAIL"] == "PASS" and float(row["EFFECTIVE_PT"]) >= 9.5
        for row in font_rows
    )
    checks["source_font_control_coverage"] = bool(source_font_coverage) and all(
        row["STATUS"] in {"PASS", "ALLOWED_NATURAL_SCRIPT"}
        for row in source_font_coverage
    )
    checks["source_scale_control_pass"] = bool(source_scale_scan) and all(
        row["STATUS"] == "PASS" for row in source_scale_scan
    )
    checks["pixel_height_pass"] = bool(pixel_rows) and all(
        row["PASS_FAIL"] == "PASS" for row in pixel_rows
    )
    checks["pixel_rows_cover_all_glyphs"] = (
        glyph_ids.issubset(set(pixels_by_id))
        and set(pixels_by_id) - glyph_ids
        == {"MATH_OPERATOR_EQ_WARMUP", "MATH_OPERATOR_EQ_RETAINED"}
    )
    checks["punctuation_calibrated"] = all(
        row["SCRIPT_CLASS"] != "LOW_PROFILE_PUNCTUATION"
        or (
            row["CALIBRATION_ID"] in cal_by_id
            and abs(int(row["H_INK_PX"]) - int(cal_by_id[row["CALIBRATION_ID"]]["H_INK_PX"])) <= 2
            and abs(int(row["INK_AREA_PX"]) - int(cal_by_id[row["CALIBRATION_ID"]]["INK_AREA_PX"]))
            <= max(8, math.ceil(0.15 * int(cal_by_id[row["CALIBRATION_ID"]]["INK_AREA_PX"])))
        )
        for row in pixel_rows
    )
    checks["calibration_artifacts_exist"] = bool(cal_rows) and all(
        exists_rel(row["PDF"])
        and exists_rel(row["PNG_300DPI"])
        and exists_rel(row["RAW_MASK"])
        and exists_rel(row["NATIVE1X"])
        and exists_rel(row["NEAREST8X"])
        for row in cal_rows
    )
    checks["same_class_d_ratio_pass"] = bool(role_template) and all(
        row["D_RATIO_STATUS"] == "PASS" for row in role_template
    )
    checks["role_e_ratio_pass"] = bool(role_template) and all(
        row["E_RATIO_STATUS"] == "PASS"
        and row["CROSS_PANEL_STATUS"] in {"PASS", "N/A"}
        for row in role_template
    )
    checks["semantic_consistency_pass"] = bool(semantic_rows) and all(
        truthy(row["PASS"]) for row in semantic_rows
    )

    checks["required_views_exist"] = all((ROOT / name).is_file() for name in ALL_VIEWS)
    checks["text_measurement_overlay_exists"] = (
        ROOT / "after_text_measurement_overlay_300dpi.png"
    ).is_file()
    checks["contact_coverage_closed"] = (
        set(contacts_by_id) == object_set
        and len(contacts) == len(objects)
        and all(exists_rel(row["NATIVE1X"]) and exists_rel(row["NEAREST8X"]) for row in contacts)
    )

    checks["manual_object_review_closed"] = (
        set(manual_by_id) == object_set
        and len(manual) == len(objects)
        and all(
            row["REVIEWER"] == "SA2_R6_LOCAL"
            and row["SHEET"] == contacts_by_id[object_id]["SHEET"]
            and row["CELL"] == contacts_by_id[object_id]["CELL"]
            and truthy(row["ORIGINAL_MATCH"])
            and truthy(row["OVERLAY_COMPLETE"])
            and truthy(row["MASK_ONLY_PURE"])
            and int(row["MISSING_STROKE_PX"]) == 0
            and int(row["FOREIGN_PIXEL_PX"]) == 0
            and row["DECISION"] == "PASS"
            and bool(row["NOTE"].strip())
            for object_id, row in manual_by_id.items()
        )
    )
    checks["manual_metric_gate_consistent"] = all(
        row.get("METRIC_GATE")
        == (pixels_by_id[object_id]["PASS_FAIL"] if object_id in pixels_by_id else "PATH_NOT_PIXEL_GATE")
        for object_id, row in manual_by_id.items()
    )
    checks["critical_pair_review_closed"] = (
        set(critical_by_id) == critical_pair_ids
        and len(critical_ledger) == len(critical_pairs)
        and all(
            row["REVIEWER"] == "SA2_R6_LOCAL"
            and truthy(row["RAW_A_MATCH"])
            and truthy(row["RAW_B_MATCH"])
            and truthy(row["INTERSECTION_MATCH"])
            and row["DECISION"] == "PASS"
            and exists_rel(row["NATIVE1X"])
            and exists_rel(row["NEAREST8X"])
            and bool(row["NOTE"].strip())
            for row in critical_ledger
        )
    )
    checks["visual_views_manually_pass"] = (
        set(views_by_name) == set(ALL_VIEWS)
        and len(view_ledger) == len(ALL_VIEWS)
        and all(
            row["REVIEWER"] == "SA2_R6_LOCAL"
            and truthy(row["OPENED"])
            and row["PASS"] == "PASS"
            and bool(row["NOTE"].strip())
            for row in view_ledger
        )
    )
    checks["role_panel_manual_pass"] = (
        set(role_manual) == set(role_templates)
        and len(role_ledger) == len(role_template)
        and all(
            row["REVIEWER"] == "SA2_R6_LOCAL"
            and row["VISUAL_HARMONY"] == "PASS"
            and all(
                same_value(row[field], role_templates[key][field])
                for field in (
                    "MEDIAN_H_INK_PX", "SOURCE_EFFECTIVE_PT", "BASE_EFFECTIVE_PT",
                    "SOURCE_ROLE_RATIO", "E_RANGE", "D_RATIO_STATUS", "E_RATIO_STATUS",
                    "CROSS_PANEL_ROLE_RATIO", "CROSS_PANEL_STATUS",
                )
            )
            and bool(row["NOTE"].strip())
            for key, row in role_manual.items()
        )
    )

    expected_sheet_files = sorted({row["SHEET"] for row in contacts if row["SHEET"] != "INDIVIDUAL"})
    expected_individual_files = sorted({
        value
        for row in contacts
        if row["SHEET"] == "INDIVIDUAL"
        for value in (row["NATIVE1X"], row["NEAREST8X"])
    })
    expected_critical_files = sorted({
        value
        for row in critical_pairs
        for value in (row["NATIVE1X"], row["NEAREST8X"])
    })
    checks["manual_open_attestation_closed"] = (
        attestation.get("reviewer") == "SA2_R6_LOCAL"
        and sorted(attestation.get("contact_sheets_opened", [])) == expected_sheet_files
        and sorted(attestation.get("individual_object_files_opened", [])) == expected_individual_files
        and sorted(attestation.get("critical_pair_files_opened", [])) == expected_critical_files
        and sorted(attestation.get("critical_pair_ids_reviewed", [])) == sorted(critical_pair_ids)
        and sorted(attestation.get("required_views_opened", [])) == sorted(ALL_VIEWS)
        and truthy(attestation.get("overlay_opened"))
        and int(attestation.get("object_rows_individually_ledgered", -1)) == len(objects)
        and int(attestation.get("critical_rows_individually_ledgered", -1)) == len(critical_pairs)
        and truthy(attestation.get("manual_review_complete"))
    )

    design_pixel_failures = [row for row in pixel_rows if row["PASS_FAIL"] != "PASS"]
    required_clearances = [
        value
        for row in pairs
        if row["REQUIRED_CLEARANCE_PX"] != "N/A"
        for value in [float_or_none(row["MIN_CLEARANCE_PX"])]
        if value is not None
    ]
    result = PASS_CODE if all(checks.values()) else FAIL_CODE
    summary = {
        "handoff_id": HANDOFF_ID,
        "sa2_route": SA2_ROUTE,
        "N": len(objects),
        "glyph_rows": len(glyph_ids),
        "path_rows": len(path_ids),
        "C_N_2_expected": expected_pairs,
        "pair_rows": len(pairs),
        "critical_pair_rows": len(critical_pairs),
        "manual_object_rows": len(manual),
        "design_pixel_failure_ids": [row["ELEMENT_ID"] for row in design_pixel_failures],
        "pre_occlusion_candidate_pixel_pair_sum": pre_candidate_pixel_pair_sum,
        "final_illegal_overlap_pixels": final_illegal_overlap_pixels,
        "clip_pixel_count": int(preliminary["clip_pixel_count_page_edge"]),
        "min_required_class_clearance_px": min(required_clearances) if required_clearances else "N/A",
        "checks": checks,
        "result": result,
    }
    if args.preflight:
        print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
        return

    sealed_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    terminal = dict(summary)
    terminal.update({
        "terminal_recalculation_time": sealed_at,
        "local_only": True,
        "official_candidate_reviewed": False,
        "fresh_sa1_started": False,
        "sa3_started": False,
        "write_stopped_next": True,
    })

    # Required seal order: terminal first, then manifest/report/result/handoff,
    # and WRITE_STOPPED strictly last after an mtime separation.
    write_json("MACHINE_TERMINAL_RECALC.json", terminal)
    manifest = {
        "handoff_id": HANDOFF_ID,
        "sa2_route": SA2_ROUTE,
        "scope": "FIG-P608-01 local one-page wrapper repair verification only",
        "frozen_local_candidate": freeze,
        "object_universe": {
            "N": len(objects), "glyphs": len(glyph_ids), "paths": len(path_ids),
            "pairs": len(pairs), "expected_pairs": expected_pairs,
        },
        "checks": checks,
        "design_failure_ids": [row["ELEMENT_ID"] for row in design_pixel_failures],
        "result": result,
        "official_candidate_required": True,
        "fresh_sa1_required": True,
        "not_root_acceptance": True,
        "terminal": "MACHINE_TERMINAL_RECALC.json",
    }
    write_json("manifest.json", manifest)

    gate_rows = "\n".join(
        f"| {name} | {'PASS' if verdict else 'FAIL'} |"
        for name, verdict in checks.items()
    )
    failure_rows = "\n".join(
        f"- `{row['ELEMENT_ID']}`: H={row['H_INK_PX']}px, threshold={row['PIXEL_THRESHOLD']}px, {row['REASON']}"
        for row in design_pixel_failures
    ) or "- None."
    report = f"""# FIG-P608-01 SA2 R6 local repair verification

HANDOFF_ID: `{HANDOFF_ID}`  
ROUTE: `{SA2_ROUTE}`  
RESULT: `{result}`

This package verifies the single authorized source repair against a frozen,
one-page local wrapper PDF. It is not an official-candidate review and does
not assert `A_LOCAL_PASS`. A new official candidate and fresh isolated SA1
remain mandatory; SA1 and SA3 were not started by this task.

## Source and local candidate

- Baseline/current HEAD: `{BASELINE_HEAD}`.
- Sole source change: `{ALLOWED_SOURCE}`; 1 insertion, 0 deletions.
- Exact insertion: `{EXACT_INSERTIONS[0]}`.
- Frozen local PDF SHA-256: `{freeze['pdf_sha256']}`; bytes: {freeze['pdf_bytes']}.
- Source SHA-256: `{freeze['source_sha256']}`; wrapper SHA-256: `{freeze['wrapper_sha256']}`.
- Four earlier bootstrap attempts exited 12 at luaotfload cache-path initialization before the P608 source was entered; they produced no candidate PDF and are retained as build history.
- The successful build directly invoked LuaLaTeX from the worktree merge-book directory with one absolute R6 `texcache` shared by TEXMFVAR/TEXMFCACHE/TEXMFCONFIG; latexmk and the temporary junction were not used for the successful candidate.
- Four rendered layout trials were rejected before freezing: direct r1 showed that `rotate=0` did not cancel PGFPlots' default +90 rotation and collided with y ticks; direct r2 exposed rotated-local `xshift` behavior; direct r3 retained a 0.80pt bottom-label/tick overlap; direct r4 cleared position geometry but the full raw-mask audit proved both natural-script t glyphs were still 10px. Direct r5 proved the `rotate=-90` layout but was rejected because the evidence wrapper redundantly forced Noto Sans SC instead of the official `statlearnbook` Noto Serif SC main-font route. Direct r6 removes only that evidence-wrapper override and is the frozen local candidate.

## Bottom-up denominator and findings

- Visible object universe: N={len(objects)} ({len(glyph_ids)} glyphs + {len(path_ids)} foreground paths).
- Complete unordered denominator: C(N,2)={expected_pairs}; emitted pair rows={len(pairs)}.
- Critical pairs opened and individually reviewed: {len(critical_pairs)}.
- Final illegal overlap pixels: {final_illegal_overlap_pixels}; clip pixels: {preliminary['clip_pixel_count_page_edge']}.
- Minimum applicable class clearance: {min(required_clearances) if required_clearances else 'N/A'}px.
- Design pixel failures: {len(design_pixel_failures)}.

## Gate matrix

| Gate | Verdict |
|---|---|
{gate_rows}

## Design failures

{failure_rows}

## Goal §9.2.1 routing matrix

| Stage | Model / reasoning | State |
|---|---|---|
| SA1 | NOT_RUN_LOCAL_SA2 | Awaiting official candidate and fresh isolated review |
| SA2 | gpt-5.6-sol / max / escalated=false | {result} |
| SA3 | NOT_RUN | Not started |

## Terminal boundary

`MACHINE_TERMINAL_RECALC.json` is the bottom-up machine result. The manifest,
this report, result token, and handoff report follow it. `WRITE_STOPPED` is the
strictly newest marker and no evidence writes are permitted afterward.
"""
    (ROOT / "after_visual_acceptance.md").write_text(report, encoding="utf-8")
    (ROOT / "RESULT.txt").write_text(result + "\n", encoding="utf-8")
    write_json("HANDOFF_REPORT.json", {
        "handoff_id": HANDOFF_ID,
        "sa2_route": SA2_ROUTE,
        "result": result,
        "local_only": True,
        "official_candidate_required": True,
        "fresh_isolated_sa1_required": True,
        "sa1_started": False,
        "sa3_started": False,
        "do_not_claim": "A_LOCAL_PASS",
        "sealed_at": sealed_at,
    })
    time.sleep(1.5)
    (ROOT / "WRITE_STOPPED").write_text(
        f"{datetime.now(timezone.utc).astimezone().isoformat(timespec='seconds')}\n"
        f"{result}\n{HANDOFF_ID}\n{SA2_ROUTE}\n"
        "terminal -> manifest/report/result/handoff -> WRITE_STOPPED; zero writes permitted after this marker.\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
