"""Independent pre-terminal consistency check for the local R12 repair package."""
from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
PROJECT = Path(r"D:\Users\ASUS\Desktop\机器学习")
SOURCE = PROJECT / r"v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C08\full_course_synthesis_map.tex"
AFTER_SHA = "00213AE30379E4337830B1C4957BE4CB7B1E99BE88144E2D7D262998E1B6CAAA"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def rows(name: str) -> list[dict[str, str]]:
    with (ROOT / name).open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def open_png(path: Path) -> None:
    require(path.suffix.lower() == ".png" and path.is_file(), f"missing ordinary PNG: {path}")
    with Image.open(path) as image:
        image.load()
        require(image.width > 0 and image.height > 0, f"invalid PNG dimensions: {path}")


def main() -> None:
    for forbidden in ("TERMINAL_STATUS.md", "MANIFEST.sha256", "WRITE_STOPPED"):
        require(not (ROOT / forbidden).exists(), f"terminal artifact created before final check: {forbidden}")
    require(sha(SOURCE) == AFTER_SHA == sha(ROOT / "source_after_00213AEA.tex"), "final source identity mismatch")
    require(sha(ROOT / "source_before_75A691EF.tex") == "75A691EF23E041AAD59A8C738A68E96427F2EC09B2BF0D48DFC2F3134E84358E", "baseline source identity mismatch")
    diff_lines = (ROOT / "SOURCE_DIFF.patch").read_text(encoding="utf-8").splitlines()
    require(sum(line.startswith("@@") for line in diff_lines) == 3, "unexpected unified-diff hunk count")
    require(not (ROOT / "build" / "texmf-var").exists() and not (ROOT / "__pycache__").exists(), "transient cache remains")
    require(not list(ROOT.glob("R115_*")), "R115 temporary alias remains in R12 evidence root")

    required = [
        "BUILD_AUDIT.md", "LOCAL_AUDIT_REPORT.md", "MATHEMATICAL_AND_SEMANTIC_AUDIT.md", "OCCLUSION_AND_INTEGRITY.md",
        "R12_LOCAL_VISUAL_HARMONY.md", "R12_PRESEAL_MACHINE_CHECK.json", "REPAIR_BEFORE_AFTER.csv",
        "render_manifest.json", "object_inventory.csv", "all_unordered_pairs.csv", "after_overlap_report.csv",
        "mandatory_relationships.csv", "clip_report.csv", "glyph_file_manifest.csv", "glyph_machine_integrity.csv",
        "R12_GLYPH_100_PERCENT_LOCAL_LEDGER.csv", "R12_CONTACT_MACHINE_OPEN_LOG.csv", "R12_RELATION_ROI_LOCAL_LEDGER.csv",
        "R12_PIXEL_FINAL_ADJUDICATION.csv", "R12_D_E_FINAL_ADJUDICATION.csv", "R12_D_E_ROLE_SUMMARY.csv",
        "after_font_audit.csv", "R12_LOW_PROFILE_CALIBRATION_MANIFEST.csv", "R12_LOW_PROFILE_CALIBRATION_VALIDATION.csv",
        "full_page_300dpi.png", "full_page_200dpi.png", "figure_crop_300dpi.png", "standalone_300dpi.png",
        "grayscale_300dpi.png", "standalone_direct_full_300dpi.png", "after_text_measurement_overlay_300dpi.png",
        "build/page/FIG-P756-01_R12_page.pdf", "build/page/FIG-P756-01_R12_page.log",
        "build/standalone/FIG-P756-01_R12_standalone.pdf", "build/standalone/FIG-P756-01_R12_standalone.log",
    ]
    missing = [name for name in required if not (ROOT / name).is_file()]
    require(not missing, f"required artifact missing: {missing}")

    render = json.loads((ROOT / "render_manifest.json").read_text(encoding="utf-8"))
    require(render["figure_id"] == "FIG-P756-01" and render["physical_page"] == 1, "render identity mismatch")
    require(render["native_300dpi_size_px"] == [2481, 3508], "render grid mismatch")
    require(render["candidate_scope"] == "LOCAL_PAGE_WRAPPER_ONLY__ROOT_OFFICIAL_FULLBOOK_REQUAL_REQUIRED", "local scope not explicit")
    render_text = json.dumps(render, ensure_ascii=False)
    require("p801" not in render_text and "-f 801" not in render_text and "official R95" not in render_text, "stale official-R95 provenance in render manifest")
    for path in [
        ROOT / "full_page_300dpi.png", ROOT / "full_page_200dpi.png", ROOT / "figure_crop_300dpi.png",
        ROOT / "standalone_300dpi.png", ROOT / "grayscale_300dpi.png", ROOT / "standalone_direct_full_300dpi.png",
        ROOT / "after_text_measurement_overlay_300dpi.png",
    ]:
        open_png(path)

    logs = [ROOT / "build/page/FIG-P756-01_R12_page.log", ROOT / "build/standalone/FIG-P756-01_R12_standalone.log"]
    hard = re.compile(r"(^!|fatal error|emergency stop|undefined control sequence|latex error|missing character|overfull|underfull|font warning)", re.I | re.M)
    require(all(not hard.search(path.read_text(encoding="utf-8", errors="replace")) for path in logs), "build log hard failure")

    inventory = rows("object_inventory.csv")
    foreground = [r for r in inventory if r["FOREGROUND_FOR_RELATIONS"] == "true"]
    require(len(inventory) == 56 and len(foreground) == 55 and len({r["OBJECT_ID"] for r in inventory}) == 56, "object inventory failure")
    for row in inventory:
        require(row["EMPTY_MASK"] == "false", f"empty mask flag: {row['OBJECT_ID']}")
        open_png(ROOT / row["FINAL_VISIBLE_MASK"])
        open_png(ROOT / row["PRE_OCCLUSION_MASK"])
    pairs = rows("all_unordered_pairs.csv")
    require(len(pairs) == 1485 and len({r["PAIR_ID"] for r in pairs}) == 1485 and all(r["PASS_FAIL"] == "PASS" for r in pairs), "unordered pair audit failure")
    require((ROOT / "all_unordered_pairs.csv").read_bytes() == (ROOT / "after_overlap_report.csv").read_bytes(), "after overlap alias diverged")
    mandatory = rows("mandatory_relationships.csv")
    require(len(mandatory) == 1107 and all(r["PASS_FAIL"] == "PASS" for r in mandatory), "mandatory relation failure")
    p1408 = next(r for r in pairs if r["PAIR_ID"] == "P1408")
    require((p1408["OBJECT_A"], p1408["OBJECT_B"], p1408["OVERLAP_PIXEL_COUNT"], p1408["MIN_CLEARANCE_PX"], p1408["PASS_FAIL"]) == ("O-G016", "O-G017", "0", "20.0000", "PASS"), "P1408 not closed")
    relation_ledger = rows("R12_RELATION_ROI_LOCAL_LEDGER.csv")
    require(len(relation_ledger) == 24 and all(r["PASS_FAIL"] == "PASS" and r["ROI_IMAGES_MACHINE_OPENED"] == "10" for r in relation_ledger), "ROI ledger failure")
    roi_names = [
        "original_raw_1x.png", "mask_A_1x.png", "mask_B_1x.png", "intersection_1x.png", "overlay_1x.png",
        "original_raw_8x_nearest.png", "mask_A_8x_nearest.png", "mask_B_8x_nearest.png", "intersection_8x_nearest.png", "overlay_8x_nearest.png",
    ]
    for row in relation_ledger:
        for name in roi_names:
            open_png(ROOT / row["ROI_PACKAGE"] / name)

    glyphs = rows("glyph_file_manifest.csv")
    ledger = rows("R12_GLYPH_100_PERCENT_LOCAL_LEDGER.csv")
    pixel = rows("R12_PIXEL_FINAL_ADJUDICATION.csv")
    integrity = rows("glyph_machine_integrity.csv")
    de = rows("R12_D_E_FINAL_ADJUDICATION.csv")
    require(len(glyphs) == len(ledger) == len(pixel) == len(integrity) == len(de) == 378, "glyph coverage mismatch")
    require(len({r["GLYPH_ID"] for r in ledger}) == 378, "duplicate glyph ledger row")
    require(all(r["PIXEL_DECISION"] == "PASS" and r["MASK_PURITY_COMPLETENESS_PASS"] == "true" and r["FOREIGN_PIXEL_PX"] == "0" and r["MISSING_STROKE_PX"] == "0" for r in ledger), "100% glyph ledger failure")
    require(all(r["D_E_ROW_DECISION"] == "PASS" for r in de), "D/E failure")
    fixed = {r["GLYPH_ID"]: r for r in ledger if r["GLYPH_ID"] in {"G0208", "G0212", "G0222"}}
    require((fixed["G0208"]["CHAR"], fixed["G0208"]["H_INK_PX"]) == ("出", "34"), "G0208 failure")
    require((fixed["G0212"]["CHAR"], fixed["G0212"]["H_INK_PX"]) == ("入", "35"), "G0212 failure")
    require((fixed["G0222"]["CHAR"], fixed["G0222"]["H_INK_PX"]) == ("入", "35"), "G0222 failure")
    contacts = rows("R12_CONTACT_MACHINE_OPEN_LOG.csv")
    require(len(contacts) == 143 and sum(r["SCALE"] == "1x_native_300dpi" for r in contacts) == 48 and sum(r["SCALE"] == "8x_nearest" for r in contacts) == 95, "contact coverage mismatch")
    for row in contacts:
        require(row["MACHINE_DECODE_STATUS"] == "PASS", "contact decode failure")
        open_png(ROOT / row["SHEET"])
    calibration_manifest = rows("R12_LOW_PROFILE_CALIBRATION_MANIFEST.csv")
    calibration = rows("R12_LOW_PROFILE_CALIBRATION_VALIDATION.csv")
    require(len(calibration_manifest) == 10 and all(r["FONT_WEIGHT_COLOR_SIZE_300DPI_VALID"] == "true" for r in calibration_manifest), "calibration manifest failure")
    require(len(calibration) == 20 and all(r["LOW_PROFILE_TOTAL_GATE_PASS"] == "true" for r in calibration), "low-profile calibration failure")
    for row in calibration_manifest:
        require("local_R12_candidate" in row["CALIBRATION_PDF"] and (ROOT / row["CALIBRATION_PDF"]).is_file(), "local calibration PDF provenance failure")
        for key in ("RAW_1X", "OVERLAY_1X", "MASK_1X"):
            open_png(ROOT / row[key])
        cid = row["CALIBRATION_ID"]
        for name in (f"{cid}_raw_8x_nearest.png", f"{cid}_target_overlay_8x_nearest.png", f"{cid}_mask_8x_nearest.png"):
            open_png(ROOT / "low_profile_calibration" / "raw_cid_replay_v2" / name)
    fonts = rows("after_font_audit.csv")
    require(fonts and all(r["SAME_PANEL_STATUS"] == "PASS" and r["CROSS_PANEL_SOURCE_STATUS"].startswith("PASS") and r["CROSS_PANEL_E_STATUS"].startswith("PASS") for r in fonts), "font-role failure")
    clips = rows("clip_report.csv")
    require(len(clips) == 55 and all(r["CLIP_PASS"] == "true" and r["CROP_EDGE_FOREGROUND_PX"] == "0" and r["PDF_PAGE_EDGE_FOREGROUND_PX"] == "0" for r in clips), "clip failure")

    repairs = rows("REPAIR_BEFORE_AFTER.csv")
    require(len(repairs) == 4 and {r["FAILURE_ID"] for r in repairs} == {"P1408", "G0208", "G0212", "G0222"}, "before/after closure table failure")
    preseal = json.loads((ROOT / "R12_PRESEAL_MACHINE_CHECK.json").read_text(encoding="utf-8"))
    require(preseal["local_result"] == "LOCAL_PASS_TO_ROOT_BUILD" and preseal["final_official_result"].startswith("NOT_AUTHORIZED"), "preseal result scope failure")
    result = {
        "figure_id": "FIG-P756-01",
        "check_scope": "local R12 page/standalone only",
        "source_sha256": AFTER_SHA,
        "required_artifacts_present": len(required),
        "objects": 56,
        "foreground_objects": 55,
        "unordered_pairs": 1485,
        "mandatory_relations": 1107,
        "pair_failures": 0,
        "p1408_overlap_px": 0,
        "p1408_clearance_px": 20.0,
        "glyphs": 378,
        "glyph_pixel_failures": 0,
        "glyph_integrity_failures": 0,
        "d_e_failures": 0,
        "low_profile_targets": 20,
        "contact_sheets_machine_opened": 143,
        "critical_roi_packages_machine_opened": 24,
        "clip_failures": 0,
        "cache_clean": True,
        "result": "PRETERMINAL_PASS__LOCAL_PASS_TO_ROOT_BUILD",
        "final_official_pass": False,
        "next_gate": "root official full-book build plus independent SA1/SA3 strict requalification",
    }
    (ROOT / "R12_MACHINE_FINAL_CHECK.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
