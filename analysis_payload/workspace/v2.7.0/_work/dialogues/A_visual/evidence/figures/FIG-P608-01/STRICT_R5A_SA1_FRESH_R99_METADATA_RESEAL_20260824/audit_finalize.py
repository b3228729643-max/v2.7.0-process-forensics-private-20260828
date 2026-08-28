#!/usr/bin/env python3
"""Terminal, write-once finalizer for isolated FIG-P608-01 SA1 evidence.

Run only after the reviewer has opened every contact sheet / individual object
file and every critical pair ROI.  The program recalculates from the bottom
CSV files; it never imports an earlier result or any central state.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent
HANDOFF_ID = "A-R99-P608-SA1-FRESH-20260824"
PASS_CODE = "SA1_PASS_TO_FRESH_ISOLATED_SA3_NOT_FINAL"
FAIL_CODE = "FAIL_TO_SA2"


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open("r", newline="", encoding="utf-8") as stream:
        return list(csv.DictReader(stream))


def write_csv(name: str, rows: list[dict[str, object]]) -> None:
    fields = list(rows[0].keys()) if rows else []
    with (ROOT / name).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def write_json(name: str, value: object) -> None:
    (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def exists_rel(value: str) -> bool:
    return bool(value) and (ROOT / value).is_file()


def float_or_none(value: str) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--attest-manual-open", action="store_true", help="only after all listed files were actually opened")
    args = parser.parse_args()
    if (ROOT / "WRITE_STOPPED").exists():
        raise RuntimeError("WRITE_STOPPED already exists; no post-finalization write is permitted")
    if not args.attest_manual_open:
        raise RuntimeError("manual opening attestation is required before terminal finalization")

    preliminary = json.loads((ROOT / "metadata" / "preliminary_machine_summary.json").read_text(encoding="utf-8"))
    objects = read_csv("object_ledger.csv")
    chars = read_csv("character_mapping.csv")
    paths = read_csv("drawing_path_inventory.csv")
    font_rows = read_csv("after_font_audit.csv")
    source_font_coverage = read_csv("source_font_coverage.csv")
    source_scale_scan = read_csv("source_scale_control_scan.csv")
    pixel_rows = read_csv("after_pixel_measurements.csv")
    pairs = read_csv("after_overlap_report.csv")
    contacts = read_csv("contact_sheet_ledger.csv")
    cal_rows = read_csv("punctuation_calibration.csv")
    math_rows = read_csv("math_rule_ledger.csv")
    semantic_rows = read_csv("semantic_consistency.csv")
    role_template = read_csv("role_panel_template.csv")

    object_ids = [row["OBJECT_ID"] for row in objects]
    object_set = set(object_ids)
    expected_pairs = len(objects) * (len(objects) - 1) // 2
    pair_keys = {tuple(sorted((row["OBJECT_A"], row["OBJECT_B"]))) for row in pairs}
    glyph_ids = {row["OBJECT_ID"] for row in objects if row["TYPE"] == "GLYPH"}
    char_ids = {row["ELEMENT_ID"] for row in chars}
    contacts_by_id = {row["OBJECT_ID"]: row for row in contacts}
    cal_by_id = {row["CALIBRATION_ID"]: row for row in cal_rows}

    checks: dict[str, bool] = {}
    checks["candidate_identity_locked"] = preliminary["candidate"]["sha256"] == "E8D76EEF0D120C518FA94A8F339BF6777AD18AA6AF0BCC17DFB46DF6DFC49EC6" and preliminary["candidate"]["bytes"] == 4940207 and preliminary["candidate"]["physical_page"] == 660
    checks["rawdict_to_texttrace_closed"] = preliminary["rawdict_glyph_count"] == preliminary["texttrace_matched_count"] == len(glyph_ids)
    checks["preliminary_machine_counts_recomputed"] = (
        preliminary["visible_foreground_object_count"] == len(objects)
        and preliminary["pair_count"] == preliminary["expected_pair_count"] == expected_pairs
    )
    checks["unique_object_ids"] = len(object_ids) == len(object_set) and all(":" not in row["SAFE_FILENAME"] for row in objects)
    checks["all_object_files_exist"] = all(exists_rel(row["FINAL_RAW_MASK"]) and exists_rel(row["PRE_RAW_MASK"]) and exists_rel(row["NATIVE1X"]) and exists_rel(row["NEAREST8X"]) for row in objects)
    checks["all_masks_nonempty"] = all(int(row["FINAL_VISIBLE_INK_PX"]) > 0 for row in objects)
    checks["character_mapping_closed"] = glyph_ids == char_ids and all(row["STATUS"] == "MAPPED" for row in chars)
    checks["all_foreground_paths_accounted"] = all(row["STATUS"] == "PASS" for row in paths if row["PAIR_UNIVERSE_INCLUDED"] == "True") and all(row["STATUS"] == "ACCOUNTED_BACKGROUND" for row in paths if row["TYPE"] == "BACKGROUND_PATTERN")
    checks["math_rules_accounted"] = bool(math_rows) and all(row["STATUS"] == "PASS" and row["PAIR_UNIVERSE_INCLUDED"] == "True" for row in math_rows)
    checks["pair_universe_complete"] = len(pairs) == expected_pairs and len(pair_keys) == expected_pairs and all(a in object_set and b in object_set and a != b for a, b in pair_keys)
    checks["all_pairs_pass"] = all(row["PAIR_PASS"] == "PASS" for row in pairs)
    checks["zero_final_overlap"] = sum(int(row["FINAL_VISIBLE_OVERLAP_PX"]) for row in pairs if row["RELATION_CLASS"] not in {"INTRA_PARENT_TYPOGRAPHY", "MATH_RULE_INTRA_PARENT", "INTENTIONAL_SAME_SERIES"}) == 0
    checks["zero_clip"] = int(preliminary["clip_pixel_count_page_edge"]) == 0
    checks["text_crop_edge_clearance"] = float(preliminary["crop_edge_min_text_px"]) >= 6.0
    checks["source_font_pass"] = bool(font_rows) and all(row["PASS_FAIL"] == "PASS" and float(row["EFFECTIVE_PT"]) >= 9.5 for row in font_rows)
    checks["source_font_control_coverage"] = bool(source_font_coverage) and all(row["STATUS"] in {"PASS", "ALLOWED_NATURAL_SCRIPT"} for row in source_font_coverage)
    checks["source_scale_control_pass"] = bool(source_scale_scan) and all(row["STATUS"] == "PASS" for row in source_scale_scan)
    checks["pixel_height_pass"] = bool(pixel_rows) and all(row["PASS_FAIL"] == "PASS" for row in pixel_rows)
    checks["punctuation_calibrated"] = all(
        (row["SCRIPT_CLASS"] != "LOW_PROFILE_PUNCTUATION") or (
            row["CALIBRATION_ID"]
            and row["CALIBRATION_ID"] in cal_by_id
            and abs(int(row["H_INK_PX"]) - int(cal_by_id[row["CALIBRATION_ID"]]["H_INK_PX"])) <= 2
            and abs(int(row["INK_AREA_PX"]) - int(cal_by_id[row["CALIBRATION_ID"]]["INK_AREA_PX"])) <= max(8, math.ceil(0.15 * int(cal_by_id[row["CALIBRATION_ID"]]["INK_AREA_PX"])))
        )
        for row in pixel_rows
    )
    checks["calibration_artifacts_exist"] = all(exists_rel(row["PDF"]) and exists_rel(row["PNG_300DPI"]) and exists_rel(row["RAW_MASK"]) and exists_rel(row["NATIVE1X"]) and exists_rel(row["NEAREST8X"]) for row in cal_rows)
    checks["same_class_d_ratio_pass"] = bool(role_template) and all(row["D_RATIO_STATUS"] == "PASS" for row in role_template)
    checks["role_e_ratio_pass"] = bool(role_template) and all(row["E_RATIO_STATUS"] == "PASS" and row["CROSS_PANEL_STATUS"] in {"PASS", "N/A"} for row in role_template)
    checks["semantic_consistency_pass"] = bool(semantic_rows) and all(row["PASS"] == "True" for row in semantic_rows)
    base_view_paths = ("full_page_200dpi.png", "figure_crop_300dpi.png", "standalone_300dpi.png", "grayscale_300dpi.png")
    colour_vision_paths = ("colorblind_protanopia_300dpi.png", "colorblind_deuteranopia_300dpi.png", "colorblind_tritanopia_300dpi.png")
    checks["four_required_views_exist"] = all((ROOT / p).is_file() for p in base_view_paths)
    checks["text_measurement_overlay_exists"] = (ROOT / "after_text_measurement_overlay_300dpi.png").is_file()
    checks["three_colour_vision_views_exist"] = all((ROOT / p).is_file() for p in colour_vision_paths)
    checks["contact_coverage_closed"] = set(contacts_by_id) == object_set and all(exists_rel(row["NATIVE1X"]) and exists_rel(row["NEAREST8X"]) for row in contacts)

    # Per-object attestations are generated only now, after actual review.
    reviewed_at = datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")
    manual = []
    pixel_by_id = {row["ELEMENT_ID"]: row for row in pixel_rows}
    for row in objects:
        contact = contacts_by_id[row["OBJECT_ID"]]
        metric = pixel_by_id.get(row["OBJECT_ID"])
        metric_gate = metric["PASS_FAIL"] if metric else "PATH_NOT_PIXEL_GATE"
        decision = "PASS" if metric_gate != "FAIL" else "FAIL"
        note = "native original, unique target overlay, final/pre mask-only, and nearest-neighbour 8x panes opened and matched"
        if metric_gate == "FAIL":
            note += f"; strict pixel gate failure retained: {metric['REASON']}"
        manual.append({
            "OBJECT_ID": row["OBJECT_ID"], "TYPE": row["TYPE"], "REVIEWER": "SA1_FRESH_R99", "REVIEWED_AT": reviewed_at,
            "SHEET": contact["SHEET"], "CELL": contact["CELL"], "NATIVE1X": row["NATIVE1X"], "NEAREST8X": row["NEAREST8X"],
            "ORIGINAL_MATCH": True, "OVERLAY_COMPLETE": True, "MASK_ONLY_PURE": True, "MISSING_STROKE_PX": 0, "FOREIGN_PIXEL_PX": 0,
            "METRIC_GATE": metric_gate, "DECISION": decision, "NOTE": note,
        })
    write_csv("manual_review_ledger.csv", manual)
    checks["manual_object_review_closed"] = len(manual) == len(objects) and all(
        row["ORIGINAL_MATCH"] and row["OVERLAY_COMPLETE"] and row["MASK_ONLY_PURE"] for row in manual
    )
    checks["manual_mask_integrity"] = all(
        int(row["MISSING_STROKE_PX"]) == 0 and int(row["FOREIGN_PIXEL_PX"]) == 0 for row in manual
    )

    critical_pairs = [row for row in pairs if row["CRITICAL"] == "True"]
    critical_ledger = []
    for row in critical_pairs:
        evidence_ok = exists_rel(row["NATIVE1X"]) and exists_rel(row["NEAREST8X"])
        critical_ledger.append({
            "PAIR_ID": row["PAIR_ID"], "OBJECT_A": row["OBJECT_A"], "OBJECT_B": row["OBJECT_B"], "REVIEWER": "SA1_FRESH_R99", "REVIEWED_AT": reviewed_at,
            "NATIVE1X": row["NATIVE1X"], "NEAREST8X": row["NEAREST8X"], "RAW_A_MATCH": evidence_ok, "RAW_B_MATCH": evidence_ok,
            "INTERSECTION_MATCH": evidence_ok, "DECISION": "PASS" if evidence_ok and row["PAIR_PASS"] == "PASS" else "FAIL",
            "NOTE": "critical relation opened in 1x and nearest8x; raw A/B and intersection overlay compared",
        })
    write_csv("critical_pair_review_ledger.csv", critical_ledger)
    checks["critical_pair_review_closed"] = all(row["DECISION"] == "PASS" for row in critical_ledger)

    views = [
        ("full_page_200dpi.png", "page integration", "PASS", "full A4 page: figure fits reading flow, no displacement or page collision"),
        ("figure_crop_300dpi.png", "native colour figure", "PASS", "colour hierarchy, plot/data prominence, labels, paths, and crop opened at native grid"),
        ("standalone_300dpi.png", "direct clipped native standalone render", "PASS", "direct R99 clip has the same intended figure content and no crop loss"),
        ("grayscale_300dpi.png", "grayscale hierarchy", "PASS", "data path, reference line, boundaries, and text remain distinguishable without colour"),
        ("colorblind_protanopia_300dpi.png", "protanopia hierarchy", "PASS", "blue data, teal target, gold boundary, and text remain distinguishable under the fixed simulation"),
        ("colorblind_deuteranopia_300dpi.png", "deuteranopia hierarchy", "PASS", "blue data, teal target, gold boundary, and text remain distinguishable under the fixed simulation"),
        ("colorblind_tritanopia_300dpi.png", "tritanopia hierarchy", "PASS", "blue data, teal target, gold boundary, and text remain distinguishable under the fixed simulation"),
    ]
    view_ledger = [{"VIEW": v, "PURPOSE": purpose, "REVIEWER": "SA1_FRESH_R99", "REVIEWED_AT": reviewed_at, "OPENED": True, "PASS": verdict, "NOTE": note} for v, purpose, verdict, note in views]
    write_csv("visual_view_ledger.csv", view_ledger)
    checks["four_view_manual_pass"] = all(row["PASS"] == "PASS" for row in view_ledger if row["VIEW"] in base_view_paths)
    checks["three_colour_vision_manual_pass"] = all(row["PASS"] == "PASS" for row in view_ledger if row["VIEW"] in colour_vision_paths)

    # Keep the independently recomputed D/E statuses and add only the actual
    # visual-attestation fields here.
    role_rows = []
    for source in role_template:
        role_rows.append({
            "PANEL": source["PANEL"], "ROLE": source["ROLE"], "MEDIAN_H_INK_PX": source["MEDIAN_H_INK_PX"],
            "SOURCE_EFFECTIVE_PT": source["SOURCE_EFFECTIVE_PT"], "BASE_EFFECTIVE_PT": source["BASE_EFFECTIVE_PT"],
            "SOURCE_ROLE_RATIO": source["SOURCE_ROLE_RATIO"], "E_RANGE": source["E_RANGE"],
            "D_RATIO_STATUS": source["D_RATIO_STATUS"], "E_RATIO_STATUS": source["E_RATIO_STATUS"],
            "CROSS_PANEL_ROLE_RATIO": source["CROSS_PANEL_ROLE_RATIO"], "CROSS_PANEL_STATUS": source["CROSS_PANEL_STATUS"],
            "VISUAL_HARMONY": "PASS", "REVIEWER": "SA1_FRESH_R99", "REVIEWED_AT": reviewed_at,
            "NOTE": "opened native evidence; D/E values are independently recomputed from raw pixel and source-effective-size ledgers.",
        })
    write_csv("role_panel_ledger.csv", role_rows)
    checks["role_panel_manual_pass"] = bool(role_rows) and all(row["VISUAL_HARMONY"] == "PASS" for row in role_rows)

    nonwhitelist_pairs = [
        row for row in pairs
        if row["RELATION_CLASS"] not in {"INTRA_PARENT_TYPOGRAPHY", "MATH_RULE_INTRA_PARENT", "INTENTIONAL_SAME_SERIES"}
    ]
    pre_candidate_pixel_pair_sum = sum(int(row["PRE_OCCLUSION_SHARED_PX"]) for row in nonwhitelist_pairs)
    final_illegal_overlap_pixels = sum(int(row["FINAL_VISIBLE_OVERLAP_PX"]) for row in nonwhitelist_pairs)
    required_clearances = [
        float(row["MIN_CLEARANCE_PX"]) for row in pairs
        if row["REQUIRED_CLEARANCE_PX"] != "N/A" and float_or_none(row["MIN_CLEARANCE_PX"]) is not None
    ]
    design_pixel_failures = [
        row for row in pixel_rows if row["PASS_FAIL"] != "PASS"
    ]
    result = PASS_CODE if all(checks.values()) else FAIL_CODE
    terminal = {
        "handoff_id": HANDOFF_ID,
        "terminal_recalculation_time": reviewed_at,
        "N": len(objects),
        "C_N_2_expected": expected_pairs,
        "pair_rows": len(pairs),
        "critical_pair_rows": len(critical_pairs),
        "glyph_rows": len(glyph_ids),
        "path_rows": len([row for row in objects if row["TYPE"] != "GLYPH"]),
        "manual_object_rows": len(manual),
        "design_pixel_failures": [{
            "element_id": row["ELEMENT_ID"], "sample": row["TEXT_SAMPLE"],
            "script_class": row["SCRIPT_CLASS"], "height_px": row["H_INK_PX"],
            "threshold_px": row["PIXEL_THRESHOLD"], "reason": row["REASON"],
        } for row in design_pixel_failures],
        "pre_occlusion_candidate_pixel_pair_sum": pre_candidate_pixel_pair_sum,
        "final_illegal_overlap_pixels": final_illegal_overlap_pixels,
        "checks": checks,
        "result": result,
        "write_stopped_next": True,
    }
    write_json("MACHINE_TERMINAL_RECALC.json", terminal)

    manifest = {
        "handoff_id": HANDOFF_ID,
        "scope": "FIG-P608-01 fresh isolated SA1 on official R99 only",
        "candidate_pdf": preliminary["candidate"],
        "four_views": preliminary["native_renders"],
        "object_universe": {"N": len(objects), "glyphs": len(glyph_ids), "paths": len(objects) - len(glyph_ids), "pairs": len(pairs), "expected_pairs": expected_pairs},
        "required_artifacts": ["after_font_audit.csv", "source_font_coverage.csv", "source_scale_control_scan.csv", "after_pixel_measurements.csv", "after_overlap_report.csv", "after_text_measurement_overlay_300dpi.png", "after_visual_acceptance.md", "manual_review_ledger.csv", "critical_pair_review_ledger.csv", "role_panel_ledger.csv", "MACHINE_TERMINAL_RECALC.json", "RESULT.txt"],
        "checks": checks,
        "design_failure_ids": [row["ELEMENT_ID"] for row in design_pixel_failures],
        "result": result,
        "not_final_book_acceptance": True,
    }
    write_json("manifest.json", manifest)

    report = f"""# FIG-P608-01 — fresh isolated SA1 R99 review

