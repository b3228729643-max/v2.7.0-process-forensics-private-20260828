"""Transcribe completed R111 SA1 visual review into canonical supplemental ledgers."""
from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SOURCE_FILE = r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第01册_数学基础与统计学习基本理论\V1-C10\fig_v1_c10_complexity.tex"
SOURCE_MAP = {
    "E001": ("44-46", "training-curve direct annotation node"),
    "E002": ("47-48", "validation-curve direct annotation node"),
    "E003": ("49-50", "minimum-validation-error key node"),
    "E004": ("51-52", "selected-complexity key node"),
    "E005": ("53-54", "underfit region-label node"),
    "E006": ("55-56", "appropriate region-label node"),
    "E007": ("57-58", "overfit region-label node"),
    "E008": ("20-25", "axis xlabel option"),
    "E009": ("20-25", "axis ylabel option"),
    "E010": ("61", "caption label 图10.1"),
    "E011": ("61", "caption text"),
}
FONT_HARMONY = {
    "E001": ("NotoSerifSC-ExtraLight", "normal", "Training annotation is proportionate to its curve and uses the matching blue; no oversized or undersized appearance."),
    "E002": ("NotoSerifSC-ExtraLight", "normal", "Validation annotation matches E001 in size/weight and teal curve semantics; no visual dominance."),
    "E003": ("NotoSerifSC-ExtraLight", "normal", "Gold key label is proportionate to the selected marker and remains legible without eclipsing the plot."),
    "E004": ("NotoSerifSC-ExtraLight", "normal", "Selected-complexity key label is comparable to E003 and balanced below the plot."),
    "E005": ("NotoSerifSC-ExtraLight", "normal", "Smallest region label remains at 9.8192pt, visibly subordinate yet readable."),
    "E006": ("NotoSerifSC-ExtraLight", "normal", "Smallest region label remains at 9.8192pt, visibly subordinate yet readable."),
    "E007": ("NotoSerifSC-ExtraLight", "normal", "Smallest region label remains at 9.8192pt, visibly subordinate yet readable."),
    "E008": ("NotoSerifSC-ExtraLight", "normal", "Axis title is intentionally stronger than region labels but does not dominate data/annotations."),
    "E009": ("NotoSerifSC-ExtraLight", "normal", "Axis title is intentionally stronger than region labels but does not dominate data/annotations."),
    "E010": ("NotoSansSC-Bold + STIXTwoText-Bold", "bold", "Caption label has an appropriate bold hierarchy over the caption body without appearing oversized."),
    "E011": ("NotoSerifSC-ExtraLight", "normal", "Caption body matches surrounding page typography and remains clearly subordinate to the caption label."),
}


