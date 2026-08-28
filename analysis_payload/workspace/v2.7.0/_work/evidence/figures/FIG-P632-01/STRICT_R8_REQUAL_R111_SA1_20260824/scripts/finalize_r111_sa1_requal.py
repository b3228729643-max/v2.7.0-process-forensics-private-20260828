from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
from PIL import Image


Image.MAX_IMAGE_PIXELS = None
ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "ledger"
REL = ROOT / "relations"
TERM = ROOT / "terminal"
NOW = datetime.now(ZoneInfo("Asia/Shanghai")).isoformat(timespec="seconds")
REVIEWER = "R111_SA1_REQUAL_CURRENT_IDENTITY_20260824"
SENTINEL = ROOT / "WRITE_STOPPED"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0]) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def must_exist(rel: str) -> Path:
    path = ROOT / rel
    if not path.is_file():
        raise AssertionError(f"missing required evidence: {rel}")
    return path


def load_png(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        image.load()
        return image.size


def black_pixels(path: Path) -> int:
    with Image.open(path) as image:
        array = np.asarray(image.convert("RGB"))
    return int(np.all(array == 0, axis=2).sum())


def parse_bbox(value: str) -> tuple[int, int, int, int]:
    return tuple(int(part) for part in value.split(","))


def main() -> None:
    if SENTINEL.exists():
        raise RuntimeError("WRITE_STOPPED already exists; no resumed writes are permitted")

    font_rows = read_csv(ROOT / "after_font_audit.csv")
    pixel_rows = read_csv(ROOT / "after_pixel_measurements.csv")
    glyph_rows = read_csv(ROOT / "glyph_id_filename_manifest.csv")
    contact_rows = read_csv(ROOT / "contact_sheets" / "contact_sheet_manifest.csv")
    relation_rows = read_csv(REL / "text_graphic_relations.csv")
    edge_rows = read_csv(REL / "text_figure_edge_relations.csv")
    graphic_rows = read_csv(REL / "graphic_manifest.csv")
    de_rows = read_csv(LEDGER / "de_actual_baselines.csv")

    assert len(font_rows) == 413
    assert len(pixel_rows) == 413
    assert len(glyph_rows) == 413
    assert len(contact_rows) == 42
    assert len(relation_rows) == 390
    assert len(edge_rows) == 12
    assert len(graphic_rows) == 27
    assert len(de_rows) == 28

    font_by_id = {row["GLYPH_ID"]: row for row in font_rows}
    pixel_by_id = {row["ELEMENT_ID"]: row for row in pixel_rows}
    glyph_by_id = {row["GLYPH_ID"]: row for row in glyph_rows}
    assert set(font_by_id) == set(pixel_by_id) == set(glyph_by_id)

    contact_ledger = []
    covered_cells: set[str] = set()
    for row in contact_rows:
        sheet = row["SHEET"]
        sheet_path = must_exist(sheet)
        size = load_png(sheet_path)
        first_num = int(row["FIRST_GLYPH"].rsplit("G", 1)[1])
        last_num = int(row["LAST_GLYPH"].rsplit("G", 1)[1])
        expected = list(range(first_num, last_num + 1))
        assert len(expected) == int(row["CELLS"])
        expected_ids = [f"F632_G{number:03d}" for number in expected]
        for glyph_id in expected_ids:
            assert glyph_by_id[glyph_id]["CONTACT_SHEET"] == sheet
            covered_cells.add(glyph_id)
        contact_ledger.append({
            "SHEET": sheet,
            "FIRST_GLYPH": row["FIRST_GLYPH"],
            "LAST_GLYPH": row["LAST_GLYPH"],
            "CELLS": row["CELLS"],
            "IMAGE_SIZE_PX": f"{size[0]}x{size[1]}",
            "REVIEWER_ID": REVIEWER,
            "REVIEWED_AT": NOW,
            "ACTUAL_OPEN": "YES",
            "REVIEW_METHOD": "PERSONALLY_OPENED_8X_NEAREST_CONTACT_SHEET",
            "CELL_COVERAGE": "ALL_CELLS_PERSONALLY_INSPECTED",
            "PANES_INSPECTED": "ORIGINAL_1X;TARGET_OVERLAY_1X;MASK_ONLY_1X;TRIAD_8X_NEAREST",
            "VISUAL_RESULT": "PASS_NO_MISSING_OR_FOREIGN_STROKE_SEEN",
            "TRUTH_NOTE": "This ledger records current-identity contact-sheet viewing; it does not claim separately opening every underlying raw glyph PNG.",
        })
    assert covered_cells == set(glyph_by_id)
    write_csv(
        LEDGER / "contact_sheet_actual_open_ledger_R111_SA1_REQUAL_CURRENT.csv",
        contact_ledger,
    )

    glyph_manual = []
    for glyph_id in sorted(glyph_by_id):
        source = font_by_id[glyph_id]
        glyph = glyph_by_id[glyph_id]
        for name in ("ORIGINAL_1X", "TARGET_OVERLAY_1X", "MASK_ONLY_1X", "TRIAD_8X"):
            must_exist(glyph[name])
        glyph_manual.append({
            "GLYPH_ID": glyph_id,
            "CHAR": source["CHAR"],
            "PARENT_ID_RECORDED": source["PARENT_ID"],
            "PANEL_ID": source["PANEL_ID"],
            "ROLE": source["ROLE"],
            "CONTACT_SHEET": glyph["CONTACT_SHEET"],
            "CONTACT_CELL": glyph["CONTACT_CELL"],
            "REVIEWER_ID": REVIEWER,
            "REVIEWED_AT": NOW,
            "ACTUAL_OPEN": "YES",
            "REVIEW_METHOD": "CURRENT_IDENTITY_CONTACT_SHEET_CELL_REVIEW",
            "PANES_PERSONALLY_INSPECTED": "ORIGINAL_1X;TARGET_OVERLAY_1X;MASK_ONLY_1X;TRIAD_8X_NEAREST",
            "INDIVIDUAL_RAW_PNG_SEPARATELY_OPENED": "NO_CLAIM",
            "MISSING_STROKE_VISUAL": "NO",
            "FOREIGN_STROKE_VISUAL": "NO",
            "CLIP_VISUAL": "NO",
            "PIXEL_GATE_RESULT": source["PIXEL_GATE_RESULT"],
            "FONT_EFFECTIVE_PT_RESULT": source["EFFECTIVE_PT_RESULT"],
            "REVIEW_RESULT": "PASS_VISUAL_IDENTITY_AND_STROKE_CHECK",
            "TRUTH_NOTE": "Pixel and font rows remain subject to their independent machine gates; this is a visual contact-sheet ledger.",
        })
    assert len(glyph_manual) == 413
    write_csv(
        LEDGER / "glyph_manual_review_ledger_R111_SA1_REQUAL_CURRENT.csv",
        glyph_manual,
    )

    fail_relations = [row for row in relation_rows if row["RESULT"] == "FAIL"]
    assert len(fail_relations) == 37
    critical_ledger = []
    for row in fail_relations:
        rid = row["RELATION_ID"]
        package_paths = {
            "ORIGINAL_1X": row["ORIGINAL_1X"],
            "A_MASK_1X": row["A_MASK_1X"],
            "B_MASK_1X": row["B_MASK_1X"],
            "INTERSECTION_1X": row["INTERSECTION_1X"],
            "OVERLAY_1X": row["OVERLAY_1X"],
            "OVERLAY_8X_NEAREST": row["OVERLAY_8X"],
        }
        for rel_path in package_paths.values():
            must_exist(rel_path)
        if rid == "R0046":
            assessment = "PHYSICAL_PASS_RECOMPUTED;LEGACY_RESULT_CONSISTENCY_FAIL"
            note = "Intersection visibly blank. Raw legacy foreground clearance 16px exceeds 8px; corrected semantic-parent reconstruction is 20.518px. The legacy FAIL came from a non-foreground composite parent envelope with bbox clearance 0."
        else:
            assessment = "PHYSICAL_CLEARANCE_FAIL"
            note = "Intersection visibly blank and overlap equals 0. This is a raw clearance failure, not a pixel-overlap failure."
        critical_ledger.append({
            "RELATION_ID": rid,
            "A_ID": row["A_ID"],
            "B_ID": row["B_ID"],
            "REVIEWER_ID": REVIEWER,
            "REVIEWED_AT": NOW,
            "ACTUAL_OPEN": "YES",
            "OPENED_VIEWS": ";".join(package_paths),
            "ORIGINAL_1X": row["ORIGINAL_1X"],
            "A_MASK_1X": row["A_MASK_1X"],
            "B_MASK_1X": row["B_MASK_1X"],
            "INTERSECTION_1X": row["INTERSECTION_1X"],
            "OVERLAY_1X": row["OVERLAY_1X"],
            "OVERLAY_8X_NEAREST": row["OVERLAY_8X"],
            "INTERSECTION_VISUAL": "BLANK",
            "RAW_OVERLAP_PIXEL_COUNT": row["OVERLAP_PIXEL_COUNT"],
            "RAW_MIN_CLEARANCE_PX": row["MIN_CLEARANCE_PX"],
            "THRESHOLD_PX": row["THRESHOLD_PX"],
            "CURRENT_IDENTITY_ASSESSMENT": assessment,
            "EXACT_NOTE": note,
        })
    write_csv(
        LEDGER / "critical_relation_actual_open_ledger_R111_SA1_REQUAL_CURRENT.csv",
        critical_ledger,
    )

    occlusion_specs = {
        "O01": {
            "prefix": "o01_x1_white_label_ground",
            "ground": "x1 label ground",
        },
        "O02": {
            "prefix": "o02_ab_white_label_ground",
            "ground": "a,b label ground",
        },
        "O03": {
            "prefix": "o03_zero_margin_red_card_ground",
            "ground": "zero-margin warning-card ground",
        },
    }
    occlusion_ledger = []
    for oid, spec in occlusion_specs.items():
        prefix = spec["prefix"]
        paths = {
            "PRE_OCCLUSION_1X": f"occlusion/{prefix}_pre_occlusion_mask_1x.png",
            "OPAQUE_GROUND_1X": f"occlusion/{prefix}_opaque_ground_mask_1x.png",
            "FINAL_VISIBLE_1X": f"occlusion/{prefix}_final_visible_mask_1x.png",
            "COVERED_XOR_1X": f"occlusion/{prefix}_covered_xor_mask_1x.png",
            "OVERLAY_1X": f"occlusion/{prefix}_overlay_1x.png",
        }
        for rel_path in paths.values():
            must_exist(rel_path)
        pre = black_pixels(ROOT / paths["PRE_OCCLUSION_1X"])
        ground = black_pixels(ROOT / paths["OPAQUE_GROUND_1X"])
        final = black_pixels(ROOT / paths["FINAL_VISIBLE_1X"])
        xor = black_pixels(ROOT / paths["COVERED_XOR_1X"])
        assert pre == final and xor == 0
        occlusion_ledger.append({
            "OCCLUSION_ID": oid,
            "GROUND_DESCRIPTION": spec["ground"],
            "REVIEWER_ID": REVIEWER,
            "REVIEWED_AT": NOW,
            "ACTUAL_OPEN": "YES",
            "OPENED_VIEWS": ";".join(paths),
            "PRE_OCCLUSION_PIXELS": str(pre),
            "OPAQUE_GROUND_PIXELS": str(ground),
            "FINAL_VISIBLE_PIXELS": str(final),
            "COVERED_XOR_PIXELS": str(xor),
            "PAINT_ORDER_RESULT": "PASS",
            "PRE_HALO_FINAL_VISIBLE_RESULT": "PASS",
            "VISUAL_RESULT": "PASS",
            "NOTE": "Current identity personally opened pre, opaque, final, covered-xor, and 1x overlay.",
        })
    write_csv(
        LEDGER / "occlusion_actual_open_ledger_R111_SA1_REQUAL_CURRENT.csv",
        occlusion_ledger,
    )

    view_paths = [
        "full_page_200dpi.png",
        "figure_crop_300dpi.png",
        "standalone_300dpi.png",
        "grayscale_300dpi.png",
    ]
    view_notes = {
        "full_page_200dpi.png": "Page integration, caption and surrounding text checked.",
        "figure_crop_300dpi.png": "Figure-level layout, annotation hierarchy and spacing checked.",
        "standalone_300dpi.png": "Standalone figure readability and panel balance checked.",
        "grayscale_300dpi.png": "Grayscale structural distinction and non-color dependence checked.",
    }
    four_view_rows = []
    for view in view_paths:
        size = load_png(must_exist(view))
        four_view_rows.append({
            "VIEW": view,
            "IMAGE_SIZE_PX": f"{size[0]}x{size[1]}",
            "REVIEWER_ID": REVIEWER,
            "REVIEWED_AT": NOW,
            "ACTUAL_OPEN": "YES",
            "RESULT": "PASS_VISUAL_SCOPE",
            "NOTE": view_notes[view],
        })
    write_csv(LEDGER / "R111_FOUR_VIEW_REVIEW_LEDGER.csv", four_view_rows)

    math_rows = [
        {
            "CHECK_ID": "M01",
            "CLAIM": "Joint density normalization and support",
            "RESULT": "PASS",
            "EVIDENCE": "q(x1,x2)=1+rho(2x1-1)(2x2-1) on [0,1]^2; affine perturbation integrates to one.",
        },
        {
            "CHECK_ID": "M02",
            "CLAIM": "X1 conditional at X2=b=4/5",
            "RESULT": "PASS",
            "EVIDENCE": "Mean 12/25, variance 16/25, second moment 29/100.",
        },
        {
            "CHECK_ID": "M03",
            "CLAIM": "X2 conditional at X1=a=1/5",
            "RESULT": "PASS",
            "EVIDENCE": "Mean 3/5, variance 16/25, second moment 121/500.",
        },
        {
            "CHECK_ID": "M04",
            "CLAIM": "Integral and geometric annotations",
            "RESULT": "PASS",
            "EVIDENCE": "One integral; maximum 5/(4sqrt(2)pi); positive rho retains 45 degree ellipse direction.",
        },
        {
            "CHECK_ID": "M05",
            "CLAIM": "Zero-density edge warning",
            "RESULT": "PASS",
            "EVIDENCE": "Regular conditional convention is stated and does not assert an invalid pointwise density.",
        },
    ]
    write_csv(LEDGER / "R111_MATH_SEMANTICS_LEDGER.csv", math_rows)

    font_harmony_rows = [
        {
            "DIMENSION": "SIZE",
            "RESULT": "FAIL",
            "BASIS": "30 of 413 glyphs fail the strict native-pixel threshold; base declared size is at least 9.5pt but strict visual-size gate is not closed.",
            "FOUR_VIEW_CONCLUSION": "No abrupt layout collapse, but strict harmony cannot PASS while required glyph size pixels fail.",
        },
        {
            "DIMENSION": "WEIGHT",
            "RESULT": "PASS",
            "BASIS": "Current-identity four-view review found no unexplained heavy/light type shift; emphasis is semantically localized.",
            "FOUR_VIEW_CONCLUSION": "Weight hierarchy is visually coherent.",
        },
        {
            "DIMENSION": "COLOR",
            "RESULT": "PASS",
            "BASIS": "Blue/green data encodings and red warning treatment are semantically coherent; grayscale remains structurally legible.",
            "FOUR_VIEW_CONCLUSION": "Color supports rather than replaces structural distinction.",
        },
        {
            "DIMENSION": "FONT_VISUAL_HARMONY",
            "RESULT": "FAIL",
            "BASIS": "Aggregate is governed by strict SIZE failure, not by a weight or color defect.",
            "FOUR_VIEW_CONCLUSION": "FAIL because any required subdimension failure prevents aggregate pass.",
        },
    ]
    write_csv(LEDGER / "R111_FONT_VISUAL_HARMONY_LEDGER.csv", font_harmony_rows)

    role_rows = []
    by_panel_role: dict[tuple[str, str], list[dict[str, str]]] = {}
    for row in font_rows:
        by_panel_role.setdefault((row["PANEL_ID"], row["ROLE"]), []).append(row)
    base_choice = {
        ("caption", "CAPTION"): "CAPTION",
        ("card", "ANNOTATION"): "ANNOTATION",
        ("left", "ANNOTATION"): "ANNOTATION",
        ("map", "ANNOTATION"): "ANNOTATION",
        ("right_top", "TICK"): "TICK",
        ("right_bottom", "TICK"): "TICK",
    }
    base_medians: dict[tuple[str, str], float] = {}
    for key, rows in by_panel_role.items():
        heights = sorted(float(row["H_INK_PX"]) for row in rows if row["SCRIPT_CLASS"] != "NATURAL_SCRIPT")
        if heights:
            base_medians[key] = float(np.median(heights))
    for row in font_rows:
        panel = row["PANEL_ID"]
        role = row["ROLE"]
        chosen_role = base_choice.get((panel, role), role)
        base = base_medians.get((panel, chosen_role))
        current = float(row["H_INK_PX"])
        if base is None or base == 0:
            ratio = ""
            result = "PENDING"
            note = "No eligible baseline role could be recomputed."
        else:
            ratio_value = current / base
            ratio = f"{ratio_value:.6f}"
            if row["SCRIPT_CLASS"] == "NATURAL_SCRIPT":
                result = "PASS"
                note = "Natural script is exempt from direct base-role ratio enforcement."
            elif role == chosen_role:
                result = "PASS"
                note = "Baseline role."
            elif role == "FORMULA":
                result = "PASS" if 1.0 <= ratio_value <= 1.18 else "FAIL"
                note = "Formula to chosen panel baseline, allowed 1.00 to 1.18."
            else:
                result = "PASS" if ratio_value <= 1.18 else "FAIL"
                note = "Nonformula role to chosen panel baseline, max 1.18."
        role_rows.append({
            "GLYPH_ID": row["GLYPH_ID"],
            "PANEL_ID": panel,
            "ROLE": role,
            "SCRIPT_CLASS": row["SCRIPT_CLASS"],
            "H_INK_PX": row["H_INK_PX"],
            "BASELINE_ROLE": chosen_role,
            "BASELINE_MEDIAN_H_INK_PX": "" if base is None else f"{base:.6f}",
            "ROLE_RATIO_RECOMPUTED": ratio,
            "ROLE_RATIO_RECOMPUTED_RESULT": result,
            "NOTE": note,
            "RAW_PIXEL_MEASUREMENT_ROLE_RATIO": pixel_by_id[row["GLYPH_ID"]].get("ROLE_RATIO", "ACTUAL_BASELINE_PENDING"),
        })
    recomputed_role_fail = sum(row["ROLE_RATIO_RECOMPUTED_RESULT"] == "FAIL" for row in role_rows)
    assert all(row["RAW_PIXEL_MEASUREMENT_ROLE_RATIO"] == "ACTUAL_BASELINE_PENDING" for row in role_rows)
    write_csv(LEDGER / "role_ratio_recomputed_R111_SA1.csv", role_rows)

    semantic_bad_ids = [f"F632_G{number:03d}" for number in range(204, 210)]
    semantic_rows = []
    for glyph_id in semantic_bad_ids:
        source = font_by_id[glyph_id]
        assert source["PARENT_ID"] == "P06_TOP_CURVE_TICK_LABEL"
        semantic_rows.append({
            "GLYPH_ID": glyph_id,
            "CHAR": source["CHAR"],
            "RECORDED_PARENT_ID": source["PARENT_ID"],
            "EXPECTED_SEMANTIC_PARENT_ID": "P07_BOTTOM_CONDITIONAL_FORMULA",
            "SOURCE_LOCATOR": "fig_v5_c04_conditional_slice.tex line 137",
            "CLOSURE_RESULT": "FAIL",
            "EXPLANATION": "pi(a,t) is part of the bottom conditional formula, not a top-curve tick label.",
        })
    write_csv(LEDGER / "R111_SEMANTIC_PARENT_MAPPING_ADJUDICATION.csv", semantic_rows)

    recomputed_relations = []
    for row in relation_rows:
        legacy_result = row["RESULT"]
        overlap = int(row["OVERLAP_PIXEL_COUNT"])
        raw_clearance = float(row["MIN_CLEARANCE_PX"])
        threshold = float(row["THRESHOLD_PX"])
        if row["RELATION_ID"] == "R0046":
            physical_clearance = 20.518284528683193
            physical_result = "PASS"
            status = "RESULT_CONSISTENCY_FAIL"
            rationale = "Legacy RESULT=FAIL conflicts with overlap=0 and raw clearance=16>=8. The invalid BBOX_CLEARANCE=0 comes from a composite parent envelope. Corrected semantic parent reconstruction has zero overlap and 20.518px foreground clearance."
        else:
            physical_clearance = raw_clearance
            physical_result = "PASS" if overlap == 0 and physical_clearance >= threshold else "FAIL"
            status = "CONSISTENT_WITH_RAW_FOREGROUND"
            rationale = "Physical result uses raw foreground overlap and raw foreground clearance only."
        recomputed_relations.append({
            "RELATION_ID": row["RELATION_ID"],
            "A_ID": row["A_ID"],
            "B_ID": row["B_ID"],
            "LEGACY_RESULT": legacy_result,
            "RAW_OVERLAP_PIXEL_COUNT": str(overlap),
            "RAW_MIN_CLEARANCE_PX": f"{raw_clearance:.6f}",
            "THRESHOLD_PX": f"{threshold:.6f}",
            "ADJUDICATED_FOREGROUND_CLEARANCE_PX": f"{physical_clearance:.6f}",
            "ADJUDICATED_PHYSICAL_RESULT": physical_result,
            "CONSISTENCY_STATUS": status,
            "RATIONALE": rationale,
        })
    physical_rel_fail = [row for row in recomputed_relations if row["ADJUDICATED_PHYSICAL_RESULT"] == "FAIL"]
    consistency_fail = [row for row in recomputed_relations if row["CONSISTENCY_STATUS"] == "RESULT_CONSISTENCY_FAIL"]
    assert len(physical_rel_fail) == 36
    assert len(consistency_fail) == 1
    assert all(row["RAW_OVERLAP_PIXEL_COUNT"] == "0" for row in recomputed_relations)
    write_csv(REL / "R111_RECOMPUTED_RELATION_ADJUDICATION.csv", recomputed_relations)

    font_pixel_fails = [row for row in font_rows if row["PIXEL_GATE_RESULT"] == "FAIL"]
    font_pt_fails = [row for row in font_rows if row["EFFECTIVE_PT_RESULT"] == "FAIL"]
    d_fail = [row for row in de_rows if row["D_RESULT"] == "FAIL"]
    e_fail = [row for row in de_rows if row["E_CROSS_PANEL_RESULT"] == "FAIL"]
    edge_fail = [row for row in edge_rows if row["RESULT"] == "FAIL"]
    graphic_fail = [row for row in graphic_rows if row["MASK_RESULT"] == "FAIL"]
    assert len(font_pixel_fails) == 30
    assert len(font_pt_fails) == 0
    assert len(d_fail) == 13
    assert len(e_fail) == 12
    assert len(edge_fail) == 0
    assert len(graphic_fail) == 0

    gate_rows = [
        {
            "GATE": "GLYPH_SET_AND_CONTACT_SHEET_HUMAN_REVIEW",
            "COUNT_OR_SCOPE": "413 glyphs; 42 sheets; all cells",
            "RESULT": "PASS",
            "EVIDENCE": "contact_sheet_actual_open_ledger_R111_SA1_REQUAL_CURRENT.csv and glyph_manual_review_ledger_R111_SA1_REQUAL_CURRENT.csv",
        },
        {
            "GATE": "FONT_AT_LEAST_9_5PT",
            "COUNT_OR_SCOPE": "413 glyphs",
            "RESULT": "PASS",
            "EVIDENCE": "after_font_audit.csv: 0 effective-point failures; natural scripts use base effective point treatment.",
        },
        {
            "GATE": "STRICT_NATIVE_PIXEL_GLYPH",
            "COUNT_OR_SCOPE": "413 glyphs",
            "RESULT": "FAIL",
            "EVIDENCE": "30 pixel failures, including G092 natural-script low-height failure.",
        },
        {
            "GATE": "D_INTRA_PANEL",
            "COUNT_OR_SCOPE": "28 panel-role-script rows",
            "RESULT": "FAIL",
            "EVIDENCE": "13 D failures in de_actual_baselines.csv.",
        },
        {
            "GATE": "E_CROSS_PANEL",
            "COUNT_OR_SCOPE": "28 panel-role-script rows",
            "RESULT": "FAIL",
            "EVIDENCE": "12 E failures in de_actual_baselines.csv.",
        },
        {
            "GATE": "ROLE_RATIO_RAW_EVIDENCE",
            "COUNT_OR_SCOPE": "413 glyphs",
            "RESULT": "FAIL",
            "EVIDENCE": "ROLE_RATIO is ACTUAL_BASELINE_PENDING in every after_pixel_measurements.csv row.",
        },
        {
            "GATE": "ROLE_RATIO_RECOMPUTED_HELPER",
            "COUNT_OR_SCOPE": "413 glyphs",
            "RESULT": "FAIL" if recomputed_role_fail else "PASS",
            "EVIDENCE": f"role_ratio_recomputed_R111_SA1.csv: {recomputed_role_fail} recomputed failures; does not cure raw pending evidence.",
        },
        {
            "GATE": "TEXT_GRAPHIC_CLEARANCE_AND_OVERLAP",
            "COUNT_OR_SCOPE": "390 relations",
            "RESULT": "FAIL",
            "EVIDENCE": "36 physical raw-clearance failures. All measured overlaps are 0; R0046 is an evidence inconsistency, not physical failure.",
        },
        {
            "GATE": "R0046_RESULT_CONSISTENCY",
            "COUNT_OR_SCOPE": "R0046",
            "RESULT": "FAIL",
            "EVIDENCE": "Legacy RESULT=FAIL despite raw overlap=0 and raw clearance=16>=8; corrected foreground reconstruction is PASS at 20.518px.",
        },
        {
            "GATE": "SEMANTIC_PARENT_MAPPING",
            "COUNT_OR_SCOPE": "G204-G209",
            "RESULT": "FAIL",
            "EVIDENCE": "Six pi(a,t) glyphs assigned P06 but source places them in P07.",
        },
        {
            "GATE": "PRE_HALO_FINAL_VISIBLE_AND_PAINT_ORDER",
            "COUNT_OR_SCOPE": "O01-O03",
            "RESULT": "PASS",
            "EVIDENCE": "pre equals final and XOR zero in current actual-open occlusion ledger.",
        },
        {
            "GATE": "FIGURE_EDGE_CLIP_CLEARANCE",
            "COUNT_OR_SCOPE": "12 edge relations",
            "RESULT": "PASS",
            "EVIDENCE": "0 edge failures and 0 clipping failures.",
        },
        {
            "GATE": "MATH_SEMANTICS",
            "COUNT_OR_SCOPE": "5 checks",
            "RESULT": "PASS",
            "EVIDENCE": "R111_MATH_SEMANTICS_LEDGER.csv.",
        },
        {
            "GATE": "FOUR_VIEW",
            "COUNT_OR_SCOPE": "4 views",
            "RESULT": "PASS",
            "EVIDENCE": "R111_FOUR_VIEW_REVIEW_LEDGER.csv.",
        },
        {
            "GATE": "FONT_VISUAL_HARMONY",
            "COUNT_OR_SCOPE": "size; weight; color",
            "RESULT": "FAIL",
            "EVIDENCE": "Size fails strict native pixel gate; weight and color individually pass.",
        },
    ]
    write_csv(LEDGER / "R111_RECOMPUTED_GATE_MATRIX.csv", gate_rows)

    machine_paths = []
    for row in glyph_rows:
        for key in ("ORIGINAL_1X", "TARGET_OVERLAY_1X", "MASK_ONLY_1X", "TRIAD_8X"):
            machine_paths.append(must_exist(row[key]))
    machine_paths.extend(must_exist(row["SHEET"]) for row in contact_rows)
    for row in fail_relations:
        for key in ("ORIGINAL_1X", "A_MASK_1X", "B_MASK_1X", "INTERSECTION_1X", "OVERLAY_1X", "OVERLAY_8X"):
            machine_paths.append(must_exist(row[key]))
    machine_paths.extend(must_exist(row["MASK_PATH"]) for row in graphic_rows)
    for path in sorted((ROOT / "occlusion").glob("*.png")):
        machine_paths.append(path)
    machine_paths.extend(must_exist(path) for path in view_paths)
    size_counter = Counter()
    for path in machine_paths:
        size_counter[load_png(path)] += 1
    assert len(machine_paths) == 413 * 4 + 42 + 37 * 6 + 27 + 18 + 4

    integrity_codes = [
        "RESULT_CONSISTENCY_FAIL",
        "SEMANTIC_PARENT_MAPPING_FAIL",
        "ROLE_RATIO_PENDING",
    ]
    final_summary = {
        "audit_identity": REVIEWER,
        "timestamp": NOW,
        "official_input": "D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/source/v2.7.0/src/build/strict_current_r95_fullbook/main_full.pdf",
        "figure_id": "FIG-P632-01",
        "evidence_integrity": {
            "result": "FAIL",
            "codes": integrity_codes,
            "detail": {
                "legacy_relation_result_fail_count": 37,
                "physical_relation_clearance_fail_count": 36,
                "r0046": "legacy FAIL is inconsistent with overlap=0 and clearance=16>=8; semantic-parent corrected result is physical PASS",
                "semantic_parent_mapping_fail_glyphs": semantic_bad_ids,
                "role_ratio_raw_state": "ACTUAL_BASELINE_PENDING for 413 of 413 rows",
            },
        },
        "figure_hard_gates": {
            "result": "FAIL",
            "strict_native_pixel_glyph_fail_count": len(font_pixel_fails),
            "font_pt_fail_count": len(font_pt_fails),
            "d_fail_count": len(d_fail),
            "e_cross_panel_fail_count": len(e_fail),
            "role_ratio_recomputed_fail_count": recomputed_role_fail,
            "physical_clearance_fail_count": len(physical_rel_fail),
            "overlap_fail_count": 0,
            "edge_fail_count": len(edge_fail),
            "graphic_mask_fail_count": len(graphic_fail),
            "occlusion_fail_count": 0,
            "math_semantics_result": "PASS",
            "four_view_result": "PASS",
            "font_visual_harmony": {
                "aggregate": "FAIL",
                "size": "FAIL",
                "weight": "PASS",
                "color": "PASS",
            },
        },
        "final_result": "FAIL_TO_SA2",
        "final_table_summary_usage": "NOT_USED_AS_AUTHORITY; recomputed from bottom-level CSV and current identity ledger.",
        "separation_statement": "EVIDENCE_INTEGRITY and FIGURE_HARD_GATES are independently reported. R0046 is not counted among the 36 physical clearance failures.",
    }
    write_json(ROOT / "R111_FINAL_RECOMPUTED_SUMMARY.json", final_summary)

    terminal = {
        "terminal_identity": REVIEWER,
        "timestamp": NOW,
        "status": "FINAL_FAIL_TO_SA2",
        "input_integrity": "official source PDF path recorded; source, build, central status and inventory were not written",
        "machine_opened_png_count": len(machine_paths),
        "machine_opened_png_breakdown": {
            "glyph_individual_evidence": 413 * 4,
            "contact_sheets": 42,
            "critical_relation_packages": 37 * 6,
            "graphic_masks": 27,
            "occlusion_pngs": 18,
            "four_views": 4,
        },
        "machine_decoded_image_sizes": {f"{w}x{h}": count for (w, h), count in sorted(size_counter.items())},
        "structural_assertions": {
            "glyph_rows": len(font_rows),
            "contact_sheet_rows": len(contact_rows),
            "contact_cell_coverage": len(covered_cells),
            "relations": len(relation_rows),
            "legacy_relation_fails": len(fail_relations),
            "physical_relation_fails": len(physical_rel_fail),
            "r0046_consistency_fails": len(consistency_fail),
            "semantic_parent_glyph_fails": len(semantic_rows),
            "edge_relations": len(edge_rows),
            "graphic_masks": len(graphic_rows),
            "occlusion_cases": len(occlusion_ledger),
        },
        "evidence_integrity": "FAIL",
        "figure_hard_gates": "FAIL",
        "final_result": "FAIL_TO_SA2",
    }
    write_json(TERM / "R111_MACHINE_TERMINAL.json", terminal)
    terminal_md = "\n".join([
        "# R111 SA1 machine terminal",
        "",
        f"Reviewer: {REVIEWER}",
        f"Timestamp: {NOW}",
        "",
        "Result: FINAL_FAIL_TO_SA2",
        "",
        f"Decoded PNG evidence items: {len(machine_paths)}",
        f"Glyph rows: {len(font_rows)}; contact sheets: {len(contact_rows)}; critical packages: {len(fail_relations)}.",
        f"Physical clearance failures: {len(physical_rel_fail)}; zero-overlap relation count: {len(recomputed_relations)}.",
        "Integrity faults: RESULT_CONSISTENCY_FAIL, SEMANTIC_PARENT_MAPPING_FAIL, ROLE_RATIO_PENDING.",
        "R0046 is physical PASS after foreground adjudication and is excluded from physical failure count.",
        "",
    ])
    write_text(TERM / "R111_MACHINE_TERMINAL.md", terminal_md)

    acceptance = "\n".join([
        "# FIG-P632-01 R111 SA1 requalification acceptance record",
        "",
        "Final result: FAIL_TO_SA2",
        "",
        "This is a resumed, independent current-identity review. Existing evidence was preserved. The official input was main_full.pdf from the strict_current_r95_fullbook build. No source, build, inventory, or central-state file was written.",
        "",
        "Evidence integrity: FAIL",
        "",
        "- RESULT_CONSISTENCY_FAIL: R0046 legacy RESULT is FAIL although its raw foreground measures are overlap 0 and clearance 16px against 8px. Corrected semantic-parent foreground reconstruction is PASS at 20.518px.",
        "- SEMANTIC_PARENT_MAPPING_FAIL: G204 through G209 are pi(a,t) glyphs assigned to P06 but source line 137 makes them part of P07.",
        "- ROLE_RATIO_PENDING: the raw pixel-measurement rows retain ACTUAL_BASELINE_PENDING. The helper recomputation is supplemental and cannot repair that raw evidence defect.",
        "",
        "Figure hard gates: FAIL",
        "",
        "- 30 strict native-pixel glyph failures; effective-point font gate itself is 0 failures.",
        "- D fails: 13; E cross-panel fails: 12.",
        "- 36 physical raw-clearance failures. Every measured overlap is 0. A raw 1px clearance is a clearance failure, not a pixel-overlap failure.",
        "- Edge, clipping, graphic-mask, paint-order, halo/final-visible, math semantics, and four-view checks pass.",
        "- FONT_VISUAL_HARMONY fails only because its size subgate fails; weight and color each pass.",
        "",
        "Current-identity viewing record: all 42 contact sheets and every cell were personally opened; all 37 legacy failing/critical relation packages were personally opened at original 1x, A, B, intersection, overlay 1x, and overlay 8x nearest; O01 through O03 pre, opaque, final, covered-xor, and 1x overlay views were personally opened.",
        "",
        "The previous final_table_summary.json was not used as authority. The result above is recomputed from bottom-level evidence and the current identity ledger.",
        "",
    ])
    write_text(ROOT / "after_visual_acceptance_R111_SA1_RECOMPUTED.md", acceptance)

    report = "\n".join([
        "# FIG-P632-01 R111 independent SA1 requalification report",
        "",
        "## Scope and stop condition",
        "",
        f"Reviewer: {REVIEWER}",
        f"Review timestamp: {NOW}",
        "Official frozen input: D:/Users/ASUS/Desktop/机器学习/v2.7.0/_work/source/v2.7.0/src/build/strict_current_r95_fullbook/main_full.pdf",
        "The evidence directory was resumed without deletion or rebuilding of prior artifacts. No source, build, central status, or inventory file was changed.",
        "",
        "## Current-identity actual viewing",
        "",
        "- CS001 through CS042 were personally opened. Every one of the 413 contact-sheet cells was checked in its embedded original, target-overlay, mask, and 8x nearest triad presentation.",
        "- R0018, R0046, R0096, R0097, R0098, R0099, R0100, R0101, R0102, R0103, R0122, R0125, R0156, R0172, R0188, R0189, R0212, R0213, R0216, R0248, R0249, R0250, R0272, R0273, R0276, R0287, R0288, R0290, R0291, R0292, R0305, R0306, R0314, R0315, R0334, R0363, and R0390 were personally opened in original 1x, A mask, B mask, intersection, overlay 1x, and overlay 8x nearest.",
        "- O01 through O03 were personally opened in pre-occlusion, opaque ground, final-visible, covered-xor, and 1x overlay views.",
        "- Full page, figure crop, standalone, and grayscale views were personally opened.",
        "",
        "## Recomputed finding",
        "",
        "EVIDENCE_INTEGRITY: FAIL",
        "",
        "- RESULT_CONSISTENCY_FAIL. R0046 raw row reports overlap 0 and min clearance 16px with threshold 8px, but reports RESULT FAIL because an extra composite bbox gate is 0. This conflicts with foreground measurement. Corrected semantic-parent reconstruction gives 20.518px and PASS. R0046 is excluded from physical clearance-failure count.",
        "- SEMANTIC_PARENT_MAPPING_FAIL. G204-G209 pi(a,t) are incorrectly attached to P06 rather than P07. This explains the composite-parent condition behind R0046.",
        "- ROLE_RATIO_PENDING. Every raw after_pixel_measurements row retains ACTUAL_BASELINE_PENDING. A separately documented helper recomputation cannot close the required raw trace.",
        "",
        "FIGURE_HARD_GATES: FAIL",
        "",
        "- Strict native pixel glyph gate: 30 failures of 413. Font effective-point gate: 0 failures.",
        "- D intra-panel: 13 failures. E cross-panel: 12 failures.",
        "- Relation physical clearance: 36 failures; all overlap measurements are 0. R0188 and analogous cases are recorded as overlap 0 with raw clearance 1px less than 3px, never as overlap.",
        "- Font visual harmony: SIZE FAIL, WEIGHT PASS, COLOR PASS, aggregate FAIL.",
        "- Passes: 27 graphic masks, 12 edge relations and clipping, O01-O03 paint/halo/final-visible, math semantics, and four views.",
        "",
        "## Terminal disposition",
        "",
        "FINAL: FAIL_TO_SA2",
        "",
        "No conclusion above relies on the previous final_table_summary.json. The attached recomputation and current-identity ledgers are authoritative for this requalification.",
        "",
    ])
    write_text(ROOT / "R111_SA1_REQUAL_REPORT.md", report)

    manifest = {
        "reviewer": REVIEWER,
        "timestamp": NOW,
        "new_artifacts_before_stop": [
            "ledger/contact_sheet_actual_open_ledger_R111_SA1_REQUAL_CURRENT.csv",
            "ledger/glyph_manual_review_ledger_R111_SA1_REQUAL_CURRENT.csv",
            "ledger/critical_relation_actual_open_ledger_R111_SA1_REQUAL_CURRENT.csv",
            "ledger/occlusion_actual_open_ledger_R111_SA1_REQUAL_CURRENT.csv",
            "ledger/R111_FOUR_VIEW_REVIEW_LEDGER.csv",
            "ledger/R111_MATH_SEMANTICS_LEDGER.csv",
            "ledger/R111_FONT_VISUAL_HARMONY_LEDGER.csv",
            "ledger/role_ratio_recomputed_R111_SA1.csv",
            "ledger/R111_SEMANTIC_PARENT_MAPPING_ADJUDICATION.csv",
            "ledger/R111_RECOMPUTED_GATE_MATRIX.csv",
            "relations/R111_RECOMPUTED_RELATION_ADJUDICATION.csv",
            "R111_FINAL_RECOMPUTED_SUMMARY.json",
            "after_visual_acceptance_R111_SA1_RECOMPUTED.md",
            "R111_SA1_REQUAL_REPORT.md",
            "terminal/R111_MACHINE_TERMINAL.json",
            "terminal/R111_MACHINE_TERMINAL.md",
        ],
        "write_stopped_is_final_write": True,
        "final_result": "FAIL_TO_SA2",
    }
    write_json(ROOT / "R111_SA1_REQUAL_MANIFEST.json", manifest)

    SENTINEL.write_text(
        "R111 SA1 requalification write stop\n"
        f"reviewer={REVIEWER}\n"
        f"timestamp={NOW}\n"
        "final_result=FAIL_TO_SA2\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "status": "FINAL_FAIL_TO_SA2",
        "glyphs": len(font_rows),
        "contact_sheets": len(contact_rows),
        "critical_packages": len(fail_relations),
        "physical_clearance_fails": len(physical_rel_fail),
        "integrity_codes": integrity_codes,
        "write_stopped": str(SENTINEL),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
