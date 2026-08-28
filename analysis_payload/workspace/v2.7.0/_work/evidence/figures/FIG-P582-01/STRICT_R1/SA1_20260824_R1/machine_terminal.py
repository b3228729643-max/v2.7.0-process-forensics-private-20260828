from __future__ import annotations

"""Final machine consistency check for the active FIG-P582-01 SA1 evidence set.

This script deliberately distinguishes evidence-package closure from the figure
verdict. A closed package may still (and here does) yield FAIL→SA2 because a
hard visual/measurement gate is false.
"""

import csv
import json
import math
import os
from collections import Counter
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
ISSUES: list[str] = []
CHECKS: dict[str, dict[str, object]] = {}


def as_text(value: object) -> str:
    return "" if value is None else str(value).strip()


def true(value: object) -> bool:
    return as_text(value).lower() in {"true", "pass", "yes", "1"}


def false(value: object) -> bool:
    return as_text(value).lower() in {"false", "fail", "no", "0"}


def number(value: object) -> float:
    return float(as_text(value))


def relative_path(value: object) -> Path:
    return ROOT / as_text(value).replace("\\", "/")


def record(name: str, passed: bool, detail: object) -> None:
    CHECKS[name] = {"pass": bool(passed), "detail": detail}
    if not passed:
        ISSUES.append(f"{name}: {detail}")


def read_csv(name: str) -> list[dict[str, str]]:
    path = ROOT / name
    if not path.is_file():
        record(f"file::{name}", False, "missing")
        return []
    try:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, strict=True)
            if not reader.fieldnames:
                record(f"csv::{name}", False, "no header")
                return []
            rows = list(reader)
            if any(None in row for row in rows):
                record(f"csv::{name}", False, "row has extra/unmapped columns")
            else:
                record(f"csv::{name}", True, {"rows": len(rows), "columns": len(reader.fieldnames)})
            return rows
    except Exception as exc:  # terminal report must be diagnostic, not silent
        record(f"csv::{name}", False, f"parse error: {exc}")
        return []


def read_json(name: str) -> dict[str, object]:
    path = ROOT / name
    if not path.is_file():
        record(f"file::{name}", False, "missing")
        return {}
    try:
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        record(f"json::{name}", True, "parsed")
        return data
    except Exception as exc:
        record(f"json::{name}", False, f"parse error: {exc}")
        return {}


def count_false(rows: list[dict[str, str]], field: str) -> int:
    return sum(false(row.get(field, "")) for row in rows)


def count_true(rows: list[dict[str, str]], field: str) -> int:
    return sum(true(row.get(field, "")) for row in rows)