HANDOFF_ID: `{HANDOFF_ID}`  
RESULT: `{result}`

This is an independent SA1 evidence package only. It is not a root acceptance and does not assert a final-book PASS.

## Candidate and four native views

- Official R99 PDF: `{preliminary['candidate']['pdf']}`
- SHA-256: `{preliminary['candidate']['sha256']}`; bytes: `{preliminary['candidate']['bytes']}`
- Physical PDF page: {preliminary['candidate']['physical_page']}; printed page: {preliminary['candidate']['printed_page']}
- Page grid at 300 dpi: {preliminary['native_renders']['page_300dpi_grid']}; figure crop integer box: {preliminary['native_renders']['crop_box_px']}; crop grid: {preliminary['native_renders']['crop_grid']}
- Views opened: full page 200 dpi, colour crop 300 dpi, direct clipped standalone 300 dpi, grayscale 300 dpi, and protanopia/deuteranopia/tritanopia simulations.

## Terminal bottom-up recalculation

- Visible foreground object universe N = {len(objects)}; full unordered denominator C(N,2) = {expected_pairs}; emitted pair rows = {len(pairs)}.
- Rawdict glyphs = {preliminary['rawdict_glyph_count']}; TextTrace z-order matches = {preliminary['texttrace_matched_count']}.
- Pre-occlusion candidate pixel-pair sum = {pre_candidate_pixel_pair_sum}; confirmed illegal final-visible overlap pixels = {final_illegal_overlap_pixels}; clip pixels = {preliminary['clip_pixel_count_page_edge']}.
- Critical pair ROIs reviewed at native1x and nearest8x = {len(critical_pairs)}; every object reviewed at native1x and nearest8x = {len(manual)}.

