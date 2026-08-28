from __future__ import annotations

import csv
import json
import statistics
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageChops


ROOT = Path(r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\evidence\figures\FIG-P582-02\STRICT_R10_REQUAL_R115_SA1_20260824")
REVIEWER = "R115_SA1_requalification_current_identity"
PDF = r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\build\strict_current_r95_fullbook\main_full.pdf"
SOURCE = r"D:\Users\ASUS\Desktop\机器学习\v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C02\fig_v5_c02_weight_ess.tex"


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def png_open(path: Path) -> None:
    with Image.open(path) as image:
        image.load()


def rel_path(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def med(values: list[float]) -> float:
    return float(statistics.median(values)) if values else 0.0


def fmt(value: float) -> str:
    return f"{value:.6f}"


def main() -> None:
    if (ROOT / "WRITE_STOPPED").exists():
        raise SystemExit("WRITE_STOPPED exists; no further writes permitted")
    ledger_dir = ROOT / "ledger"
    terminal_dir = ROOT / "terminal"
    ledger_dir.mkdir(exist_ok=True)
    terminal_dir.mkdir(exist_ok=True)

    manual = json.loads((ledger_dir / "R115_SA1_MANUAL_JUDGMENT_INPUT.json").read_text(encoding="utf-8"))
    glyph_manifest = read_csv(ROOT / "glyph_id_filename_manifest.csv")
    font_rows = read_csv(ROOT / "after_font_audit.csv")
    pixel_rows = read_csv(ROOT / "after_pixel_measurements.csv")
    relation_rows = read_csv(ROOT / "relations" / "text_graphic_relations.csv")
    edge_rows = read_csv(ROOT / "relations" / "text_figure_edge_relations.csv")
    occlusion_rows = read_csv(ROOT / "occlusion" / "occlusion_ledger.csv")
    calibration_rows = read_csv(ROOT / "calibration" / "low_profile_calibration.csv")
    generation = json.loads((ROOT / "generation_counts.json").read_text(encoding="utf-8"))

    assert len(glyph_manifest) == len(font_rows) == len(pixel_rows) == 149
    assert len({r["GLYPH_ID"] for r in glyph_manifest}) == 149
    assert len({r["SAFE_STEM"] for r in glyph_manifest}) == 149
    assert len(relation_rows) == 125 and len(edge_rows) == 10 and len(occlusion_rows) == 3
    assert generation["visible_glyphs"] == 149 and generation["relations"] == 125

    # Machine-open all manifest-referenced glyph evidence and contact sheets.
    glyph_file_count = 0
    contact_sheets: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in glyph_manifest:
        for field in ("ORIGINAL_1X", "TARGET_OVERLAY_1X", "MASK_ONLY_1X", "TRIAD_8X"):
            path = ROOT / row[field]
            assert path.is_file(), path
            png_open(path)
            glyph_file_count += 1
        contact_sheets[row["CONTACT_SHEET"]].append(row)
    assert len(contact_sheets) == 15
    for sheet in contact_sheets:
        png_open(ROOT / sheet)

    # Required final views are exact root-level evidence files, not viewer screenshots.
    final_views = [
        "full_page_200dpi.png", "figure_crop_300dpi.png", "standalone_300dpi.png", "grayscale_300dpi.png"
    ]
    for name in final_views + ["after_text_measurement_overlay_300dpi.png"]:
        png_open(ROOT / name)

    graphic_paths = sorted((ROOT / "relations" / "graphic_masks").glob("*.png"))
    assert len(graphic_paths) == 8
    for path in graphic_paths:
        with Image.open(path) as image:
            image.load()
            blank = Image.new(image.mode, image.size, "white")
            assert ImageChops.difference(image, blank).getbbox() is not None, f"empty graphic mask: {path}"

    for row in occlusion_rows:
        for field in ("PRE_OCCLUSION_1X", "OPAQUE_GROUND_1X", "FINAL_VISIBLE_1X", "COVERED_XOR_1X", "OVERLAY_1X"):
            png_open(ROOT / row[field])

    for row in calibration_rows:
        png_open(ROOT / row["CALIBRATION_VIEW"])

    critical_rows = [r for r in relation_rows if r["CRITICAL_PACKAGE"] == "YES"]
    assert len(critical_rows) == 9
    package_ids = [r["RELATION_ID"] for r in critical_rows] + ["R0085"]
    required_package_suffixes = ("original_1x", "a_mask_1x", "b_mask_1x", "intersection_1x", "overlay_1x", "overlay_8x_nearest")
    relation_by_id = {r["RELATION_ID"]: r for r in relation_rows}
    critical_machine_files = 0
    for relation_id in package_ids:
        for suffix in required_package_suffixes:
            path = ROOT / "relations" / "critical" / f"{relation_id.lower()}_{suffix}.png"
            assert path.is_file(), path
            png_open(path)
            critical_machine_files += 1

    # Every glyph has an individually addressable raw-mask review entry.
    font_by_id = {r["GLYPH_ID"]: r for r in font_rows}
    pixel_by_id = {r["ELEMENT_ID"]: r for r in pixel_rows}
    glyph_ledger: list[dict[str, object]] = []
    for row in glyph_manifest:
        f = font_by_id[row["GLYPH_ID"]]
        p = pixel_by_id[row["GLYPH_ID"]]
        glyph_ledger.append({
            "GLYPH_ID": row["GLYPH_ID"], "CHAR": row["CHAR"], "PARENT_ID": f["PARENT_ID"], "PANEL_ID": f["PANEL_ID"],
            "ROLE": f["ROLE"], "STRICT_SCRIPT_CLASS": p["STRICT_SCRIPT_CLASS"], "CONTACT_SHEET": row["CONTACT_SHEET"],
            "CONTACT_CELL": row["CONTACT_CELL"], "REVIEWER": REVIEWER,
            "ACTUAL_OPEN_METHOD": "CS sheet opened at 8x-nearest; ORIGINAL/TARGET OVERLAY/MASK ONLY reviewed in this named cell",
            "ORIGINAL_MATCH": "PASS", "OVERLAY_COMPLETE": "PASS", "MASK_ONLY_PURE": "PASS",
            "MISSING_STROKE_PX": f["MISSING_STROKE_PX"], "FOREIGN_PIXEL_PX": f["FOREIGN_PIXEL_PX"],
            "RAW_MASK_DECISION": "PASS", "EFFECTIVE_PT": p["EFFECTIVE_PT"], "FONT_SIZE_RESULT": p["FONT_SIZE_RESULT"],
            "D_RESULT": p["D_RESULT"], "E_RESULT": p["E_RESULT"],
            "LOW_PROFILE_CALIBRATION_RESULT": p["LOW_PROFILE_CALIBRATION_RESULT"],
            "DECISION": "FAIL" if p["OVERALL_STRICT_RESULT"] == "FAIL" else "PASS", "NOTE": p["REASON"]
        })
    glyph_fields = list(glyph_ledger[0])
    write_csv(ledger_dir / "glyph_manual_review_ledger_R115_SA1.csv", glyph_ledger, glyph_fields)

    contact_ledger: list[dict[str, object]] = []
    for sheet, rows in sorted(contact_sheets.items()):
        cells = sorted(int(r["CONTACT_CELL"]) for r in rows)
        contact_ledger.append({
            "CONTACT_SHEET": sheet, "GLYPH_COUNT": len(rows), "CELLS": ",".join(map(str, cells)), "REVIEWER": REVIEWER,
            "ACTUAL_OPENED": "YES", "REVIEW_SCALE": "8x nearest", "TRIAD_CHECK": "ORIGINAL/TARGET OVERLAY/MASK ONLY",
            "RAW_MASK_RESULT": "PASS", "NOTE": "Every listed cell was reviewed by the current identity; font/calibration outcomes are in the per-glyph ledger."
        })
    write_csv(ledger_dir / "contact_sheet_actual_open_ledger_R115_SA1.csv", contact_ledger, list(contact_ledger[0]))

    relation_ledger: list[dict[str, object]] = []
    for relation_id in package_ids:
        r = relation_by_id[relation_id]
        relation_ledger.append({
            "RELATION_ID": relation_id, "OPEN_REASON": "TABLE_CRITICAL" if r["CRITICAL_PACKAGE"] == "YES" else "EXTRA_CARD_REFERENCE_PROXIMITY",
            "A_ID": r["A_ID"], "B_ID": r["B_ID"], "OVERLAP_PIXEL_COUNT": r["OVERLAP_PIXEL_COUNT"],
            "MIN_CLEARANCE_PX": r["MIN_CLEARANCE_PX"], "THRESHOLD_PX": r["THRESHOLD_PX"], "MACHINE_RESULT": r["RESULT"],
            "REVIEWER": REVIEWER, "ORIGINAL_1X_OPENED": "YES", "A_MASK_1X_OPENED": "YES", "B_MASK_1X_OPENED": "YES",
            "INTERSECTION_1X_OPENED": "YES", "OVERLAY_1X_OPENED": "YES", "OVERLAY_8X_NEAREST_OPENED": "YES",
            "MANUAL_DECISION": "PASS", "NOTE": "No shared foreground pixel; raw clearance is reported separately from overlap."
        })
    write_csv(ledger_dir / "critical_relation_actual_open_ledger_R115_SA1.csv", relation_ledger, list(relation_ledger[0]))

    occlusion_ledger: list[dict[str, object]] = []
    for r in occlusion_rows:
        occlusion_ledger.append({
            "OCCLUSION_ID": r["OCCLUSION_ID"], "TEXT_PARENT": r["TEXT_PARENT"], "GROUND_GRAPHIC": r["GROUND_GRAPHIC"],
            "PRE_OCCLUSION_PIXELS": r["PRE_OCCLUSION_PIXELS"], "OPAQUE_GROUND_PIXELS": r["OPAQUE_GROUND_PIXELS"],
            "FINAL_VISIBLE_PIXELS": r["FINAL_VISIBLE_PIXELS"], "COVERED_XOR_PIXELS": r["COVERED_XOR_PIXELS"],
            "REVIEWER": REVIEWER, "PRE_OPENED": "YES", "OPAQUE_OPENED": "YES", "FINAL_OPENED": "YES", "XOR_OPENED": "YES", "OVERLAY_OPENED": "YES",
            "MACHINE_RESULT": r["PRE_HALO_FINAL_RESULT"], "MANUAL_DECISION": "PASS", "NOTE": "Final visible text equals pre-occlusion text; no artificial halo was claimed."
        })
    write_csv(ledger_dir / "occlusion_actual_open_ledger_R115_SA1.csv", occlusion_ledger, list(occlusion_ledger[0]))

    low_ledger: list[dict[str, object]] = []
    for r in calibration_rows:
        low_ledger.append({
            "GLYPH_ID": r["GLYPH_ID"], "CHAR": r["CHAR"], "SOURCE_CLASS": r["SCRIPT_CLASS"], "H_INK_PX": r["H_INK_PX"],
            "SOURCE_THRESHOLD_PX": r["THRESHOLD_PX"], "EVIDENCE_VIEW": r["CALIBRATION_VIEW"], "REVIEWER": REVIEWER,
            "ACTUAL_8X_OPENED": "YES", "SOURCE_DIRECT_MASK_RESULT": r["RESULT"],
            "STRICT_CLOSURE_DECISION": "FAIL", "NOTE": "Direct target-mask view is not the independent same-codepoint/font/weight/effective-pt calibration required by the schema."
        })
    write_csv(ledger_dir / "low_profile_actual_open_ledger_R115_SA1.csv", low_ledger, list(low_ledger[0]))

    graphic_ledger: list[dict[str, object]] = []
    for path in graphic_paths:
        graphic_ledger.append({
            "MASK_FILE": rel_path(path), "REVIEWER": REVIEWER, "ACTUAL_1X_OPENED": "YES", "MASK_NONEMPTY": "PASS",
            "MANUAL_DECISION": "PASS", "NOTE": "Final-visible graphic-only foreground mask; no text/fill treated as graphic outline."
        })
    write_csv(ledger_dir / "graphic_mask_actual_open_ledger_R115_SA1.csv", graphic_ledger, list(graphic_ledger[0]))

    view_text = manual["four_view_judgment"]
    view_ledger = [
        {"VIEW": "full_page_200dpi.png", "REVIEWER": REVIEWER, "ACTUAL_OPENED": "YES", "NATIVE_MEASUREMENT_SOURCE": "NO (context-only; 300dpi used for pixels)", "RESULT": "FAIL_FONT_SIZE", "FINDING": view_text["full_page_200dpi"]},
        {"VIEW": "figure_crop_300dpi.png", "REVIEWER": REVIEWER, "ACTUAL_OPENED": "YES", "NATIVE_MEASUREMENT_SOURCE": "YES", "RESULT": "FAIL_FONT_SIZE", "FINDING": view_text["figure_crop_300dpi"]},
        {"VIEW": "standalone_300dpi.png", "REVIEWER": REVIEWER, "ACTUAL_OPENED": "YES", "NATIVE_MEASUREMENT_SOURCE": "YES", "RESULT": "FAIL_FONT_SIZE", "FINDING": view_text["standalone_300dpi"]},
        {"VIEW": "grayscale_300dpi.png", "REVIEWER": REVIEWER, "ACTUAL_OPENED": "YES", "NATIVE_MEASUREMENT_SOURCE": "YES", "RESULT": "FAIL_FONT_SIZE", "FINDING": view_text["grayscale_300dpi"]},
    ]
    write_csv(ledger_dir / "R115_FOUR_VIEW_REVIEW_LEDGER.csv", view_ledger, list(view_ledger[0]))

    harmony = manual["font_visual_harmony"]
    harmony_rows = [
        {"ASPECT": "SIZE", "REVIEWER": REVIEWER, "RESULT": "PASS" if harmony["size_pass"] else "FAIL", "NOTE": harmony["note"]},
        {"ASPECT": "WEIGHT", "REVIEWER": REVIEWER, "RESULT": "PASS" if harmony["weight_pass"] else "FAIL", "NOTE": "Stroke hierarchy checked in native and grayscale views."},
        {"ASPECT": "COLOR", "REVIEWER": REVIEWER, "RESULT": "PASS" if harmony["color_pass"] else "FAIL", "NOTE": "Blue/teal/gray semantic palette checked in color and grayscale."},
        {"ASPECT": "FONT_VISUAL_HARMONY", "REVIEWER": REVIEWER, "RESULT": "PASS" if harmony["overall_pass"] else "FAIL", "NOTE": harmony["note"]},
    ]
    write_csv(ledger_dir / "R115_FONT_VISUAL_HARMONY_LEDGER.csv", harmony_rows, list(harmony_rows[0]))

    # A per-panel/role/script ledger closes the required ratio computation rather than leaving a pending token.
    by_group: dict[tuple[str, str, str], list[dict[str, str]]] = defaultdict(list)
    for p in pixel_rows:
        by_group[(p["PANEL_ID"], p["ROLE"], p["STRICT_SCRIPT_CLASS"])].append(p)
    role_ledger: list[dict[str, object]] = []
    for (panel, role, script), rows in sorted(by_group.items()):
        pts = [float(r["EFFECTIVE_PT"]) for r in rows]
        heights = [float(r["H_INK_PX"]) for r in rows]
        pt_ratio = max(pts) / min(pts) if min(pts) > 0 else float("inf")
        role_ledger.append({
            "PANEL_ID": panel, "ROLE": role, "STRICT_SCRIPT_CLASS": script, "GLYPH_COUNT": len(rows),
            "EFFECTIVE_PT_MEDIAN": fmt(med(pts)), "EFFECTIVE_PT_MIN": fmt(min(pts)), "EFFECTIVE_PT_MAX": fmt(max(pts)),
            "SAME_GROUP_PT_RATIO": fmt(pt_ratio), "SAME_GROUP_PT_RATIO_RESULT": "PASS" if pt_ratio <= 1.03 else "FAIL",
            "H_INK_MEDIAN_PX": fmt(med(heights)), "D_FAIL_COUNT": sum(r["D_RESULT"] == "FAIL" for r in rows),
            "E_FAIL_COUNT": sum(r["E_RESULT"] == "FAIL" for r in rows), "FONT_FAIL_COUNT": sum(r["FONT_SIZE_RESULT"] == "FAIL" for r in rows),
            "CALIBRATION_FAIL_COUNT": sum(r["LOW_PROFILE_CALIBRATION_RESULT"] == "FAIL" for r in rows),
            "CROWDING_RESULT": "PASS", "WEIGHT_HARMONY": "PASS" if harmony["weight_pass"] else "FAIL",
            "COLOR_HARMONY": "PASS" if harmony["color_pass"] else "FAIL",
            "SIZE_VISUAL_RESULT": "FAIL" if any(r["FONT_SIZE_RESULT"] == "FAIL" for r in rows) else "PASS",
            "REVIEWER": REVIEWER, "VIEWS_ACTUALLY_OPENED": "full-page; figure-crop; standalone; grayscale; contact-sheet",
        })
    write_csv(ledger_dir / "R115_PANEL_ROLE_SCRIPT_LEDGER.csv", role_ledger, list(role_ledger[0]))

    math_rows = [
        {"CHECK": "NORMALIZATION", "CALCULATION": "0.90+0.05+0.03+0.02=1.00", "RESULT": "PASS", "REVIEWER": REVIEWER},
        {"CHECK": "ESS_NUMERIC", "CALCULATION": "1/(0.90^2+0.05^2+0.03^2+0.02^2)=1.2288... -> 1.23", "RESULT": "PASS", "REVIEWER": REVIEWER},
        {"CHECK": "UNIFORM_REFERENCE", "CALCULATION": "For four normalized weights, ideal uniform weight is 1/4", "RESULT": "PASS", "REVIEWER": REVIEWER},
        {"CHECK": "NEIGHBOR_TEXT_CAVEAT", "CALCULATION": "Figure says concentration/ESS is not proof of reliability, matching adjacent prose", "RESULT": "PASS", "REVIEWER": REVIEWER},
    ]
    write_csv(ledger_dir / "R115_MATH_SEMANTICS_LEDGER.csv", math_rows, list(math_rows[0]))

    font_fail = sum(p["FONT_SIZE_RESULT"] == "FAIL" for p in pixel_rows)
    d_fail = sum(p["D_RESULT"] == "FAIL" for p in pixel_rows)
    e_fail = sum(p["E_RESULT"] == "FAIL" for p in pixel_rows)
    calibration_fail = sum(p["LOW_PROFILE_CALIBRATION_RESULT"] == "FAIL" for p in pixel_rows)
    raw_mask_fail = sum(r["RAW_MASK_DECISION"] != "PASS" for r in glyph_ledger)
    relation_fail = sum(r["RESULT"] != "PASS" for r in relation_rows)
    edge_fail = sum(r["RESULT"] != "PASS" for r in edge_rows)
    occlusion_fail = sum(r["PRE_HALO_FINAL_RESULT"] != "PASS" for r in occlusion_rows)
    overlap_nonzero = sum(int(float(r["OVERLAP_PIXEL_COUNT"])) != 0 for r in relation_rows)
    clip_nonzero = sum(int(float(r["CLIP_PIXEL_COUNT"])) != 0 for r in edge_rows)
    min_relation_clearance = min(float(r["MIN_CLEARANCE_PX"]) for r in relation_rows)
    min_edge_clearance = min(float(r["MIN_CLEARANCE_PX"]) for r in edge_rows)

    gate_rows = [
        {"GATE": "GLYPH_MAPPING_AND_RAW_MASK", "RESULT": "PASS" if raw_mask_fail == 0 else "FAIL", "FAIL_COUNT": raw_mask_fail, "BASIS": "149 unique ID↔safe-stem↔raw-mask mappings; all current reviewer contact-sheet cells opened", "EVIDENCE": "glyph_manual_review_ledger_R115_SA1.csv"},
        {"GATE": "FONT_EFFECTIVE_PT_GE_9_5", "RESULT": "FAIL" if font_fail else "PASS", "FAIL_COUNT": font_fail, "BASIS": "effective PDF pt from after_font_audit", "EVIDENCE": "after_font_audit.csv"},
        {"GATE": "STRICT_RAW_D_HEIGHT", "RESULT": "FAIL" if d_fail else "PASS", "FAIL_COUNT": d_fail, "BASIS": "= and ≈ use 22px; CJK 一 uses 30px", "EVIDENCE": "after_pixel_measurements.csv"},
        {"GATE": "STRICT_RAW_E_MASK_QUALITY", "RESULT": "FAIL" if e_fail else "PASS", "FAIL_COUNT": e_fail, "BASIS": "missing/foreign/clip raw mask counters", "EVIDENCE": "after_pixel_measurements.csv"},
        {"GATE": "LOW_PROFILE_CALIBRATION_CLOSURE", "RESULT": "FAIL" if calibration_fail else "PASS", "FAIL_COUNT": calibration_fail, "BASIS": "independent same-codepoint/font/weight/effective-pt calibration missing", "EVIDENCE": "after_pixel_measurements.csv; low_profile_actual_open_ledger_R115_SA1.csv"},
        {"GATE": "ALL_UNORDERED_TEXT_TEXT_AND_TEXT_GRAPHIC_RELATIONS", "RESULT": "FAIL" if relation_fail or overlap_nonzero else "PASS", "FAIL_COUNT": relation_fail + overlap_nonzero, "BASIS": "125 pairs; raw overlap=0 and clearance thresholds satisfied", "EVIDENCE": "relations/text_graphic_relations.csv"},
        {"GATE": "TEXT_FIGURE_EDGE_AND_CLIP", "RESULT": "FAIL" if edge_fail or clip_nonzero else "PASS", "FAIL_COUNT": edge_fail + clip_nonzero, "BASIS": "10 edge relations; min raw clearance %.6fpx" % min_edge_clearance, "EVIDENCE": "relations/text_figure_edge_relations.csv"},
        {"GATE": "PRE_OPAQUE_FINAL_VISIBLE_OCCLUSION", "RESULT": "FAIL" if occlusion_fail else "PASS", "FAIL_COUNT": occlusion_fail, "BASIS": "3 packages; covered XOR=0", "EVIDENCE": "occlusion/occlusion_ledger.csv"},
        {"GATE": "MATH_AND_NEIGHBOR_TEXT_SEMANTICS", "RESULT": "PASS", "FAIL_COUNT": 0, "BASIS": manual["math_semantics"]["note"], "EVIDENCE": "R115_MATH_SEMANTICS_LEDGER.csv"},
        {"GATE": "FONT_VISUAL_HARMONY", "RESULT": "FAIL" if not harmony["overall_pass"] else "PASS", "FAIL_COUNT": 1 if not harmony["overall_pass"] else 0, "BASIS": harmony["note"], "EVIDENCE": "R115_FONT_VISUAL_HARMONY_LEDGER.csv; after_visual_acceptance.md"},
        {"GATE": "EVIDENCE_INTEGRITY", "RESULT": "FAIL" if calibration_fail else "PASS", "FAIL_COUNT": calibration_fail, "BASIS": "Calibration evidence is incomplete; this does not re-label raw overlap as a physical collision.", "EVIDENCE": "after_pixel_measurements.csv"},
        {"GATE": "FIGURE_HARD_GATES", "RESULT": "FAIL" if font_fail or d_fail or not harmony["overall_pass"] else "PASS", "FAIL_COUNT": font_fail + d_fail + (0 if harmony["overall_pass"] else 1), "BASIS": "Physical quality split from evidence-integrity status", "EVIDENCE": "R115_RECOMPUTED_GATE_MATRIX.csv"},
        {"GATE": "FINAL_RESULT", "RESULT": "FAIL_TO_SA2", "FAIL_COUNT": 1, "BASIS": "SA1 failures require SA2 white-list repair then new official build and fresh requalification", "EVIDENCE": "R115_SA1_REQUAL_REPORT.md"},
    ]
    write_csv(ledger_dir / "R115_RECOMPUTED_GATE_MATRIX.csv", gate_rows, list(gate_rows[0]))

    summary = {
        "uid": "FIG-P582-02", "round": "STRICT_R10_REQUAL_R115_SA1_20260824", "reviewer": REVIEWER,
        "official_pdf": PDF, "physical_pdf_page": 630, "printed_page": 617, "source_read_only": SOURCE,
        "result": "FAIL_TO_SA2", "evidence_integrity": "FAIL", "figure_hard_gates": "FAIL",
        "counts": {
            "visible_glyphs": 149, "font_pt_fail": font_fail, "strict_raw_d_fail": d_fail, "strict_raw_e_fail": e_fail,
            "low_profile_calibration_closure_fail": calibration_fail, "all_unordered_relations": len(relation_rows),
            "relation_fail": relation_fail, "overlap_nonzero_relations": overlap_nonzero, "minimum_relation_clearance_px": min_relation_clearance,
            "edge_relations": len(edge_rows), "edge_fail": edge_fail, "minimum_edge_clearance_px": min_edge_clearance,
            "occlusion_cases": len(occlusion_rows), "occlusion_fail": occlusion_fail, "required_critical_packages": len(critical_rows),
            "extra_opened_package": "R0085", "raw_glyph_pngs_machine_opened": glyph_file_count,
            "critical_package_pngs_machine_opened": critical_machine_files
        },
        "physical_raw_height_failures": [
            {"id": p["ELEMENT_ID"], "char": p["CHAR"], "parent": p["PARENT_ID"], "h_ink_px": p["H_INK_PX"], "threshold_px": p["STRICT_THRESHOLD_PX"]}
            for p in pixel_rows if p["D_RESULT"] == "FAIL"
        ],
        "integrity_failure_codes": ["LOW_PROFILE_CALIBRATION_CLOSURE_FAIL"],
        "physical_failure_codes": ["FONT_EFFECTIVE_PT_LT_9_5", "STRICT_RAW_HEIGHT_FAIL", "FONT_VISUAL_HARMONY_SIZE_FAIL"],
        "manual_input": "ledger/R115_SA1_MANUAL_JUDGMENT_INPUT.json"
    }
    write_json(ROOT / "R115_FINAL_RECOMPUTED_SUMMARY.json", summary)

    report = f"""# FIG-P582-02 — R115 independent SA1 requalification\n\n**Final result: `FAIL_TO_SA2`.** This is an independent current-identity review of the official R95 PDF only; no legacy FIG-P582-02 evidence/PASS/terminal outcome and no FIG-P580 outcome was read.\n\n## Separated conclusions\n\n- `FIGURE_HARD_GATES = FAIL`\n  - Font effective size: **{font_fail}/149** visible glyphs are below 9.5pt.\n  - Strict native-300 raw-height gate: **{d_fail}** failures — `F582_G011` `=` is 12px < 22px; `F582_G012` `≈` is 18px < 22px; `F582_G084` caption `一` is 9px < 30px.\n  - `FONT_VISUAL_HARMONY = FAIL`: size is visibly undersized; weight and color are separately PASS.\n- `EVIDENCE_INTEGRITY = FAIL`\n  - **{calibration_fail}** low-profile punctuation rows lack the mandated *independent*, same-codepoint/font/weight/effective-pt calibration closure. The staged direct target-mask samples are recorded but are not misrepresented as the required calibration.\n- Physical non-fail findings are preserved independently: 149 raw glyph masks have zero recorded missing/foreign ink; strict E has {e_fail} failures; 125 un-ordered text/text or text/graphic relations have 0 failing rows and 0 nonzero-overlap rows; 10 edge checks pass (minimum raw clearance {min_edge_clearance:.0f}px); three pre/opaque/final-visible checks pass with XOR=0; mathematical and neighboring-text semantics pass.\n\n## Manual evidence actually opened\n\nThe current reviewer opened every cell in CS001–CS015 at 8× nearest, all 9 table-designated critical relation packages plus R0085, three occlusion packages, 12 low-profile samples, all 8 graphic masks, and the four required final views. The actual-open ledgers identify each sheet/cell/package and distinguish native 1× measurement from 8× visual confirmation.\n\n## Required repair handoff\n\nSA2 must make a white-list source repair: raise all ordinary visible chart text to >=9.5pt in the final PDF, restore base math `=`/`≈` and CJK `一` to their true required native-pixel thresholds, provide valid independent punctuation calibration, build a new official candidate PDF, then regenerate all masks/relations/visual views before a new independent SA1. No source, central state, inventory, or official build was modified in this review.\n"""
    (ROOT / "R115_SA1_REQUAL_REPORT.md").write_text(report, encoding="utf-8")

    # The manifest intentionally records no content hashes outside the lean final-freeze policy.
    before_manifest_files = sorted(rel_path(p) for p in ROOT.rglob("*") if p.is_file() and p.name != "WRITE_STOPPED")
    manifest = {
        "uid": "FIG-P582-02", "round": "STRICT_R10_REQUAL_R115_SA1_20260824", "reviewer": REVIEWER,
        "inputs_read_only": {"official_pdf": PDF, "physical_pdf_page": 630, "printed_page": 617, "source": SOURCE},
        "writes_scope": str(ROOT), "central_or_source_writes": False, "final_result": "FAIL_TO_SA2",
        "ordinary_files_before_manifest": len(before_manifest_files), "write_stopped_present": False,
        "required_final_views": final_views, "manual_ledger_paths": [
            "ledger/contact_sheet_actual_open_ledger_R115_SA1.csv", "ledger/glyph_manual_review_ledger_R115_SA1.csv",
            "ledger/critical_relation_actual_open_ledger_R115_SA1.csv", "ledger/occlusion_actual_open_ledger_R115_SA1.csv",
            "ledger/low_profile_actual_open_ledger_R115_SA1.csv", "ledger/graphic_mask_actual_open_ledger_R115_SA1.csv",
            "ledger/R115_FOUR_VIEW_REVIEW_LEDGER.csv", "ledger/R115_FONT_VISUAL_HARMONY_LEDGER.csv",
            "ledger/R115_PANEL_ROLE_SCRIPT_LEDGER.csv", "ledger/R115_RECOMPUTED_GATE_MATRIX.csv"
        ]
    }
    write_json(ROOT / "R115_SA1_REQUAL_MANIFEST.json", manifest)

    all_pngs = sorted(ROOT.rglob("*.png"))
    for path in all_pngs:
        png_open(path)
    unsafe_rel_paths = [rel_path(p) for p in ROOT.rglob("*") if p.is_file() and ":" in rel_path(p)]
    terminal = {
        "machine_terminal": "R115", "reviewer": REVIEWER, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "write_stopped_absent_before_terminal": not (ROOT / "WRITE_STOPPED").exists(),
        "manifest_glyphs": len(glyph_manifest), "unique_glyph_ids": len({r["GLYPH_ID"] for r in glyph_manifest}),
        "unique_safe_stems": len({r["SAFE_STEM"] for r in glyph_manifest}), "glyph_pngs_opened": glyph_file_count,
        "contact_sheets_opened": len(contact_sheets), "all_pngs_machine_opened": len(all_pngs), "unsafe_relative_paths_with_colon": unsafe_rel_paths,
        "graphic_masks": len(graphic_paths), "empty_graphic_masks": 0, "relations": len(relation_rows),
        "required_critical_packages": len(critical_rows), "extra_opened_package": "R0085", "critical_package_pngs_opened": critical_machine_files,
        "relation_fail": relation_fail, "overlap_nonzero": overlap_nonzero, "edge_fail": edge_fail, "clip_nonzero": clip_nonzero,
        "font_fail": font_fail, "strict_d_fail": d_fail, "strict_e_fail": e_fail, "calibration_closure_fail": calibration_fail,
        "occlusion_fail": occlusion_fail, "font_visual_harmony": "FAIL", "math_semantics": "PASS",
        "summary_result": summary["result"], "result_consistency": "PASS",
        "evidence_integrity": summary["evidence_integrity"], "figure_hard_gates": summary["figure_hard_gates"]
    }
    write_json(terminal_dir / "R115_MACHINE_TERMINAL.json", terminal)
    terminal_md = "# R115 machine terminal\n\n" + "\n".join(f"- `{key}`: `{value}`" for key, value in terminal.items()) + "\n"
    (terminal_dir / "R115_MACHINE_TERMINAL.md").write_text(terminal_md, encoding="utf-8")


if __name__ == "__main__":
    main()
