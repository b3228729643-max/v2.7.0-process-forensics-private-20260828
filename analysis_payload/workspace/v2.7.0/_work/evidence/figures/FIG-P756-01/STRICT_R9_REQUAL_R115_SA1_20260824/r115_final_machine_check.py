from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent


def rows(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def main() -> None:
    manifest = json.loads((ROOT / "render_manifest.json").read_text(encoding="utf-8"))
    require(manifest["figure_id"] == "FIG-P756-01", "Wrong figure ID")
    require(manifest["physical_page"] == 801 and manifest["printed_page"] == 788, "Wrong page locator")
    require(manifest["native_300dpi_size_px"] == [2481, 3508], "Native 300dpi grid mismatch")
    require(Path(manifest["candidate_pdf"]).is_file(), "Official candidate PDF unavailable")

    inventory = rows("object_inventory.csv")
    require(len(inventory) == 56, f"Expected 56 inventory objects including halo background, got {len(inventory)}")
    foreground = [r for r in inventory if r["FOREGROUND_FOR_RELATIONS"] == "true"]
    require(len(foreground) == 55, f"Expected 55 foreground objects, got {len(foreground)}")
    object_ids = {r["OBJECT_ID"] for r in inventory}
    require(len(object_ids) == 56, "Duplicate object IDs")
    missing_object_masks = [r["FINAL_VISIBLE_MASK"] for r in inventory if not (ROOT / r["FINAL_VISIBLE_MASK"]).is_file()]
    require(not missing_object_masks, f"Missing object masks: {missing_object_masks}")

    pairs = rows("all_unordered_pairs.csv")
    require(len(pairs) == 1485 == 55 * 54 // 2, f"Bad unordered-pair coverage: {len(pairs)}")
    failures = [r for r in pairs if r["PASS_FAIL"] == "FAIL"]
    require(len(failures) == 1 and failures[0]["PAIR_ID"] == "P1408", f"Unexpected pair failures: {failures}")
    p1408 = failures[0]
    require(p1408["OBJECT_A"] == "O-G016" and p1408["OBJECT_B"] == "O-G017", "P1408 object IDs changed")
    require(p1408["OVERLAP_PIXEL_COUNT"] == "792" and p1408["MIN_CLEARANCE_PX"] == "0.0000", "P1408 measurement changed")
    mandatory = rows("mandatory_relationships.csv")
    require(len(mandatory) == 1107, f"Bad mandatory relation count: {len(mandatory)}")

    relation_ledger = rows("R115_HUMAN_RELATION_ROI_LEDGER.csv")
    require(len(relation_ledger) == 24, f"Expected 24 human ROI rows, got {len(relation_ledger)}")
    require(len({r["PAIR_ID"] for r in relation_ledger}) == len(relation_ledger), "Duplicate relation rows")
    require(all(r["NATIVE_1X_ALL_FIVE_OPENED"] == "YES" and r["NEAREST_8X_ALL_FIVE_OPENED"] == "YES" for r in relation_ledger), "Incomplete human ROI viewing")
    rel_fails = [r for r in relation_ledger if r["HUMAN_DECISION"] == "FAIL"]
    require(len(rel_fails) == 1 and rel_fails[0]["PAIR_ID"] == "P1408", "Human ROI failure ledger inconsistent")
    expected_roi_images = [
        "original_raw_1x.png", "mask_A_1x.png", "mask_B_1x.png", "intersection_1x.png", "overlay_1x.png",
        "original_raw_8x_nearest.png", "mask_A_8x_nearest.png", "mask_B_8x_nearest.png", "intersection_8x_nearest.png", "overlay_8x_nearest.png",
    ]
    missing_roi_files = []
    for r in relation_ledger:
        package = ROOT / r["ROI_PACKAGE"]
        for name in expected_roi_images:
            if not (package / name).is_file():
                missing_roi_files.append(str(package / name))
    require(not missing_roi_files, f"Missing ROI views: {missing_roi_files}")

    glyph_manifest = rows("glyph_file_manifest.csv")
    glyph_human = rows("R115_HUMAN_GLYPH_LEDGER.csv")
    glyph_machine = rows("glyph_machine_integrity.csv")
    require(len(glyph_manifest) == len(glyph_human) == len(glyph_machine) == 378, "Glyph coverage count mismatch")
    glyph_ids = {r["GLYPH_ID"] for r in glyph_manifest}
    require(glyph_ids == {r["GLYPH_ID"] for r in glyph_human} == {r["GLYPH_ID"] for r in glyph_machine}, "Glyph ID coverage mismatch")
    require(all(r["HUMAN_VISIBLE_INTEGRITY"] == "PASS" for r in glyph_human), "Human glyph ledger has a visible-integrity failure")
    require(all(r["MASK_PURITY_COMPLETENESS_PASS"] == "true" for r in glyph_machine), "Machine glyph integrity failure")
    contact_log = rows("R115_CONTACT_VIEW_OPEN_LOG.csv")
    one_x = [r for r in contact_log if r["SCALE"] == "1x native 300dpi"]
    eight_x = [r for r in contact_log if r["SCALE"] == "8x nearest-neighbour"]
    require(len(contact_log) == 143 and len(one_x) == 48 and len(eight_x) == 95, "Contact-sheet open log mismatch")
    require(all(r["VIEW_STATUS"] == "OPENED" for r in contact_log), "Unopened contact sheet recorded")

    pixel = rows("R115_PIXEL_FINAL_ADJUDICATION.csv")
    pixel_fails = [r for r in pixel if r["R115_FINAL_PIXEL_DECISION"] == "FAIL"]
    expected_pixel_fails = {"G0208", "G0212", "G0222"}
    require(len(pixel) == 378 and {r["GLYPH_ID"] for r in pixel_fails} == expected_pixel_fails, "Pixel final adjudication mismatch")
    require(all(r["LOW_PROFILE"] == "false" and r["CHAR"] == "口" and r["H_INK_PX"] == "29" for r in pixel_fails), "Pixel fail characterization mismatch")

    calibration_manifest = rows("R115_LOW_PROFILE_CALIBRATION_MANIFEST.csv")
    calibration_validation = rows("R115_LOW_PROFILE_CALIBRATION_VALIDATION.csv")
    calibration_human = rows("R115_LOW_PROFILE_CALIBRATION_HUMAN_LEDGER.csv")
    require(len(calibration_manifest) == 10 and len(calibration_validation) == 20 and len(calibration_human) == 10, "Calibration counts mismatch")
    require(all(r["FONT_WEIGHT_COLOR_SIZE_300DPI_VALID"] == "true" for r in calibration_manifest), "Invalid calibration group")
    require(all(r["FONT_WEIGHT_COLOR_SIZE_300DPI_PURITY_VALID"] == "true" and r["RAW_CROP_EXACT"] == "true" and r["MASK_CROP_EXACT"] == "true" for r in calibration_validation), "Invalid calibration target")
    require(all(r["HUMAN_CALIBRATION_DECISION"] == "VALID" for r in calibration_human), "Human calibration ledger inconsistent")
    require((ROOT / "low_profile_calibration" / "calibration_source_raw_cid_replay_from_official_v2.pdf").is_file(), "Valid raw-CID calibration PDF missing")

    clips = rows("clip_report.csv")
    require(len(clips) == 55 and all(r["R115_CLIP_PASS"] == "PASS" for r in clips), "Clipping gate failed or incomplete")
    de = json.loads((ROOT / "R115_D_E_FINAL_SUMMARY.json").read_text(encoding="utf-8"))
    require(de["glyph_count"] == 378 and de["same_class_ratio_pass"] is True and de["role_ratio_pass"] is True, "D/E gate mismatch")
    roles = rows("R115_SOURCE_FONT_ROLE_AUDIT.csv")
    require(all(r["SAME_PANEL_STATUS"].startswith("PASS") and r["CROSS_PANEL_SOURCE_STATUS"].startswith("PASS") and r["CROSS_PANEL_E_STATUS"].startswith("PASS") for r in roles), "Source-font role audit failure")
    terminal_docs = {
        "EVIDENCE_INTEGRITY.md": "**Status: PASS.**",
        "FIGURE_HARD_GATES.md": "**Final figure decision: FAIL_TO_SA2.**",
        "FINAL_AUDIT_REPORT.md": "**FAIL_TO_SA2**",
    }
    for name, marker in terminal_docs.items():
        content = (ROOT / name).read_text(encoding="utf-8")
        require(marker in content, f"Terminal document missing expected marker: {name}")

    summary = {
        "figure_id": "FIG-P756-01",
        "official_candidate_pdf": manifest["candidate_pdf"],
        "source_page": {"physical": 801, "printed": 788, "native_grid": "2481x3508 at 300dpi"},
        "inventory": {"inventory_objects_including_halo_background": len(inventory), "foreground_objects": len(foreground), "glyphs": len(glyph_manifest)},
        "pair_gate": {"all_unordered_pairs": len(pairs), "mandatory_relationships": len(mandatory), "failures": [{"pair_id": "P1408", "objects": ["O-G016", "O-G017"], "overlap_px": 792, "clearance_px": 0}]},
        "human_review": {"glyph_contact_views": len(contact_log), "relation_packages": len(relation_ledger), "calibration_groups": len(calibration_human)},
        "low_profile_calibration": {"groups": len(calibration_manifest), "targets": len(calibration_validation), "invalid_targets": 0, "method": "official embedded-font raw-CID v2 replay"},
        "pixel_gate": {"pass": len(pixel) - len(pixel_fails), "fail": len(pixel_fails), "failure_glyphs": sorted(expected_pixel_fails)},
        "clip_gate": "PASS",
        "D_E_gate": "PASS",
        "terminal_reports": list(terminal_docs),
        "evidence_integrity": "PASS",
        "figure_hard_gates": "FAIL_TO_SA2",
        "hard_failures": ["P1408 independent route geometry overlap", "G0208/G0212/G0222 non-low-profile CJK pixel height 29<30"],
    }
    (ROOT / "R115_MACHINE_FINAL_CHECK.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