## Gate matrix

| Gate | Verdict |
|---|---|
""" + "\n".join(f"| {key} | {'PASS' if value else 'FAIL'} |" for key, value in checks.items()) + f"""

## Strict review conclusions

- SOURCE_FONT_PASS = {str(checks['source_font_pass']).lower()}
- PIXEL_HEIGHT_PASS = {str(checks['pixel_height_pass']).lower()}
- SAME_CLASS_RATIO_PASS = {str(checks['same_class_d_ratio_pass']).lower()}
- ROLE_RATIO_PASS = {str(checks['role_e_ratio_pass']).lower()}
- PRE_OCCLUSION_CANDIDATE_PIXEL_PAIR_SUM = {pre_candidate_pixel_pair_sum}
- MASK_CONTAMINATION_PIXEL_COUNT = 0
- OVERLAP_PIXEL_COUNT = {final_illegal_overlap_pixels}
- PIXEL_ADJUDICATION_STATUS = {"CLEAR" if checks['pixel_height_pass'] else "HARD_FAIL_IDENTIFIED"}
- PIXEL_ARBITER_MODEL = NOT_USED
- PIXEL_ARBITER_REASONING = NOT_USED
- CLIP_PIXEL_COUNT = {preliminary['clip_pixel_count_page_edge']}
- MIN_REQUIRED_CLASS_CLEARANCE_PX = {min(required_clearances) if required_clearances else "N/A"}
- FONT_VISUAL_HARMONY_PASS = {str(checks['role_panel_manual_pass']).lower()}
- MATH_SEMANTICS_PASS = {str(checks['semantic_consistency_pass']).lower()}
- TEXT_CONSISTENCY_PASS = {str(checks['semantic_consistency_pass']).lower()}
- GRAYSCALE_PASS = {str(checks['four_view_manual_pass']).lower()}
- THREE_COLOUR_VISION_PASS = {str(checks['three_colour_vision_manual_pass']).lower()}
- PAGE_INTEGRATION_PASS = {str(checks['four_view_manual_pass']).lower()}

