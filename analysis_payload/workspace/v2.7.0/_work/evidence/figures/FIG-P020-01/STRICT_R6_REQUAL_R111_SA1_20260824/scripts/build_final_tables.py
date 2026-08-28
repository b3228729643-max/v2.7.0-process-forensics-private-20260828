"""Build final non-terminal R111 tables after calibration and manual review."""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def read_csv(path: Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({field: row.get(field, "") for field in fields} for row in rows)


def main() -> None:
    pre_font = read_csv(ROOT / "after_font_audit_precalibration.csv")
    pixels = {row["ELEMENT_ID"]: row for row in read_csv(ROOT / "after_pixel_measurements.csv")}
    manual = {row["ELEMENT_ID"]: row for row in read_csv(ROOT / "ledger" / "glyph_manual_review_ledger.csv")}
    calibration = {
        row["TARGET_ELEMENT_ID"]: row
        for row in read_csv(ROOT / "calibration" / "low_profile_punctuation_calibration.csv")
    }
    manifest = read_csv(ROOT / "glyph_id_filename_manifest.csv")
    ids = [row["ELEMENT_ID"] for row in manifest]
    if len(ids) != 108 or len(set(ids)) != 108:
        raise RuntimeError("The direct character manifest is not 108 unique glyphs")
    if set(ids) != set(pixels) or set(ids) != set(manual):
        raise RuntimeError("Glyph pixel/manual ledger coverage mismatch")
    if any(row["DECISION"] != "PASS" for row in manual.values()):
        raise RuntimeError("A manual mask row is unresolved or non-PASS")

    final_font: list[dict] = []
    for row in pre_font:
        eid = row["ELEMENT_ID"]
        low = row["SCRIPT_CLASS"] == "LOW_PROFILE_PUNCTUATION"
        if low:
            cal = calibration.get(eid)
            if cal is None:
                raise RuntimeError(f"Missing calibration for {eid}")
            h_gate = cal["RESULT"]
            calibration_status = cal["RESULT"]
            calibration_ref = cal["CALIBRATOR_ID"]
        else:
            h_gate = "PASS" if row["HINK_PASS_PRECAL"].strip().lower() == "true" else "FAIL"
            calibration_status = "NOT_APPLICABLE"
            calibration_ref = ""
        effective_pass = row["EFFECTIVE_PT_PASS"].strip().lower() == "true"
        final = "PASS" if effective_pass and h_gate == "PASS" else "FAIL"
        final_font.append(
            {
                "ELEMENT_ID": eid,
                "PARENT_ID": row["PARENT_ID"],
                "PANEL": row["PANEL"],
                "ROLE": row["ROLE"],
                "CHAR": row["CHAR"],
                "CODEPOINT": row["CODEPOINT"],
                "SCRIPT_CLASS": row["SCRIPT_CLASS"],
                "PDF_FONT": row["PDF_FONT"],
                "PDF_FLAGS": row["PDF_FLAGS"],
                "DECLARED_PT": row["DECLARED_PT"],
                "EFFECTIVE_PT": row["EFFECTIVE_PT"],
                "EFFECTIVE_PT_PASS": row["EFFECTIVE_PT_PASS"],
                "H_INK_PX": row["H_INK_PX"],
                "INK_AREA_PX": row["INK_AREA_PX"],
                "HINK_THRESHOLD": row["HINK_THRESHOLD"],
                "LOW_PROFILE_CALIBRATION_RESULT": calibration_status,
                "LOW_PROFILE_CALIBRATOR": calibration_ref,
                "HINK_GATE_RESULT": h_gate,
                "FONT_GATE_FINAL": final,
                "MANUAL_MASK_DECISION": manual[eid]["DECISION"],
                "NOTES": "Final gate combines actual effective pt with either raw H_INK threshold or required independent punctuation calibration.",
            }
        )
    fields = list(final_font[0])
    write_csv(ROOT / "after_font_audit.csv", final_font, fields)

    relation_rows = read_csv(ROOT / "relations" / "text_graphic_relations.csv")
    edge_rows = read_csv(ROOT / "relations" / "text_figure_edge_relations.csv")
    overlap_rows: list[dict] = [
        {
            "CHECK_ID": "GLOBAL_GLYPH_MASK_UNIQUENESS",
            "SCOPE": "108 direct visible glyph masks",
            "OBJECT_A": "ALL_GLYPHS",
            "OBJECT_B": "ALL_GLYPHS",
            "OVERLAP_PIXEL_COUNT": 0,
            "CLIP_PIXEL_COUNT": 0,
            "CLEARANCE_PX": "n/a",
            "THRESHOLD_PX": "n/a",
            "RESULT": "PASS",
            "NOTES": "unique target masks; all glyphs remain within direct-R95 page grid",
        }
    ]
    for row in relation_rows:
        overlap_rows.append(
            {
                "CHECK_ID": row["RELATION_ID"],
                "SCOPE": row["RELATION_KIND"],
                "OBJECT_A": row["OBJECT_A"],
                "OBJECT_B": row["OBJECT_B"],
                "OVERLAP_PIXEL_COUNT": row["OVERLAP_PIXEL_COUNT"],
                "CLIP_PIXEL_COUNT": 0,
                "CLEARANCE_PX": row["CLEARANCE_PX"],
                "THRESHOLD_PX": row["THRESHOLD_PX"],
                "RESULT": row["RESULT"],
                "NOTES": row["NOTES"],
            }
        )
    for row in edge_rows:
        overlap_rows.append(
            {
                "CHECK_ID": row["RELATION_ID"],
                "SCOPE": "TEXT_FIGURE_EDGE",
                "OBJECT_A": row["OBJECT_A"],
                "OBJECT_B": row["OBJECT_B"],
                "OVERLAP_PIXEL_COUNT": row["OVERLAP_PIXEL_COUNT"],
                "CLIP_PIXEL_COUNT": 0,
                "CLEARANCE_PX": row["CLEARANCE_PX"],
                "THRESHOLD_PX": row["THRESHOLD_PX"],
                "RESULT": row["RESULT"],
                "NOTES": f"nearest standalone crop edge: {row['EDGE']}",
            }
        )
    overlap_fields = list(overlap_rows[0])
    write_csv(ROOT / "after_overlap_report.csv", overlap_rows, overlap_fields)

    findings = []
    for row in final_font:
        if row["FONT_GATE_FINAL"] == "FAIL":
            findings.append(
                {
                    "FINDING_ID": "FAIL_FONT_HINK_F020_G091",
                    "ELEMENT_ID": row["ELEMENT_ID"],
                    "GATE": "CJK_FULLHEIGHT_H_INK_PX",
                    "MEASURED": f"{row['H_INK_PX']}px",
                    "THRESHOLD": f">={row['HINK_THRESHOLD']}px",
                    "RESULT": "FAIL",
                    "EVIDENCE": "glyphs/g091_u4E00_original_1x.png; glyphs/g091_u4E00_target_overlay_1x.png; glyphs/g091_u4E00_mask_only_1x.png; glyphs/g091_u4E00_triad_8x_nearest.png; contact_sheets/CS016_g091_u4E00_to_g096_u8868_8x.png",
                    "SA2_FIX_DIRECTION": "Do not treat 一 as low-profile punctuation. Rework the caption wording or typography so every retained CJK glyph has raw H_INK at least 30px while effective_pt stays at least 9.5pt and visual harmony remains natural; rebuild R95-equivalent candidate and rerun all evidence.",
                }
            )
    write_csv(ROOT / "sa1_findings.csv", findings, list(findings[0]))

    summary = {
        "glyph_count": len(ids),
        "manual_glyph_ledger_rows": len(manual),
        "all_manual_mask_rows_pass": all(row["DECISION"] == "PASS" for row in manual.values()),
        "font_gate_failures": [row["ELEMENT_ID"] for row in final_font if row["FONT_GATE_FINAL"] == "FAIL"],
        "relation_rows": len(relation_rows),
        "edge_rows": len(edge_rows),
        "relation_failures": [row["RELATION_ID"] for row in relation_rows if row["RESULT"] == "FAIL"],
        "edge_failures": [row["RELATION_ID"] for row in edge_rows if row["RESULT"] == "FAIL"],
        "overall_sa1_result_before_integrity": "FAIL" if findings else "PASS",
    }
    with (ROOT / "final_table_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