def main() -> int:
    # Parse every existing CSV/JSON before writing terminal outputs. This also
    # catches stale diagnostics while allowing the declared superseded raw
    # ledgers to remain parseable forensic records.
    parse_csv_errors: list[str] = []
    parse_json_errors: list[str] = []
    csv_paths = sorted(ROOT.rglob("*.csv"))
    json_paths = sorted(ROOT.rglob("*.json"))
    for path in csv_paths:
        try:
            with path.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.reader(handle, strict=True))
            if not rows or not rows[0]:
                parse_csv_errors.append(str(path.relative_to(ROOT)))
            elif any(row and len(row) != len(rows[0]) for row in rows[1:]):
                parse_csv_errors.append(str(path.relative_to(ROOT)))
        except Exception:
            parse_csv_errors.append(str(path.relative_to(ROOT)))
    for path in json_paths:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            parse_json_errors.append(str(path.relative_to(ROOT)))
    record("all_existing_csv_parseable", not parse_csv_errors,
           {"count": len(csv_paths), "errors": parse_csv_errors})
    record("all_existing_json_parseable", not parse_json_errors,
           {"count": len(json_paths), "errors": parse_json_errors})

    summary = read_json("measurement_summary.json")
    role_summary = read_json("role_actual_hink_summary.json")
    low_summary = read_json("low_profile_calibration/low_profile_calibration_summary.json")

    font = read_csv("after_font_audit.csv")
    pixel = read_csv("after_pixel_measurements.csv")
    objects = read_csv("object_inventory.csv")
    graphics = read_csv("graphic_object_inventory.csv")
    semantic = read_csv("semantic_text_inventory_machine.csv")
    all_pairs = read_csv("all_unordered_pairs.csv")
    overlap = read_csv("after_overlap_report.csv")
    mandatory = read_csv("mandatory_relationships.csv")
    clip = read_csv("clip_report.csv")
    glyph_manifest = read_csv("glyph_file_manifest.csv")
    final_mask_manifest = read_csv("glyph_final_mask_manifest.csv")
    final_mask_integrity = read_csv("glyph_final_mask_integrity.csv")
    final_ledger = read_csv("glyph_final_reviewer_ledger.csv")
    isolation = read_csv("glyph_isolation_ledger.csv")
    low = read_csv("low_profile_punctuation_calibration.csv")
    low_ledger = read_csv("low_profile_reviewer_ledger.csv")
    four_view = read_csv("four_view_reviewer_ledger.csv")
    panel_role = read_csv("panel_role_script_visual_ledger.csv")
    semantic_ledger = read_csv("semantic_reviewer_ledger.csv")
    role_hierarchy = read_csv("role_hierarchy_audit.csv")
    role_e = read_csv("role_e_actual_hink_audit.csv")

    # Objects, semantic text, and complete unordered pair coverage.
    object_ids = [as_text(row.get("OBJECT_ID")) for row in objects]
    text_ids = [as_text(row.get("ELEMENT_ID")) for row in semantic]
    graphic_ids = [as_text(row.get("OBJECT_ID")) for row in graphics]
    object_graphic_ids = {object_id for object_id in object_ids if object_id.startswith("O-G")}
    n_objects = len(objects)
    expected_pairs = math.comb(n_objects, 2) if n_objects >= 2 else 0
    record("object_inventory_unique", len(object_ids) == len(set(object_ids)) == n_objects,
           {"count": n_objects, "unique": len(set(object_ids))})
    record("semantic_inventory_unique", len(text_ids) == len(set(text_ids)) == len(semantic),
           {"count": len(semantic), "unique": len(set(text_ids))})
    record("graphic_inventory_unique", len(graphic_ids) == len(set(graphic_ids)) == len(graphics) == 17
           and set(graphic_ids) == object_graphic_ids,
           {"count": len(graphics), "unique": len(set(graphic_ids)),
            "matches_authoritative_object_inventory": set(graphic_ids) == object_graphic_ids})
    record("object_composition", n_objects == len(semantic) + len(graphics),
           {"all_objects": n_objects, "semantic": len(semantic), "graphics": len(graphics)})
    unsafe_object_names = [as_text(row.get("OBJECT_ID")) for row in objects
                           if not as_text(row.get("SAFE_FILENAME"))
                           or Path(as_text(row.get("SAFE_FILENAME"))).name != as_text(row.get("SAFE_FILENAME"))
                           or any(char in as_text(row.get("SAFE_FILENAME")) for char in "\\/:*?\"<>|")]
    record("object_safe_names", not unsafe_object_names, {"unsafe": unsafe_object_names})

    all_pair_ids = [as_text(row.get("PAIR_ID")) for row in all_pairs]
    overlap_ids = [as_text(row.get("PAIR_ID")) for row in overlap]
    mandatory_ids = [as_text(row.get("PAIR_ID")) for row in mandatory]
    required_ids = {as_text(row.get("PAIR_ID")) for row in all_pairs if true(row.get("REQUIRED_BY_921"))}
    record("all_unordered_pair_formula", len(all_pairs) == expected_pairs and len(set(all_pair_ids)) == expected_pairs,
           {"objects": n_objects, "expected_n_choose_2": expected_pairs,
            "pair_rows": len(all_pairs), "unique_pair_ids": len(set(all_pair_ids))})
    record("after_overlap_complete_pair_coverage", set(overlap_ids) == set(all_pair_ids) and len(overlap) == expected_pairs,
           {"after_overlap_rows": len(overlap), "all_pair_rows": len(all_pairs)})
    record("mandatory_relationship_coverage", set(mandatory_ids) == required_ids and len(mandatory) == len(required_ids),
           {"mandatory_rows": len(mandatory), "required_pair_count": len(required_ids)})

    pair_failures = [row for row in overlap if as_text(row.get("PASS_FAIL")).upper() == "FAIL"]
    critical_rows = [row for row in overlap if true(row.get("CRITICAL_OR_FAILURE"))]
    critical_missing_packages: list[str] = []
    for row in critical_rows:
        package = relative_path(row.get("ROI_PACKAGE"))
        if not as_text(row.get("ROI_PACKAGE")) or not package.is_dir():
            critical_missing_packages.append(as_text(row.get("PAIR_ID")))
    record("critical_failure_package_paths", not critical_missing_packages,
           {"critical_or_failure_count": len(critical_rows), "missing": critical_missing_packages})

    p0717 = [row for row in overlap if as_text(row.get("PAIR_ID")) == "P0717"]
    p0717_ok = (
        len(p0717) == 1
        and as_text(p0717[0].get("OBJECT_A")) == "E014"
        and as_text(p0717[0].get("OBJECT_B")) == "E016"
        and number(p0717[0].get("OVERLAP_PIXEL_COUNT")) == 3
        and number(p0717[0].get("MIN_CLEARANCE_PX")) == 0
        and number(p0717[0].get("REQUIRED_CLEARANCE_PX")) == 4
        and as_text(p0717[0].get("PASS_FAIL")).upper() == "FAIL"
    )
    record("P0717_real_relation_failure", p0717_ok,
           p0717[0] if p0717 else "missing")
    p0717_dir = ROOT / "roi_packages_r2_geometry_isolated" / "P0717_E014_E016"
    p0717_expected = [
        "original_raw_1x.png", "mask_A_1x.png", "mask_B_1x.png", "intersection_1x.png", "overlay_1x.png",
        "original_raw_8x_nearest.png", "mask_A_8x_nearest.png", "mask_B_8x_nearest.png",
        "intersection_8x_nearest.png", "overlay_8x_nearest.png", "package_manifest.json",
    ]
    record("P0717_native_and_8x_package_complete", all((p0717_dir / name).is_file() for name in p0717_expected),
           {"package": str(p0717_dir.relative_to(ROOT)),
            "missing": [name for name in p0717_expected if not (p0717_dir / name).is_file()]})

    # Font/pixel and revision-111 low-profile recalculation.
    pixel_glyph_rows = [row for row in pixel if as_text(row.get("LEVEL")).upper() == "GLYPH"]
    source_font_fail = count_false(font, "SOURCE_FONT_PASS")
    pixel_fail = count_false(pixel_glyph_rows, "PIXEL_PASS")
    overall_glyph_gate_fail = sum(as_text(row.get("PASS_FAIL")).upper() == "FAIL" for row in pixel_glyph_rows)
    pixel_source_floor_fail = count_false(pixel_glyph_rows, "FONT_PASS")
    low_rows = [row for row in pixel_glyph_rows if true(row.get("LOW_PROFILE_PUNCTUATION"))]
    low_total_fail = count_false(low, "LOW_PROFILE_TOTAL_GATE_PASS")
    low_calibration_fail = count_false(low, "CALIBRATION_PASS")
    low_font_floor_fail = count_false(low, "SOURCE_EFFECTIVE_PT_PASS")
    record("font_and_pixel_row_coverage", len(font) == len(semantic)
           and len(pixel_glyph_rows) == len(glyph_manifest)
           and len(pixel) == len(font) + len(glyph_manifest),
           {"font_elements": len(font), "semantic_elements": len(semantic),
            "after_pixel_total_rows": len(pixel), "pixel_glyphs": len(pixel_glyph_rows),
            "manifest_glyphs": len(glyph_manifest)})
    record("revision111_low_profile_coverage", len(low) == len(low_rows) == len(low_ledger) == 21,
           {"calibration_rows": len(low), "pixel_low_profile_rows": len(low_rows), "manual_rows": len(low_ledger)})
    record("revision111_low_profile_gate_field", all(as_text(row.get("LOW_PROFILE_TOTAL_GATE_PASS")) for row in low),
           "counted from LOW_PROFILE_TOTAL_GATE_PASS; no STATUS column is used")
    record("revision111_low_profile_counts", low_calibration_fail == 2 and low_font_floor_fail == 11 and low_total_fail == 13,
           {"calibration_fail": low_calibration_fail, "source_font_floor_fail": low_font_floor_fail,
            "total_gate_fail": low_total_fail})
    low_manual_allowed = {"CALIBRATION_FAIL", "CALIBRATION_PASS_FONT_FAIL", "PASS_LOCAL"}
    low_manual_counts = Counter(as_text(row.get("MANUAL_DECISION")) for row in low_ledger)
    record("low_profile_manual_ledger_closed",
           all(as_text(row.get(field)) for row in low_ledger for field in
               ("REVIEWER", "GLYPH_ID", "NATIVE_1X_OPENED", "NEAREST_8X_OPENED", "MANUAL_DECISION", "NOTE"))
           and all(as_text(row.get("MANUAL_DECISION")) in low_manual_allowed for row in low_ledger),
           {"rows": len(low_ledger), "manual_decision_counts": dict(low_manual_counts)})

    # Active final glyph evidence only. The older raw ledgers are checked only
    # for parseability and declared supersession, never used in final counts.
    expected_glyph_ids = {as_text(row.get("GLYPH_ID")) for row in glyph_manifest}
    final_ledger_ids = {as_text(row.get("GLYPH_ID")) for row in final_ledger}
    final_mask_ids = {as_text(row.get("GLYPH_ID")) for row in final_mask_manifest}
    final_integrity_ids = {as_text(row.get("GLYPH_ID")) for row in final_mask_integrity}
    record("final_glyph_id_coverage", len(expected_glyph_ids) == 139
           and len(final_ledger) == len(final_mask_manifest) == len(final_mask_integrity) == 139
           and final_ledger_ids == final_mask_ids == final_integrity_ids == expected_glyph_ids,
           {"expected": len(expected_glyph_ids), "final_ledger_rows": len(final_ledger),
            "final_ledger_unique": len(final_ledger_ids), "final_mask_manifest_rows": len(final_mask_manifest),
            "final_integrity_rows": len(final_mask_integrity)})
    final_fields = (
        "REVIEWER", "SHEET", "CELL", "GLYPH_ID", "ELEMENT_ID", "CHAR", "FINAL_CONTACT_SHEET",
        "FINAL_1X_ORIGINAL", "FINAL_1X_TARGET_OVERLAY", "FINAL_1X_MASK_ONLY", "FINAL_8X_REVIEW_EVIDENCE",
        "ORIGINAL_MATCH", "OVERLAY_COMPLETE", "MASK_ONLY_PURE", "MISSING_STROKE_PX", "FOREIGN_PIXEL_PX",
        "FINAL_MANUAL_DECISION", "NOTE",
    )
    blank_cells = [as_text(row.get("GLYPH_ID")) for row in final_ledger
                   if any(not as_text(row.get(field)) for field in final_fields)]
    final_decision_bad = [as_text(row.get("GLYPH_ID")) for row in final_ledger
                          if as_text(row.get("FINAL_MANUAL_DECISION")).upper() != "PASS"
                          or as_text(row.get("ORIGINAL_MATCH")).upper() != "PASS"
                          or as_text(row.get("OVERLAY_COMPLETE")).upper() != "PASS"
                          or as_text(row.get("MASK_ONLY_PURE")).upper() != "PASS"]
    broken_final_paths: list[str] = []
    for row in final_ledger:
        for field in ("FINAL_CONTACT_SHEET", "FINAL_1X_ORIGINAL", "FINAL_1X_TARGET_OVERLAY", "FINAL_1X_MASK_ONLY", "FINAL_8X_REVIEW_EVIDENCE"):
            candidate = relative_path(row.get(field))
            if not candidate.is_file():
                broken_final_paths.append(f"{row.get('GLYPH_ID')}:{field}")
    record("final_manual_glyph_ledger_closed", not blank_cells and not final_decision_bad and not broken_final_paths,
           {"rows": len(final_ledger), "blank_cells": blank_cells, "bad_decisions": final_decision_bad,
            "broken_paths": broken_final_paths})
    final_contact_sheets = {as_text(row.get("FINAL_CONTACT_SHEET")) for row in final_ledger}
    record("final_contact_sheet_coverage", len(final_contact_sheets) == 12 and all(relative_path(path).is_file() for path in final_contact_sheets),
           {"count": len(final_contact_sheets), "paths": sorted(final_contact_sheets)})
    final_mask_paths_bad = []
    for row in final_mask_manifest:
        for field in ("FINAL_VISIBLE_MASK", "FINAL_TARGET_OVERLAY"):
            if not relative_path(row.get(field)).is_file():
                final_mask_paths_bad.append(f"{row.get('GLYPH_ID')}:{field}")
    record("final_mask_and_overlay_files", not final_mask_paths_bad,
           {"rows": len(final_mask_manifest), "broken": final_mask_paths_bad})
    integrity_bad = [as_text(row.get("GLYPH_ID")) for row in final_mask_integrity
                     if not true(row.get("MASK_PURITY_COMPLETENESS_PASS"))
                     or number(row.get("FINAL_FOREIGN_GLYPH_PIXEL_PX")) != 0]
    record("final_mask_purity_completeness", not integrity_bad,
           {"rows": len(final_mask_integrity), "bad": integrity_bad})
    isolation_bad = [as_text(row.get("GLYPH_ID")) for row in isolation
                     if as_text(row.get("EVIDENCE_INTEGRITY_DECISION")).upper() != "PASS"]
    special_ids = {"G0011", "G0016", "G0029", "G0036", "G0106", "G0107", "G0108", "G0114", "G0115", "G0124", "G0125"}
    package_missing: list[str] = []
    expected_special_images = (
        "original_raw_1x.png", "original_raw_8x_nearest.png", "mask_only_1x.png", "mask_only_8x_nearest.png",
        "final_visible_mask_1x.png", "final_visible_mask_8x_nearest.png", "final_visible_overlay_1x.png",
        "final_visible_overlay_8x_nearest.png", "target_overlay_1x.png", "target_overlay_8x_nearest.png",
        "package_manifest.json",
    )
    for glyph_id in special_ids:
        folder = ROOT / "glyph_integrity_packages" / glyph_id
        for filename in expected_special_images:
            if not (folder / filename).is_file():
                package_missing.append(f"{glyph_id}/{filename}")
    record("initial_candidate_isolation_closure", set(as_text(r.get("GLYPH_ID")) for r in isolation) == special_ids
           and not isolation_bad and not package_missing,
           {"rows": len(isolation), "bad_decisions": isolation_bad, "package_missing": package_missing})
    final_by_id = {as_text(row.get("GLYPH_ID")): row for row in final_mask_integrity}
    p0717_glyph_integrity_ok = all(
        glyph_id in final_by_id
        and number(final_by_id[glyph_id].get("FINAL_FOREIGN_GLYPH_PIXEL_PX")) == 0
        and number(final_by_id[glyph_id].get("REAL_SHARED_COLLISION_PX")) == 3
        and true(final_by_id[glyph_id].get("MASK_PURITY_COMPLETENESS_PASS"))
        for glyph_id in {"G0029", "G0036"}
    )
    record("P0717_mask_integrity_vs_real_collision_separated", p0717_glyph_integrity_ok,
           {glyph_id: final_by_id.get(glyph_id, {}) for glyph_id in ("G0029", "G0036")})
    superseded = (ROOT / "SUPERSEDED_ARTIFACTS.md").read_text(encoding="utf-8") if (ROOT / "SUPERSEDED_ARTIFACTS.md").is_file() else ""
    raw_paths_exist = all((ROOT / name).is_file() for name in ("glyph_reviewer_ledger.csv", "glyph_machine_integrity.csv"))
    superseded_ok = raw_paths_exist and "SUPERSEDED_INITIAL_RAW" in superseded and "glyph_final_reviewer_ledger.csv" in superseded
    record("initial_raw_ledgers_declared_superseded", superseded_ok,
           {"raw_files_exist": raw_paths_exist, "declared": "SUPERSEDED_INITIAL_RAW" in superseded})

    # Four required views, visual harmony review, and actual native H_INK D/E.
    no_pending = lambda rows: not [as_text(r.get("GLYPH_ID") or r.get("VIEW_ID") or r.get("PANEL_ID"))
                                  for r in rows
                                  if any(word in as_text(value).upper() for value in r.values() for word in ("PENDING", "UNKNOWN", "MISSING"))]
    record("four_view_manual_ledger_closed", len(four_view) == 5 and no_pending(four_view)
           and all(as_text(row.get("DECISION")).upper() in {"PASS", "FAIL"} for row in four_view),
           {"rows": len(four_view), "view_ids": [row.get("VIEW_ID") for row in four_view]})
    record("panel_role_script_manual_ledger_closed", len(panel_role) == 23 and no_pending(panel_role)
           and all(as_text(row.get("MANUAL_FONT_VISUAL_HARMONY")).upper() in {"PASS", "FAIL"} for row in panel_role),
           {"rows": len(panel_role)})
    record("semantic_manual_ledger_closed", len(semantic_ledger) == len(semantic) and no_pending(semantic_ledger)
           and all(as_text(row.get("DECISION")).upper() == "PASS" for row in semantic_ledger),
           {"rows": len(semantic_ledger)})
    d_rows = [row for row in role_hierarchy if as_text(row.get("AUDIT_LEVEL")) == "PANEL_ROLE_SCRIPT"]
    d_fail = sum(as_text(row.get("D_STATUS")).upper() == "FAIL" for row in d_rows)
    e_fail = sum(as_text(row.get("E_STATUS")).upper() == "FAIL" for row in role_e)
    annotation_operator = [row for row in role_e if as_text(row.get("RULE_ID")) == "E_NA_BODY_ANNOTATION_MATH_OPERATOR"]
    annotation_operator_na_ok = len(annotation_operator) == 1 and as_text(annotation_operator[0].get("E_STATUS")) == "N/A_WITH_BASIS" and not as_text(annotation_operator[0].get("BASE_PANEL_ROLE_SCRIPT"))
    record("actual_final_mask_H_INK_D", len(d_rows) == 23 and d_fail == 3,
           {"panel_role_script_rows": len(d_rows), "D_fail": d_fail})
    record("actual_final_mask_H_INK_E", e_fail == 2 and annotation_operator_na_ok,
           {"E_fail": e_fail, "annotation_operator_is_NA_with_empty_base": annotation_operator_na_ok})
    record("actual_H_INK_summary_consistency",
           role_summary.get("d_applicable_fail_count") == d_fail
           and role_summary.get("e_applicable_fail_count") == e_fail
           and role_summary.get("pdf_span_proxy_used_for_pass") is False
           and role_summary.get("e_coverage_closed_with_basis") is True,
           role_summary)

    # Freeze an input artifact manifest after removal of the two exact zero-byte
    # LaTeX auxiliaries. Dynamic terminal products are intentionally excluded
    # from this input manifest so it stays non-self-referential.
    input_manifest_path = ROOT / "machine_terminal_input_file_manifest.csv"
    dynamic_terminal_products = {
        "machine_terminal.json",
        "machine_terminal.md",
        "machine_terminal_input_file_manifest.csv",
        "WRITE_STOPPED.md",
    }
    input_manifest_rows = []
    for path in sorted(candidate for candidate in ROOT.rglob("*") if candidate.is_file()):
        relative = str(path.relative_to(ROOT)).replace("\\", "/")
        if relative in dynamic_terminal_products:
            continue
        input_manifest_rows.append((relative, path.stat().st_size, path.suffix.lower() or "[no_extension]", "true"))
    with input_manifest_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("RELATIVE_PATH", "BYTES", "EXTENSION", "ORDINARY_FILE"))
        writer.writerows(input_manifest_rows)
    record("post_deletion_input_manifest", input_manifest_path.is_file() and input_manifest_path.stat().st_size > 0,
           {"file": input_manifest_path.name, "input_file_count": len(input_manifest_rows),
            "excluded_dynamic_products": sorted(dynamic_terminal_products)})

    # File hygiene and openability. This happens before terminal JSON/MD writes;
    # the terminal outputs themselves are then checked explicitly after writing.
    all_files = [path for path in ROOT.rglob("*") if path.is_file()]
    zero_files = [str(path.relative_to(ROOT)) for path in all_files if path.stat().st_size == 0]
    unsafe_names = [str(path.relative_to(ROOT)) for path in all_files if ":" in path.name or "\x00" in path.name]
    non_ordinary = [str(path.relative_to(ROOT)) for path in all_files if path.is_symlink() or not os.path.isfile(path)]
    bad_png: list[str] = []
    png_files = [path for path in all_files if path.suffix.lower() == ".png"]
    for path in png_files:
        try:
            with Image.open(path) as image:
                image.verify()
            with Image.open(path) as image:
                image.load()
        except Exception as exc:
            bad_png.append(f"{path.relative_to(ROOT)}: {exc}")
    record("ordinary_files_nonzero_safe_names", not zero_files and not unsafe_names and not non_ordinary,
           {"file_count": len(all_files), "zero_byte": zero_files, "unsafe_name_or_ads": unsafe_names, "non_ordinary": non_ordinary})
    record("all_png_openable", not bad_png,
           {"png_count": len(png_files), "bad_png": bad_png})

    # Reconcile the bottom-level recomputations with published JSON and MD.
    summary_expected = {
        "text_element_count": len(semantic),
        "glyph_count": len(glyph_manifest),
        "graphic_object_count": len(graphics),
        "all_object_count": n_objects,
        "all_unordered_pair_count": expected_pairs,
        "mandatory_relationship_count": len(mandatory),
        "source_font_fail_element_count": source_font_fail,
        "pixel_fail_glyph_count": pixel_fail,
        "low_profile_target_count": len(low),
        "low_profile_calibration_fail_count": low_calibration_fail,
        "low_profile_font_floor_fail_count": low_font_floor_fail,
        "low_profile_total_gate_fail_count": low_total_fail,
        "pair_failure_count": len(pair_failures),
        "clip_failure_count": sum(not true(row.get("CLIP_PASS")) for row in clip),
        "real_shared_collision_px": 3,
    }
    summary_mismatch = {key: {"summary": summary.get(key), "recomputed": value}
                        for key, value in summary_expected.items() if summary.get(key) != value}
    record("measurement_summary_recomputed_from_csv", not summary_mismatch, summary_mismatch or summary_expected)
    low_summary_ok = (
        low_summary.get("revision") == "111"
        and low_summary.get("low_profile_target_count") == len(low)
        and low_summary.get("calibration_fail_count") == low_calibration_fail
        and low_summary.get("font_floor_fail_count") == low_font_floor_fail
        and low_summary.get("total_low_profile_gate_fail_count") == low_total_fail
    )
    record("low_profile_summary_recomputed_from_csv", low_summary_ok, low_summary)
    visual = (ROOT / "after_visual_acceptance.md").read_text(encoding="utf-8") if (ROOT / "after_visual_acceptance.md").is_file() else ""
    source_audit = (ROOT / "source_audit.md").read_text(encoding="utf-8") if (ROOT / "source_audit.md").is_file() else ""
    low_audit = (ROOT / "low_profile_punctuation_audit.md").read_text(encoding="utf-8") if (ROOT / "low_profile_punctuation_audit.md").is_file() else ""
    expected_visual_tokens = (
        "SOURCE_FONT_PASS=false", "PIXEL_HEIGHT_PASS=false", "LOW_PROFILE_CALIBRATION_PASS=false",
        "FONT_VISUAL_HARMONY_PASS=false", "H_INK_D_PASS=false", "H_INK_E_PASS=false",
        "REQUIRED_OVERLAP_CLEARANCE_PASS=false", "CLIP_PASS=true", "EVIDENCE_INTEGRITY_PASS=true", "RESULT: FAIL→SA2",
    )
    record("markdown_conclusion_consistency", all(token in visual for token in expected_visual_tokens)
           and "six failed general glyph pixel/calibration gates" in source_audit
           and "three D failures and two applicable same-script E failures" in source_audit
           and "LOW_PROFILE_TOTAL_GATE_PASS" in low_audit,
           {"visual_tokens_present": [token for token in expected_visual_tokens if token in visual]})

    hard_gate_failures = {
        "SOURCE_FONT_PASS": source_font_fail > 0,
        "PIXEL_HEIGHT_PASS": pixel_fail > 0,
        "LOW_PROFILE_CALIBRATION_PASS": low_total_fail > 0,
        "FONT_VISUAL_HARMONY_PASS": True,
        "H_INK_D_PASS": d_fail > 0,
        "H_INK_E_PASS": e_fail > 0,
        "REQUIRED_OVERLAP_CLEARANCE_PASS": len(pair_failures) > 0,
    }
    expected_figure_result = "FAIL→SA2" if any(hard_gate_failures.values()) else "PASS→等待root"
    evidence_integrity_pass = all(
        CHECKS[name]["pass"]
        for name in (
            "final_glyph_id_coverage", "final_manual_glyph_ledger_closed", "final_contact_sheet_coverage",
            "final_mask_and_overlay_files", "final_mask_purity_completeness", "initial_candidate_isolation_closure",
            "P0717_mask_integrity_vs_real_collision_separated", "initial_raw_ledgers_declared_superseded",
            "ordinary_files_nonzero_safe_names", "all_png_openable", "all_existing_csv_parseable", "all_existing_json_parseable",
        )
    )
    record("evidence_integrity_expected_true", evidence_integrity_pass,
           "active final evidence only; initial raw ledgers excluded from final counts")
    terminal_machine_check_pass = not ISSUES
    report = {
        "figure_id": "FIG-P582-01",
        "audit_role": "SA1 independent strict audit",
        "coordinate": "candidate final PDF native 300dpi 1:1 raw masks",
        "superseded_initial_raw": ["glyph_reviewer_ledger.csv", "glyph_machine_integrity.csv"],
        "bottom_level_counts": {
            "text_elements": len(semantic),
            "glyphs": len(glyph_manifest),
            "graphic_objects": len(graphics),
            "all_objects": n_objects,
            "all_unordered_pairs": len(all_pairs),
            "pair_formula": f"{n_objects} choose 2 = {expected_pairs}",
            "mandatory_relationships": len(mandatory),
            "source_font_fail_elements": source_font_fail,
            "pixel_fail_glyphs": pixel_fail,
            "pixel_source_floor_fail_glyphs": pixel_source_floor_fail,
            "glyph_combined_source_or_pixel_gate_failures": overall_glyph_gate_fail,
            "low_profile_targets": len(low),
            "low_profile_calibration_failures": low_calibration_fail,
            "low_profile_source_floor_failures": low_font_floor_fail,
            "low_profile_total_gate_failures": low_total_fail,
            "D_actual_H_INK_failures": d_fail,
            "E_actual_H_INK_failures": e_fail,
            "pair_failures": len(pair_failures),
            "clip_failures": sum(not true(row.get("CLIP_PASS")) for row in clip),
            "P0717_overlap_pixels": 3,
        },
        "file_hygiene": {
            "preterminal_ordinary_file_count": len(all_files),
            "preterminal_png_count": len(png_files),
            "zero_byte_file_count": len(zero_files),
            "unsafe_filename_or_ads_count": len(unsafe_names),
            "nonordinary_file_count": len(non_ordinary),
            "unopenable_png_count": len(bad_png),
        },
        "post_deletion_input_manifest": {
            "file": input_manifest_path.name,
            "input_file_count": len(input_manifest_rows),
            "excluded_dynamic_products": sorted(dynamic_terminal_products),
        },
        "hard_gate_failures_present": hard_gate_failures,
        "EVIDENCE_INTEGRITY_PASS": evidence_integrity_pass,
        "FIGURE_HARD_GATES_PASS": not any(hard_gate_failures.values()),
        "FIGURE_RESULT": expected_figure_result,
        "TERMINAL_MACHINE_CONSISTENCY_PASS": terminal_machine_check_pass,
        "checks": CHECKS,
        "issues": ISSUES,
    }
    json_path = ROOT / "machine_terminal.json"
    md_path = ROOT / "machine_terminal.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_lines = [
        "# FIG-P582-01 SA1 machine terminal check",
        "",
        "The active evidence package is machine-consistent only if `TERMINAL_MACHINE_CONSISTENCY_PASS=true`. This field is distinct from the figure verdict.",
        "",
        f"- `TERMINAL_MACHINE_CONSISTENCY_PASS={str(terminal_machine_check_pass).lower()}`",
        f"- `EVIDENCE_INTEGRITY_PASS={str(evidence_integrity_pass).lower()}`",
        f"- `FIGURE_HARD_GATES_PASS={str(not any(hard_gate_failures.values())).lower()}`",
        f"- `FIGURE_RESULT={expected_figure_result}`",
        "",
        "## Recomputed bottom-level counts",
        "",
        f"- Objects: {n_objects} = {len(semantic)} semantic/text + {len(graphics)} graphic; pairs: {n_objects} choose 2 = {expected_pairs}.",
        f"- Mandatory relationships: {len(mandatory)}; source-font failures: {source_font_fail}; glyph pixel/calibration failures: {pixel_fail}; combined glyph source-or-pixel failures: {overall_glyph_gate_fail}.",
        f"- Low-profile: {len(low)} targets, {low_calibration_fail} calibration failures, {low_font_floor_fail} source-floor failures, {low_total_fail} total `LOW_PROFILE_TOTAL_GATE_PASS=false` rows.",
        f"- Actual native final-mask H_INK: D failures {d_fail}; applicable E failures {e_fail}.",
        f"- Pair failures: {len(pair_failures)}; P0717 arrow/value relation: 3px overlap and 0px clearance; clip failures: {sum(not true(row.get('CLIP_PASS')) for row in clip)}.",
        "",
        "## File hygiene",
        "",
        f"- Pre-terminal ordinary files: {len(all_files)}; PNG files opened: {len(png_files)}; zero-byte files: {len(zero_files)}; unsafe/ADS-style names: {len(unsafe_names)}; non-ordinary files: {len(non_ordinary)}; unopenable PNGs: {len(bad_png)}.",
        f"- `machine_terminal_input_file_manifest.csv` records the {len(input_manifest_rows)} post-deletion input artifacts; only dynamic terminal products and the future stop marker are excluded to avoid self-reference.",
        "- The initial raw `glyph_reviewer_ledger.csv` and `glyph_machine_integrity.csv` are parseable `SUPERSEDED_INITIAL_RAW` diagnostics and are excluded from final integrity counts.",
        "",
        "## Checks",
        "",
    ]
    for name, item in CHECKS.items():
        md_lines.append(f"- {'PASS' if item['pass'] else 'FAIL'} — `{name}`: `{item['detail']}`")
    if ISSUES:
        md_lines.extend(["", "## Issues", ""])
        md_lines.extend(f"- {issue}" for issue in ISSUES)
    md_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    # The two emitted terminal products must themselves be ordinary non-empty
    # files; all other scan values describe the deterministic input set.
    emitted_ok = all(path.is_file() and path.stat().st_size > 0 and not path.is_symlink()
                     for path in (json_path, md_path))
    if not emitted_ok:
        return 2
    return 0 if terminal_machine_check_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