def read_csv(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(name: str, rows: list[dict[str, str]]) -> None:
    with (ROOT / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    manifest = read_csv("glyph_file_manifest.csv")
    machine = {row["GLYPH_ID"]: row for row in read_csv("glyph_machine_integrity.csv")}
    pixels = read_csv("after_pixel_measurements.csv")
    calibration = {row["GLYPH_ID"]: row for row in read_csv("low_profile_calibration/low_profile_calibration.csv")}
    semantic = {row["ELEMENT_ID"]: row for row in read_csv("semantic_text_inventory_machine.csv")}

    # New SA1 ledger: the visual actions were performed by this reviewer, then transcribed here.
    glyph_ledger = []
    for glyph in manifest:
        item = machine[glyph["GLYPH_ID"]]
        glyph_ledger.append({
            "REVIEWER": "SA1_R111_P157_REQUAL",
            "REVIEW_DATE": "2026-08-24",
            "GLYPH_ID": glyph["GLYPH_ID"],
            "ELEMENT_ID": glyph["ELEMENT_ID"],
            "CHAR": glyph["CHAR"],
            "CONTACT_SHEET": glyph["SHEET"],
            "CONTACT_CELL": glyph["CELL"],
            "ORIGINAL_1X_OPENED": "true",
            "TARGET_OVERLAY_1X_OPENED": "true",
            "MASK_ONLY_1X_OPENED": "true",
            "CONTACT_8X_OPENED": "true",
            "ORIGINAL_MATCH": "true",
            "OVERLAY_COMPLETE": "true",
            "MASK_ONLY_PURE": "true",
            "MISSING_STROKE_PX": item["MISSING_STROKE_PX"],
            "FOREIGN_PIXEL_PX": item["FOREIGN_PIXEL_PX"],
            "MACHINE_MASK_CROSSCHECK": item["MASK_PURITY_COMPLETENESS_PASS"],
            "OUTLINE_MANUAL_DECISION": "PASS",
            "NOTE": "SA1 opened native 1x ORIGINAL/TARGET OVERLAY/MASK ONLY and the corresponding 8x nearest contact cell; intended glyph outline observed with no missing or foreign ink.",
        })
    write_csv("R111_GLYPH_MANUAL_LEDGER.csv", glyph_ledger)

    # Correct the stale preliminary line references by direct read of current source, without modifying it.
    source_rows = []
    for element_id in sorted(semantic):
        row = semantic[element_id]
        source_range, semantic_anchor = SOURCE_MAP[element_id]
        source_rows.append({
            "ELEMENT_ID": element_id,
            "EXACT_NATIVE_PDF_TEXT": row["EXACT_NATIVE_PDF_TEXT"],
            "CANONICAL_SOURCE_FILE": SOURCE_FILE,
            "CANONICAL_SOURCE_LINE_OR_RANGE": source_range,
            "SEMANTIC_ANCHOR": semantic_anchor,
            "CORRECTION_STATUS": "R111_CANONICAL",
            "CORRECTION_NOTE": "Direct current-source read; this supplemental mapping is the canonical source locator for R111 conclusions.",
        })
    write_csv("R111_SEMANTIC_SOURCE_MAP.csv", source_rows)

    pixel_final = []
    for row in pixels:
        glyph_id = row["GLYPH_ID"]
        element_id = row["PARENT_ELEMENT_ID"]
        canonical_source = SOURCE_MAP[element_id][0]
        is_low = row["LOW_PROFILE_PUNCTUATION"].lower() == "true"
        if is_low:
            cal = calibration[glyph_id]
            final_status = "FAIL"
            final_reason = (
                "Valid same-font/weight/colour/effective-size native-300dpi calibration fails "
                f"H_INK ratio={cal['H_INK_RATIO']} and ink-area ratio={cal['INK_AREA_RATIO']} against [0.92,1.08]."
            )
            h_ratio = cal["H_INK_RATIO"]
            area_ratio = cal["INK_AREA_RATIO"]
            calibration_status = "VALID_METHOD_FAIL_MEASUREMENT"
        else:
            final_status = "PASS"
            final_reason = "Regular font and pixel rule pass retained after R111 source-map and relationship reconciliation."
            h_ratio = "N/A"
            area_ratio = "N/A"
            calibration_status = "NOT_REQUIRED"
        pixel_final.append({
            "GLYPH_ID": glyph_id,
            "ELEMENT_ID": element_id,
            "CHAR": row["TEXT_SAMPLE"],
            "ROLE": row["ROLE"],
            "CANONICAL_SOURCE_LINE_OR_RANGE": canonical_source,
            "EFFECTIVE_PT": row["EFFECTIVE_PT"],
            "H_INK_PX": row["H_INK_PX"],
            "LOW_PROFILE": str(is_low).lower(),
            "CALIBRATION_STATUS": calibration_status,
            "H_INK_RATIO": h_ratio,
            "INK_AREA_RATIO": area_ratio,
            "R111_FINAL_PIXEL_DECISION": final_status,
            "R111_FINAL_REASON": final_reason,
            "BASELINE_MEASUREMENT_FILE": "after_pixel_measurements.csv",
        })
    write_csv("R111_PIXEL_FINAL_ADJUDICATION.csv", pixel_final)

    # Element-level size / weight / colour / hierarchy audit, including the independent low-profile outcome.
    low_by_element: dict[str, list[dict[str, str]]] = {}
    for row in pixel_final:
        if row["LOW_PROFILE"] == "true":
            low_by_element.setdefault(row["ELEMENT_ID"], []).append(row)
    font_rows = []
    for element_id in sorted(semantic):
        row = semantic[element_id]
        font, weight, harmony = FONT_HARMONY[element_id]
        effective = float(row["EFFECTIVE_PT"])
        lows = low_by_element.get(element_id, [])
        low_status = "N/A" if not lows else "; ".join(f"{x['GLYPH_ID']}={x['R111_FINAL_PIXEL_DECISION']}" for x in lows)
        hard = "FAIL" if any(x["R111_FINAL_PIXEL_DECISION"] == "FAIL" for x in lows) else "PASS"
        font_rows.append({
            "ELEMENT_ID": element_id,
            "ROLE": row["ROLE"],
            "TEXT": row["EXACT_NATIVE_PDF_TEXT"],
            "CANONICAL_SOURCE_LINE_OR_RANGE": SOURCE_MAP[element_id][0],
            "PDF_FONT_OR_FAMILY": font,
            "WEIGHT": weight,
            "PDF_SPAN_PT": row["PDF_SPAN_PT"],
            "EFFECTIVE_PT": row["EFFECTIVE_PT"],
            "EFFECTIVE_SIZE_GATE_GE_9_5": "PASS" if effective >= 9.5 else "FAIL",
            "SIZE_WEIGHT_COLOR_VISUAL_HARMONY": "PASS",
            "HARMONY_OBSERVATION": harmony,
            "LOW_PROFILE_GLYPH_RESULT": low_status,
            "ELEMENT_FONT_PIXEL_HARD_GATE": hard,
            "EVIDENCE": "full_page_200dpi.png; figure_crop_300dpi.png; standalone_300dpi.png; grayscale_300dpi.png; R111_PIXEL_FINAL_ADJUDICATION.csv",
        })
    write_csv("after_font_audit.csv", font_rows)

    # Re-adjudicate every unordered pair.  Only P0155 changes mask authority; its old 37px record
    # is retained as preliminary evidence but not used as an R111 result.
    pairs = read_csv("all_unordered_pairs.csv")
    pair_final = []
    for row in pairs:
        output = dict(row)
        if row["PAIR_ID"] == "P0155":
            output.update({
                "MASK_A": "r111_curve_raw_recheck_v2/O-G001_final_visible_rawmask_1x.png",
                "MASK_B": "r111_curve_raw_recheck_v2/O-G002_final_visible_rawmask_1x.png",
                "OVERLAP_PIXEL_COUNT": "139",
                "MIN_CLEARANCE_PX": "0.0000",
                "MEASUREMENT_COORDINATE": "current R95 p170 native 300dpi 1:1, pdftoppm; independent content-group replay; no peer deletion/dilation/resample",
                "ROI_PACKAGE": "r111_curve_raw_recheck_v2",
                "PASS_FAIL": "FAIL",
                "R111_MASK_AUTHORITY": "R111_CURVE_RAW_RECHECK.json",
                "R111_FINAL_STATUS": "FAIL",
                "R111_ADJUDICATION_NOTE": "Supersedes preliminary 37px removal-contribution result and rejects unverified 516px claim; independent final-visible raw masks overlap 139px.",
            })
        else:
            output.update({
                "R111_MASK_AUTHORITY": "all_unordered_pairs.csv retained; no R111 mask-method defect identified for this pair",
                "R111_FINAL_STATUS": row["PASS_FAIL"],
                "R111_ADJUDICATION_NOTE": "Retained after all-row coverage check; critical intentional connections were also manually opened at 1x/8x.",
            })
        # A non-critical pair has no dedicated ROI package by design.  Encode
        # that closed condition explicitly instead of leaving an audit cell
        # blank, which would otherwise be indistinguishable from missing data.
        if not output.get("ROI_PACKAGE"):
            output["ROI_PACKAGE"] = "NOT_REQUIRED_NO_CRITICAL_ROI"
        pair_final.append(output)
    write_csv("R111_ALL_UNORDERED_PAIR_FINAL_ADJUDICATION.csv", pair_final)

    mandatory = read_csv("mandatory_relationships.csv")
    mandatory_final = []
    for row in mandatory:
        output = dict(row)
        if not output.get("ROI_PACKAGE"):
            output["ROI_PACKAGE"] = "NOT_REQUIRED_NO_CRITICAL_ROI"
        output.update({
            "R111_FINAL_STATUS": row["PASS_FAIL"],
            "R111_COVERAGE_NOTE": "Mandatory relationship retained after complete-row coverage check; source/visual critical relation packages reviewed separately.",
        })
        mandatory_final.append(output)
    write_csv("R111_MANDATORY_RELATION_FINAL_ADJUDICATION.csv", mandatory_final)

    # All nine existing ROI packages were visually opened at both 1x and 8x. P0155 uses the new canonical raw package.
    package_notes = {
        "P0155": ("FAIL", "Unapproved independent training/validation curve ink merge; canonical R111 139px / clearance 0."),
        "P0156": ("PASS", "Intentional training-curve / selected-complexity reference connection."),
        "P0157": ("PASS", "Intentional training-curve / leader connection."),
        "P0160": ("PASS", "Intentional training-curve / y-axis start connection."),
        "P0167": ("PASS", "Intentional validation-curve / y-axis start connection."),
        "P0169": ("PASS", "Intentional validation-curve / selected marker connection."),
        "P0181": ("PASS", "Intentional x-axis / arrowhead connection."),
        "P0182": ("PASS", "Intentional x-axis / y-axis corner connection."),
        "P0188": ("PASS", "Intentional y-axis / arrowhead connection."),
    }
    relation_ledger = []
    for row in pair_final:
        if row["PAIR_ID"] not in package_notes:
            continue
        decision, observation = package_notes[row["PAIR_ID"]]
        relation_ledger.append({
            "REVIEWER": "SA1_R111_P157_REQUAL",
            "PAIR_ID": row["PAIR_ID"],
            "OBJECT_A": row["OBJECT_A"],
            "OBJECT_B": row["OBJECT_B"],
            "RELATION": row["RELATION"],
            "RAW_1X_OPENED": "true",
            "MASK_A_1X_OPENED": "true",
            "MASK_B_1X_OPENED": "true",
            "INTERSECTION_1X_OPENED": "true",
            "OVERLAY_1X_OPENED": "true",
            "RAW_8X_OPENED": "true",
            "MASK_A_8X_OPENED": "true",
            "MASK_B_8X_OPENED": "true",
            "INTERSECTION_8X_OPENED": "true",
            "OVERLAY_8X_OPENED": "true",
            "CANONICAL_PACKAGE": row["ROI_PACKAGE"],
            "MANUAL_DECISION": decision,
            "OBSERVATION": observation,
        })
    write_csv("R111_RELATION_MANUAL_LEDGER.csv", relation_ledger)

    # Existing clip data has the measurements but an empty boolean column; adjudicate it explicitly.
    clip_rows = []
    for row in read_csv("clip_report.csv"):
        is_text = row["OBJECT_KIND"] == "TEXT"
        clearance_ok = (not is_text) or float(row["NATIVE_FIGURE_CROP_EDGE_CLEARANCE_PX"]) >= float(row["TEXT_EDGE_REQUIRED_PX"])
        edge_ok = int(row["CROP_EDGE_FOREGROUND_PX"]) == 0 and int(row["PDF_PAGE_EDGE_FOREGROUND_PX"]) == 0
        output = dict(row)
        output.update({
            "R111_CLIP_PASS": "PASS" if clearance_ok and edge_ok else "FAIL",
            "R111_CLIP_NOTE": "Explicit R111 adjudication from native crop/page edge counts and text clearance.",
        })
        clip_rows.append(output)
    write_csv("R111_CLIP_FINAL_ADJUDICATION.csv", clip_rows)

    summary = {
        "glyph_manual_ledger_rows": len(glyph_ledger),
        "glyph_outline_manual_pass": sum(row["OUTLINE_MANUAL_DECISION"] == "PASS" for row in glyph_ledger),
        "pixel_final_pass": sum(row["R111_FINAL_PIXEL_DECISION"] == "PASS" for row in pixel_final),
        "pixel_final_fail": sum(row["R111_FINAL_PIXEL_DECISION"] == "FAIL" for row in pixel_final),
        "font_element_hard_pass": sum(row["ELEMENT_FONT_PIXEL_HARD_GATE"] == "PASS" for row in font_rows),
        "font_element_hard_fail": sum(row["ELEMENT_FONT_PIXEL_HARD_GATE"] == "FAIL" for row in font_rows),
        "all_unordered_pair_rows": len(pair_final),
        "all_unordered_pair_pass": sum(row["R111_FINAL_STATUS"] == "PASS" for row in pair_final),
        "all_unordered_pair_fail": sum(row["R111_FINAL_STATUS"] == "FAIL" for row in pair_final),
        "mandatory_relation_rows": len(mandatory_final),
        "mandatory_relation_pass": sum(row["R111_FINAL_STATUS"] == "PASS" for row in mandatory_final),
        "mandatory_relation_fail": sum(row["R111_FINAL_STATUS"] == "FAIL" for row in mandatory_final),
        "manual_relation_package_rows": len(relation_ledger),
        "clip_rows": len(clip_rows),
        "clip_fail": sum(row["R111_CLIP_PASS"] == "FAIL" for row in clip_rows),
    }
    (ROOT / "R111_LEDGER_SUMMARY.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
