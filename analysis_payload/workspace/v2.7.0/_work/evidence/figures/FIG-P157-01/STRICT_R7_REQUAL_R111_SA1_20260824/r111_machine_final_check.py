"""Machine terminal consistency check for the R111 SA1 evidence package.

It distinguishes a valid, reproducible evidence package from the figure's hard
quality result.  The expected quality result is FAIL; the expected evidence
integrity result is PASS.
"""
from __future__ import annotations

import csv
import itertools
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
FAILURES: list[str] = []
CHECKS: dict[str, object] = {}


def read_csv(name: str) -> list[dict[str, str]]:
    path = ROOT / name
    if not path.is_file():
        FAILURES.append(f"missing CSV: {name}")
        return []
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def require(condition: bool, message: str) -> None:
    if not condition:
        FAILURES.append(message)


def as_true(value: str) -> bool:
    return value.strip().lower() == "true"


def image_openable(relative: str) -> bool:
    path = ROOT / relative
    if not path.is_file():
        FAILURES.append(f"missing image: {relative}")
        return False
    try:
        with Image.open(path) as image:
            image.load()
            require(image.width > 0 and image.height > 0, f"zero-sized image: {relative}")
        return True
    except Exception as exc:  # report the precise file, not an opaque aggregate
        FAILURES.append(f"unopenable image {relative}: {exc}")
        return False


def no_blank_rows(rows: list[dict[str, str]], label: str) -> None:
    for index, row in enumerate(rows, start=2):
        for field, value in row.items():
            require(bool(str(value).strip()), f"blank {label} row {index} field {field}")