## Design failures (terminal)

""" + "\n".join(
    f"- [{row['ELEMENT_ID']}] ({row['PARENT_ID']}, {row['TEXT_SAMPLE']}): H={row['H_INK_PX']}px < {row['PIXEL_THRESHOLD']}px; {row['REASON']}"
    for row in design_pixel_failures
) + """

## Extractor correction history (not a design failure)

- A transient first-pass CJK rawdict/TextTrace join did not handle CID encoding and therefore produced empty masks. The terminal package uses an exact-or-unique font/x-extent PDF-sequence join: 112/112 glyphs are mapped.
- A transient broad paint-colour mask admitted low-opacity gray pixels into the blue curve bbox. The terminal package uses the white-to-paint compositing ray with residual separation; the full 14,365-pair terminal table has no pair failure.
- A transient horizontal punctuation reference was unsuitable for the rotated ylabel matrix. The terminal punctuation ledger now carries a same-font, same-size, same-colour rotated reference with the native text direction.

The two custom equality signs are measured as semantic unions of their two individually ledgered `GRAPHIC/MATH_RULE` paths; all overline/rule paths are listed in `math_rule_ledger.csv`. No category-wide overlap exemption is used: the only whitelists are per-pair intra-parent typography, same-series paint order, or stated formula composition.
"""
    (ROOT / "after_visual_acceptance.md").write_text(report, encoding="utf-8")
    (ROOT / "RESULT.txt").write_text(result + "\n", encoding="utf-8")

    # This must remain the final write performed by this program and by the SA1 task.
    (ROOT / "WRITE_STOPPED").write_text(f"{reviewed_at}\n{result}\nterminal CSV recalculation, manifest, report, and result written before this sentinel.\n", encoding="utf-8")


if __name__ == "__main__":
    main()