def main() -> None:
    manifest = json.loads((ROOT / "render_manifest.json").read_text(encoding="utf-8"))
    require(manifest.get("native_300dpi_size_px") == [2481, 3508], "render manifest native grid is not 2481x3508")
    require(manifest.get("text_element_count") == 11, "render manifest text element count is not 11")
    require(manifest.get("glyph_count") == 80, "render manifest glyph count is not 80")
    CHECKS["candidate_render_identity"] = True

    inventory = read_csv("object_inventory.csv")
    foreground = [row for row in inventory if as_true(row["FOREGROUND_FOR_RELATIONS"])]
    object_ids = {row["OBJECT_ID"] for row in foreground}
    require(len(foreground) == 20 and len(object_ids) == 20, "foreground semantic object count is not 20 unique IDs")
    for row in foreground:
        image_openable(row["FINAL_VISIBLE_MASK"])
    CHECKS["foreground_objects_and_masks"] = {"count": len(object_ids), "all_opened": True}

    semantic = read_csv("R111_SEMANTIC_SOURCE_MAP.csv")
    require(len(semantic) == 11 and {r["ELEMENT_ID"] for r in semantic} == {f"E{i:03d}" for i in range(1, 12)}, "semantic source-map coverage mismatch")
    require(all(r["CORRECTION_STATUS"] == "R111_CANONICAL" for r in semantic), "semantic source-map has noncanonical row")
    CHECKS["semantic_source_map"] = {"count": len(semantic), "canonical": True}

    glyphs = read_csv("glyph_file_manifest.csv")
    glyph_ids = {row["GLYPH_ID"] for row in glyphs}
    require(len(glyphs) == 80 and len(glyph_ids) == 80, "glyph manifest is not 80 unique rows")
    for row in glyphs:
        image_openable(row["ORIGINAL_FILE"])
        image_openable(row["TARGET_OVERLAY_FILE"])
        image_openable(row["MASK_FILE"])
    contacts = sorted((ROOT / "glyph_contacts").glob("contact_sheet_*.png"))
    require(len(contacts) == 10, "glyph contact-sheet count is not 10")
    for path in contacts:
        image_openable(str(path.relative_to(ROOT)).replace("\\", "/"))
    machine_glyph = read_csv("glyph_machine_integrity.csv")
    require(len(machine_glyph) == 80 and {r["GLYPH_ID"] for r in machine_glyph} == glyph_ids, "glyph machine integrity coverage mismatch")
    require(all(as_true(r["MASK_PURITY_COMPLETENESS_PASS"]) and int(r["FOREIGN_PIXEL_PX"]) == 0 and int(r["MISSING_STROKE_PX"]) == 0 and r["EMPTY_MASK"].lower() == "false" for r in machine_glyph), "glyph mask purity/completeness failure")
    manual_glyph = read_csv("R111_GLYPH_MANUAL_LEDGER.csv")
    require(len(manual_glyph) == 80 and {r["GLYPH_ID"] for r in manual_glyph} == glyph_ids, "manual glyph ledger coverage mismatch")
    manual_open_fields = ["ORIGINAL_1X_OPENED", "TARGET_OVERLAY_1X_OPENED", "MASK_ONLY_1X_OPENED", "CONTACT_8X_OPENED", "ORIGINAL_MATCH", "OVERLAY_COMPLETE", "MASK_ONLY_PURE", "MACHINE_MASK_CROSSCHECK"]
    require(all(all(as_true(r[field]) for field in manual_open_fields) and r["OUTLINE_MANUAL_DECISION"] == "PASS" and int(r["MISSING_STROKE_PX"]) == 0 and int(r["FOREIGN_PIXEL_PX"]) == 0 for r in manual_glyph), "manual glyph ledger has unopened/nonpass/contaminated row")
    CHECKS["glyph_1x_8x_manual_and_machine"] = {"count": 80, "contacts": 10, "pass": True}

    calibration_validation = read_csv("R111_LOW_PROFILE_CALIBRATION_VALIDATION.csv")
    low_raw = read_csv("low_profile_calibration/low_profile_calibration.csv")
    require(len(calibration_validation) == 5 == len(low_raw), "low-profile calibration count is not five")
    require(all(as_true(r["FONT_WEIGHT_COLOR_SIZE_300DPI_PURITY_VALID"]) for r in calibration_validation), "low-profile calibration method invalid")
    require(all(r["LOW_PROFILE_TOTAL_GATE_PASS"].lower() == "false" for r in low_raw), "low-profile raw calibration did not retain five measured failures")
    pixel = read_csv("R111_PIXEL_FINAL_ADJUDICATION.csv")
    require(len(pixel) == 80 and {r["GLYPH_ID"] for r in pixel} == glyph_ids, "pixel final adjudication coverage mismatch")
    require(not any("PENDING" in "|".join(r.values()).upper() for r in pixel), "PENDING value in final pixel adjudication")
    pixel_fail = {r["GLYPH_ID"] for r in pixel if r["R111_FINAL_PIXEL_DECISION"] == "FAIL"}
    require(pixel_fail == {"G0005", "G0014", "G0050", "G0068", "G0080"}, f"unexpected pixel fail IDs: {sorted(pixel_fail)}")
    CHECKS["pixel_and_low_profile"] = {"rows": len(pixel), "pass": len(pixel) - len(pixel_fail), "fail": len(pixel_fail), "calibration_method_valid": True}

    de = read_csv("R111_D_E_FINAL_ADJUDICATION.csv")
    no_blank_rows(de, "D/E")
    require(len(de) == 80 and {r["GLYPH_ID"] for r in de} == glyph_ids, "D/E coverage mismatch")
    require(all(r["D_STATUS"].startswith("PASS") for r in de), "same-class D audit failure")
    e_fail = [r for r in de if r["E_STATUS"] == "FAIL"]
    require(len(e_fail) == 8 and all(r["ROLE"] == "REGION_LABEL" and r["SCRIPT_CLASS"] == "CJK_FULL" and r["E_ROLE_RATIO"] == "0.9459" for r in e_fail), "unexpected E role-ratio failure set")
    de_summary = json.loads((ROOT / "R111_D_E_FINAL_SUMMARY.json").read_text(encoding="utf-8"))
    require(de_summary.get("same_class_ratio_pass") is True and de_summary.get("role_ratio_pass") is False and de_summary.get("role_ratio_fail_glyphs") == 8, "D/E summary inconsistent")
    CHECKS["D_E"] = {"same_class_pass": True, "role_pass": False, "role_fail_glyphs": 8}

    views = read_csv("R111_REQUIRED_VIEW_REVIEW_LEDGER.csv")
    no_blank_rows(views, "view ledger")
    require(len(views) == 4 and all(as_true(r["ACTUALLY_OPENED"]) and r["VIEW_DECISION"] == "PASS" for r in views), "required view ledger not fully opened/pass")
    for row in views:
        image_openable(row["FILE"])
    font_visual = read_csv("R111_FONT_VISUAL_HARMONY_LEDGER.csv")
    no_blank_rows(font_visual, "font visual ledger")
    require(len(font_visual) == 10 and all(r["FONT_VISUAL_HARMONY_PASS"].lower() == "true" for r in font_visual), "font visual harmony ledger failure")
    require(sum(r["ROW_HARD_GATE_DECISION"] == "FAIL" for r in font_visual) == 5, "unexpected font visual hard-gate group failures")
    CHECKS["human_visual_review"] = {"views": 4, "panel_role_script_rows": 10, "visual_harmony": True}

    pairs = read_csv("R111_ALL_UNORDERED_PAIR_FINAL_ADJUDICATION.csv")
    expected_pairs = {tuple(sorted(pair)) for pair in itertools.combinations(object_ids, 2)}
    actual_pairs = {tuple(sorted((r["OBJECT_A"], r["OBJECT_B"]))) for r in pairs}
    require(len(pairs) == 190 and len(actual_pairs) == 190 and actual_pairs == expected_pairs, "unordered-pair universe mismatch")
    require(not any("PENDING" in "|".join(r.values()).upper() for r in pairs), "PENDING value in final pair adjudication")
    pair_fail = [r for r in pairs if r["PASS_FAIL"] == "FAIL"]
    require(len(pair_fail) == 1 and pair_fail[0]["PAIR_ID"] == "P0155", "pair final fail set is not exactly P0155")
    p155 = pair_fail[0]
    require(int(p155["OVERLAP_PIXEL_COUNT"]) == 139 and float(p155["MIN_CLEARANCE_PX"]) == 0.0 and p155["R111_FINAL_STATUS"] == "FAIL", "P0155 count/clearance/status mismatch")
    for field in ("MASK_A", "MASK_B"):
        image_openable(p155[field])
    mandatory = read_csv("R111_MANDATORY_RELATION_FINAL_ADJUDICATION.csv")
    required_pairs = [r for r in pairs if r["REQUIRED_BY_921"].lower() == "true"]
    require(len(mandatory) == 154 == len(required_pairs), "mandatory relation count mismatch")
    require(all(r["PASS_FAIL"] == "PASS" and r["R111_FINAL_STATUS"] == "PASS" for r in mandatory), "mandatory relation failure")
    relation = read_csv("R111_RELATION_MANUAL_LEDGER.csv")
    require(len(relation) == 9 and len({r["PAIR_ID"] for r in relation}) == 9, "relation manual ledger coverage mismatch")
    opened = [key for key in relation[0] if key.endswith("OPENED")]
    require(all(all(as_true(r[key]) for key in opened) for r in relation), "unopened 1x/8x relation asset")
    require(next(r for r in relation if r["PAIR_ID"] == "P0155")["MANUAL_DECISION"] == "FAIL", "P0155 manual decision mismatch")
    curve = json.loads((ROOT / "r111_curve_raw_recheck_v2" / "R111_CURVE_RAW_RECHECK.json").read_text(encoding="utf-8"))
    require(curve.get("final_visible_overlap_px") == 139 and curve.get("final_visible_min_clearance_px") == 0.0 and curve.get("raw_overlap_px") == 139, "canonical curve raw-mask count mismatch")
    require(curve.get("math_semantics", {}).get("source_functions_cross") is False and curve.get("all_opaque_external_pair_intersection_px") == 0, "curve semantic/opaque-occluder check mismatch")
    for name in ("original_raw_1x.png", "original_raw_8x_nearest.png", "mask_A_training_1x.png", "mask_A_training_8x_nearest.png", "mask_B_validation_1x.png", "mask_B_validation_8x_nearest.png", "intersection_1x.png", "intersection_8x_nearest.png", "overlay_1x.png", "overlay_8x_nearest.png"):
        image_openable("r111_curve_raw_recheck_v2/" + name)
    CHECKS["pairs_relations_and_raw_curve"] = {"pairs": len(pairs), "pairs_pass": 189, "pairs_fail": 1, "mandatory": len(mandatory), "P0155_overlap": 139, "P0155_clearance": 0.0}

    clip = read_csv("R111_CLIP_FINAL_ADJUDICATION.csv")
    require(len(clip) == 20 and {r["OBJECT_ID"] for r in clip} == object_ids, "clip object coverage mismatch")
    require(all(r["R111_CLIP_PASS"] == "PASS" and int(r["CROP_EDGE_FOREGROUND_PX"]) == 0 and int(r["PDF_PAGE_EDGE_FOREGROUND_PX"]) == 0 for r in clip), "clip failure")
    CHECKS["clip"] = {"objects": len(clip), "clip_pixel_count": 0, "pass": True}

    register = read_csv("R111_CANONICAL_EVIDENCE_REGISTER.csv")
    no_blank_rows(register, "canonical register")
    for row in register:
        if row["STATUS"].startswith("CANONICAL") or row["STATUS"].startswith("SUPPORTING") or row["STATUS"].startswith("RAW_BASELINE"):
            require((ROOT / row["ARTIFACT"]).exists(), f"registered artifact absent: {row['ARTIFACT']}")
    CHECKS["canonical_register"] = {"rows": len(register), "pass": True}

    for name in ("R111_DRAW_ORDER_CLIP_AUDIT.md", "R111_MATH_SEMANTICS_AUDIT.md", "after_visual_acceptance.md", "R111_SA1_REPORT.md"):
        require((ROOT / name).is_file(), f"missing final report: {name}")
    acceptance = (ROOT / "after_visual_acceptance.md").read_text(encoding="utf-8")
    report = (ROOT / "R111_SA1_REPORT.md").read_text(encoding="utf-8")
    for token in ("RESULT: FAIL", "PIXEL_HEIGHT_PASS` | `false", "ROLE_RATIO_PASS` | `false", "OVERLAP_PIXEL_COUNT` | `139", "CLIP_PIXEL_COUNT` | `0"):
        require(token in acceptance, f"visual acceptance missing/inconsistent token: {token}")
    for token in ("EVIDENCE_INTEGRITY: PASS", "FIGURE_HARD_GATES: FAIL", "139 px", "516 px", "37 px"):
        require(token in report, f"SA1 report missing required token: {token}")
    CHECKS["reports"] = {"final_result": "FAIL", "integrity_claim": "PASS", "figure_hard_gates": "FAIL"}

    integrity_pass = not FAILURES
    result = {
        "figure_id": "FIG-P157-01",
        "revision": "R111",
        "machine_check_execution": "PASS" if integrity_pass else "FAIL",
        "evidence_integrity_result": "PASS" if integrity_pass else "FAIL",
        "figure_hard_gates_result": "FAIL",
        "expected_final_result": "FAIL_TO_SA2",
        "checks": CHECKS,
        "failures": FAILURES,
        "canonical_curve_result": {"pair": "P0155", "final_visible_overlap_px": 139, "min_clearance_px": 0.0, "legacy_516_retracted": True, "legacy_37_retracted": True},
        "hard_failures": [
            "P0155 independent-curve final-visible raw-mask intersection 139px / clearance 0",
            "five valid low-profile calibrated pixel failures",
            "BODY REGION_LABEL/CJK role ratio 0.9459 below 0.95",
        ],
    }
    (ROOT / "R111_MACHINE_FINAL_CHECK.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"machine_check_execution": result["machine_check_execution"], "evidence_integrity_result": result["evidence_integrity_result"], "figure_hard_gates_result": result["figure_hard_gates_result"], "failure_count": len(FAILURES)}, ensure_ascii=False))
    if FAILURES:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
