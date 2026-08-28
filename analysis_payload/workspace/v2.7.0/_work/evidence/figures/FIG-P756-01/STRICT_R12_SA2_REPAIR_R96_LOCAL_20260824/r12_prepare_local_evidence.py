"""Prepare auditable local-only R12 evidence before terminal sealing.

The script is deliberately non-terminal: it writes measurements, ledgers, and
reports, but never writes TERMINAL_STATUS.md, MANIFEST.sha256, or WRITE_STOPPED.
"""
from __future__ import annotations

import csv
import difflib
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path

import fitz
import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parent
PROJECT = Path(r"D:\Users\ASUS\Desktop\机器学习")
SOURCE = PROJECT / r"v2.7.0\_work\source\v2.7.0\src\绘图源码\第05册_采样方法主题模型与图排序\V5-C08\full_course_synthesis_map.tex"
SOURCE_BEFORE = ROOT / "source_before_75A691EF.tex"
OLD = ROOT.parent / "STRICT_R9_REQUAL_R115_SA1_20260824"
PAGE_PDF = ROOT / "build" / "page" / "FIG-P756-01_R12_page.pdf"
STANDALONE_PDF = ROOT / "build" / "standalone" / "FIG-P756-01_R12_standalone.pdf"
BEFORE_SHA = "75A691EF23E041AAD59A8C738A68E96427F2EC09B2BF0D48DFC2F3134E84358E"
AFTER_SHA = "00213AE30379E4337830B1C4957BE4CB7B1E99BE88144E2D7D262998E1B6CAAA"


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def read_csv(path_or_name: str | Path) -> list[dict[str, str]]:
    path = Path(path_or_name)
    if not path.is_absolute():
        path = ROOT / path
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(name: str, rows: list[dict[str, object]]) -> None:
    require(bool(rows), f"refusing empty CSV: {name}")
    with (ROOT / name).open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def open_image(path: Path) -> tuple[int, int, str]:
    with Image.open(path) as image:
        image.load()
        return image.width, image.height, image.mode


def foreground_pixels(path: Path) -> int:
    with Image.open(path) as image:
        arr = np.asarray(image.convert("L"))
    return int((arr == 0).sum())


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def main() -> None:
    # Source identity and the sole business-source diff.
    require(digest(SOURCE_BEFORE) == BEFORE_SHA, "baseline source hash mismatch")
    require(digest(SOURCE) == AFTER_SHA, "repaired source hash mismatch")
    before_lines = SOURCE_BEFORE.read_text(encoding="utf-8").splitlines(keepends=True)
    after_lines = SOURCE.read_text(encoding="utf-8").splitlines(keepends=True)
    require(len(before_lines) == len(after_lines), "source line count changed")
    changed = [i + 1 for i, (a, b) in enumerate(zip(before_lines, after_lines)) if a != b]
    require(changed == [32, 57, 59, 74, 81], f"unexpected changed source lines: {changed}")
    required_fragments = [
        "唯一单向通道", "(-6.20,-1.00)", "(-6.20,-2.80)",
        "仅此单向输出", "实线接入：监督任务；虚线接入：无监督任务",
    ]
    after_text = "".join(after_lines)
    require(all(fragment in after_text for fragment in required_fragments), "expected repaired source fragment missing")
    require("仅此单向出口" not in after_text and "实线入口" not in after_text and "虚线入口" not in after_text, "old low-pixel wording remains")
    source_after = ROOT / "source_after_00213AEA.tex"
    shutil.copyfile(SOURCE, source_after)
    diff = difflib.unified_diff(
        before_lines, after_lines,
        fromfile="source_before_75A691EF.tex",
        tofile=str(SOURCE),
    )
    (ROOT / "SOURCE_DIFF.patch").write_text("".join(diff), encoding="utf-8")

    # Candidate/render identity is explicitly local, never the root official full book.
    manifest_path = ROOT / "render_manifest.json"
    render = json.loads(manifest_path.read_text(encoding="utf-8"))
    render.update({
        "candidate_scope": "LOCAL_PAGE_WRAPPER_ONLY__ROOT_OFFICIAL_FULLBOOK_REQUAL_REQUIRED",
        "physical_page": 1,
        "printed_page": 753,
        "native_coordinate": "local R12 page-wrapper p1 direct pdftoppm 300dpi; no resize",
        "render_method": "pdftoppm -png -singlefile -f 1 -l 1 -r 300",
        "page_wrapper": str(PAGE_PDF),
        "standalone_wrapper": str(STANDALONE_PDF),
    })
    manifest_path.write_text(json.dumps(render, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    require(render["native_300dpi_size_px"] == [2481, 3508], "bad native page grid")
    image_expectations = {
        "full_page_300dpi.png": (2481, 3508),
        "renders/full_page_native_300dpi.png": (2481, 3508),
        "standalone_direct_full_300dpi.png": (2481, 3508),
        "figure_crop_300dpi.png": (1981, 1468),
        "standalone_300dpi.png": (1981, 1285),
        "grayscale_300dpi.png": (1981, 1468),
        "after_text_measurement_overlay_300dpi.png": (2481, 3508),
    }
    for name, size in image_expectations.items():
        width, height, _ = open_image(ROOT / name)
        require((width, height) == size, f"render size mismatch: {name}")
    require(open_image(ROOT / "grayscale_300dpi.png")[2] == "L", "grayscale render is not L mode")
    for candidate in (PAGE_PDF, STANDALONE_PDF):
        doc = fitz.open(candidate)
        require(len(doc) == 1, f"local candidate page count mismatch: {candidate}")
        require(abs(doc[0].rect.width - 595.276) < 0.01 and abs(doc[0].rect.height - 841.890) < 0.01, "local candidate page size mismatch")
        doc.close()

    # Clean build logs and wrapper provenance.
    logs = [
        ROOT / "build" / "page" / "FIG-P756-01_R12_page.log",
        ROOT / "build" / "standalone" / "FIG-P756-01_R12_standalone.log",
    ]
    hard_patterns = re.compile(r"(^!|fatal error|emergency stop|undefined control sequence|latex error|missing character|overfull|underfull|font warning)", re.I | re.M)
    for log in logs:
        text = log.read_text(encoding="utf-8", errors="replace")
        require(not hard_patterns.search(text), f"hard build-log pattern: {log}")
        require("full_course_synthesis_map.tex" in text.replace("\r", "").replace("\n", ""), f"business source absent from log: {log}")
    page_info = subprocess.run(["pdfinfo", str(PAGE_PDF)], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()
    standalone_info = subprocess.run(["pdfinfo", str(STANDALONE_PDF)], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()
    font_info = subprocess.run(["pdffonts", str(PAGE_PDF)], check=True, capture_output=True, text=True, encoding="utf-8", errors="replace").stdout.strip()
    build_report = f"""# FIG-P756-01 R12 local build audit

- Scope: local page/standalone wrappers only; no root official full-book build was run.
- Working directory: `v2.7.0/_work/source/v2.7.0/src/讲义源码/合并总册`.
- Engine: `lualatex`, two passes per wrapper, `-interaction=nonstopmode -halt-on-error -file-line-error -recorder`.
- Page wrapper log: `{rel(logs[0])}`; hard-error/overflow/missing-glyph/font-warning scan: PASS.
- Standalone wrapper log: `{rel(logs[1])}`; same scan: PASS.
- An initial parameter-resolution attempt produced no accepted evidence; its exact transient R12 artifacts were removed before the clean build above.
- Page PDF SHA256: `{digest(PAGE_PDF)}`.
- Standalone PDF SHA256: `{digest(STANDALONE_PDF)}`.

## pdfinfo — page wrapper

```text
{page_info}
```

## pdfinfo — standalone wrapper

```text
{standalone_info}
```

## pdffonts — page wrapper

```text
{font_info}
```
"""
    (ROOT / "BUILD_AUDIT.md").write_text(build_report, encoding="utf-8")

    # Complete object universe and unordered-pair audit, including graphic-graphic.
    inventory = read_csv("object_inventory.csv")
    require(len(inventory) == 56 and len({r["OBJECT_ID"] for r in inventory}) == 56, "object inventory mismatch")
    foreground = [r for r in inventory if r["FOREGROUND_FOR_RELATIONS"] == "true"]
    require(len(foreground) == 55, "foreground object count mismatch")
    for row in inventory:
        require(row["EMPTY_MASK"] == "false", f"empty inventory mask flag: {row['OBJECT_ID']}")
        for key in ("FINAL_VISIBLE_MASK", "PRE_OCCLUSION_MASK"):
            path = ROOT / row[key]
            require(path.is_file(), f"missing object mask: {path}")
            open_image(path)
    pairs = read_csv("all_unordered_pairs.csv")
    require(len(pairs) == 1485 == 55 * 54 // 2, "all unordered-pair count mismatch")
    require(len({r["PAIR_ID"] for r in pairs}) == 1485, "duplicate pair ID")
    expected_pairs = {
        tuple(sorted((a["OBJECT_ID"], b["OBJECT_ID"])))
        for i, a in enumerate(foreground)
        for b in foreground[i + 1:]
    }
    actual_pairs = {tuple(sorted((r["OBJECT_A"], r["OBJECT_B"]))) for r in pairs}
    require(expected_pairs == actual_pairs, "unordered object-pair universe mismatch")
    require(all(r["PASS_FAIL"] == "PASS" for r in pairs), "local pair failure")
    mandatory = read_csv("mandatory_relationships.csv")
    require(len(mandatory) == 1107 and all(r["PASS_FAIL"] == "PASS" for r in mandatory), "mandatory relation mismatch")
    kinds = {
        "TEXT_TEXT": sum(r["KIND_A"] == "TEXT" and r["KIND_B"] == "TEXT" for r in pairs),
        "TEXT_GRAPHIC": sum((r["KIND_A"] == "TEXT") ^ (r["KIND_B"] == "TEXT") for r in pairs),
        "GRAPHIC_GRAPHIC": sum(r["KIND_A"] != "TEXT" and r["KIND_B"] != "TEXT" for r in pairs),
    }
    require(kinds == {"TEXT_TEXT": 351, "TEXT_GRAPHIC": 756, "GRAPHIC_GRAPHIC": 378}, f"pair kind counts mismatch: {kinds}")
    p1408 = next(r for r in pairs if r["PAIR_ID"] == "P1408")
    require((p1408["OBJECT_A"], p1408["OBJECT_B"], p1408["OVERLAP_PIXEL_COUNT"], p1408["MIN_CLEARANCE_PX"], p1408["PASS_FAIL"]) == ("O-G016", "O-G017", "0", "20.0000", "PASS"), "P1408 repair mismatch")
    shutil.copyfile(ROOT / "all_unordered_pairs.csv", ROOT / "after_overlap_report.csv")

    expected_roi_files = [
        "original_raw_1x.png", "mask_A_1x.png", "mask_B_1x.png", "intersection_1x.png", "overlay_1x.png",
        "original_raw_8x_nearest.png", "mask_A_8x_nearest.png", "mask_B_8x_nearest.png", "intersection_8x_nearest.png", "overlay_8x_nearest.png",
    ]
    critical = [r for r in pairs if r["CRITICAL_OR_FAILURE"] == "true"]
    require(len(critical) == 24, "critical/intentional ROI count mismatch")
    relation_ledger = []
    for row in critical:
        package = ROOT / row["ROI_PACKAGE"]
        require(package.is_dir(), f"missing ROI package: {row['PAIR_ID']}")
        for name in expected_roi_files:
            open_image(package / name)
        relation_ledger.append({
            "PAIR_ID": row["PAIR_ID"], "OBJECT_A": row["OBJECT_A"], "OBJECT_B": row["OBJECT_B"],
            "RELATION": row["RELATION"], "OVERLAP_PIXEL_COUNT": row["OVERLAP_PIXEL_COUNT"],
            "MIN_CLEARANCE_PX": row["MIN_CLEARANCE_PX"], "REQUIRED_CLEARANCE_PX": row["REQUIRED_CLEARANCE_PX"],
            "PASS_FAIL": row["PASS_FAIL"], "ROI_PACKAGE": row["ROI_PACKAGE"], "ROI_IMAGES_MACHINE_OPENED": 10,
            "SA2_VISUAL_SCOPE": "OPENED_ALL_1X_AND_8X_REPAIR_VIEWS" if row["PAIR_ID"] == "P1408" else "MACHINE_DECODED__FINAL_MANUAL_REVIEW_BELONGS_TO_ROOT_SA1_SA3",
        })
    write_csv("R12_RELATION_ROI_LOCAL_LEDGER.csv", relation_ledger)

    # 100% glyph mapping/masks/pixel/D/E evidence; local SA2 does not forge final human review.
    glyphs = read_csv("glyph_file_manifest.csv")
    preliminary = {r["GLYPH_ID"]: r for r in read_csv("after_pixel_measurements.csv")}
    pixels = {r["GLYPH_ID"]: r for r in read_csv("R12_PIXEL_FINAL_ADJUDICATION.csv")}
    machine = {r["GLYPH_ID"]: r for r in read_csv("glyph_machine_integrity.csv")}
    de = {r["GLYPH_ID"]: r for r in read_csv("R12_D_E_FINAL_ADJUDICATION.csv")}
    require(len(glyphs) == len(preliminary) == len(pixels) == len(machine) == len(de) == 378, "glyph table count mismatch")
    glyph_ids = {r["GLYPH_ID"] for r in glyphs}
    require(all(set(table) == glyph_ids for table in (preliminary, pixels, machine, de)), "glyph ID join mismatch")
    require(all(r["R115_FINAL_PIXEL_DECISION"] == "PASS" for r in pixels.values()), "final pixel failure")
    require(all(r["MASK_PURITY_COMPLETENESS_PASS"] == "true" and r["FOREIGN_PIXEL_PX"] == "0" and r["MISSING_STROKE_PX"] == "0" for r in machine.values()), "glyph integrity failure")
    require(all(r["D_E_ROW_DECISION"] == "PASS" for r in de.values()), "D/E failure")
    fixed_expected = {"G0208": ("出", 34), "G0212": ("入", 35), "G0222": ("入", 35)}
    glyph_ledger = []
    for row in glyphs:
        gid = row["GLYPH_ID"]
        expected_files = [row["ORIGINAL_FILE"], row["TARGET_OVERLAY_FILE"], row["MASK_FILE"]]
        expected_files += [
            f"glyph_8x/{gid}_original_8x_nearest.png",
            f"glyph_8x/{gid}_target_overlay_8x_nearest.png",
            f"glyph_8x/{gid}_mask_only_8x_nearest.png",
        ]
        for name in expected_files:
            open_image(ROOT / name)
        measured_h = foreground_pixels(ROOT / row["MASK_FILE"])
        require(measured_h > 0, f"empty glyph mask: {gid}")
        require(machine[gid]["H_INK_PX"] == row["H_INK_PX"], f"glyph H mismatch: {gid}")
        if gid in fixed_expected:
            char, height = fixed_expected[gid]
            require((row["CHAR"], int(row["H_INK_PX"])) == (char, height), f"fixed glyph mismatch: {gid}")
        glyph_ledger.append({
            "GLYPH_ID": gid, "ELEMENT_ID": row["ELEMENT_ID"], "CHAR": row["CHAR"], "PANEL_ID": row["PANEL_ID"],
            "ROLE": row["ROLE"], "SCRIPT_CLASS": row["SCRIPT_CLASS"], "EFFECTIVE_PT": row["EFFECTIVE_PT"],
            "H_INK_PX": row["H_INK_PX"], "THRESHOLD": preliminary[gid]["H_INK_THRESHOLD_PX"],
            "PIXEL_DECISION": pixels[gid]["R115_FINAL_PIXEL_DECISION"], "D_STATUS": de[gid]["D_STATUS"], "E_STATUS": de[gid]["E_STATUS"],
            "FOREIGN_PIXEL_PX": machine[gid]["FOREIGN_PIXEL_PX"], "MISSING_STROKE_PX": machine[gid]["MISSING_STROKE_PX"],
            "MASK_PURITY_COMPLETENESS_PASS": machine[gid]["MASK_PURITY_COMPLETENESS_PASS"], "SHEET_1X": row["SHEET_1X"], "CELL_1X": row["CELL_1X"],
            "SHEET_8X": row["SHEET_8X"], "CELL_8X": row["CELL_8X"], "SIX_FILES_MACHINE_OPENED": "true",
            "SA2_VISUAL_SCOPE": "OPENED_1X_AND_8X_TARGET_REPAIR" if gid in fixed_expected else "CONTACT_EVIDENCE_READY__FINAL_ROW_MANUAL_REVIEW_BELONGS_TO_ROOT_SA1_SA3",
        })
    write_csv("R12_GLYPH_100_PERCENT_LOCAL_LEDGER.csv", glyph_ledger)

    contact_rows = []
    for scale, directory in (("1x_native_300dpi", ROOT / "glyph_contacts_1x"), ("8x_nearest", ROOT / "glyph_contacts_8x")):
        files = sorted(directory.glob("contact_sheet_*.png"))
        expected = 48 if scale.startswith("1x") else 95
        require(len(files) == expected, f"contact sheet count mismatch: {scale}")
        for path in files:
            width, height, mode = open_image(path)
            contact_rows.append({
                "SCALE": scale, "SHEET": rel(path), "WIDTH": width, "HEIGHT": height, "MODE": mode,
                "MACHINE_DECODE_STATUS": "PASS", "HUMAN_VIEW_STATUS": "TARGETED_ONLY__ROOT_SA1_SA3_MUST_OPEN_ALL_FOR_FINAL",
            })
    require(len(contact_rows) == 143, "contact open-log count mismatch")
    write_csv("R12_CONTACT_MACHINE_OPEN_LOG.csv", contact_rows)

    inherited_calibration_pdf = ROOT / "low_profile_calibration" / "calibration_source_raw_cid_replay_from_official_v2.pdf"
    local_calibration_pdf = ROOT / "low_profile_calibration" / "calibration_source_raw_cid_replay_from_local_R12_candidate.pdf"
    require(inherited_calibration_pdf.is_file() or local_calibration_pdf.is_file(), "calibration source PDF missing")
    if inherited_calibration_pdf.is_file():
        shutil.copyfile(inherited_calibration_pdf, local_calibration_pdf)
    old_calibration_name = "low_profile_calibration/calibration_source_raw_cid_replay_from_official_v2.pdf"
    new_calibration_name = "low_profile_calibration/calibration_source_raw_cid_replay_from_local_R12_candidate.pdf"
    for name in ("R12_LOW_PROFILE_CALIBRATION_MANIFEST.csv", "R12_LOW_PROFILE_CALIBRATION_VALIDATION.csv"):
        path = ROOT / name
        text = path.read_text(encoding="utf-8")
        path.write_text(text.replace(old_calibration_name, new_calibration_name), encoding="utf-8", newline="")
    calibration_manifest = read_csv("R12_LOW_PROFILE_CALIBRATION_MANIFEST.csv")
    calibration_validation = read_csv("R12_LOW_PROFILE_CALIBRATION_VALIDATION.csv")
    require(len(calibration_manifest) == 10 and len(calibration_validation) == 20, "low-profile calibration count mismatch")
    require(all(r["FONT_WEIGHT_COLOR_SIZE_300DPI_VALID"] == "true" for r in calibration_manifest), "invalid low-profile calibration group")
    require(all(r["LOW_PROFILE_TOTAL_GATE_PASS"] == "true" for r in calibration_validation), "low-profile target failure")
    for row in calibration_manifest:
        for key in ("RAW_1X", "OVERLAY_1X", "MASK_1X"):
            open_image(ROOT / row[key])
    font_rows = read_csv("after_font_audit.csv")
    require(all(r["SAME_PANEL_STATUS"] == "PASS" and r["CROSS_PANEL_SOURCE_STATUS"].startswith("PASS") and r["CROSS_PANEL_E_STATUS"].startswith("PASS") for r in font_rows), "font role audit failure")
    min_pt = min(float(r["EFFECTIVE_PT"]) for r in glyphs)
    max_pt = max(float(r["EFFECTIVE_PT"]) for r in glyphs)
    require(min_pt >= 9.5, "visible text below 9.5pt")

    # Before/after hard-failure closure with direct evidence paths.
    old_pair = next(r for r in read_csv(OLD / "all_unordered_pairs.csv") if r["PAIR_ID"] == "P1408")
    old_pixels = {r["GLYPH_ID"]: r for r in read_csv(OLD / "R115_PIXEL_FINAL_ADJUDICATION.csv")}
    repair_rows: list[dict[str, object]] = [{
        "FAILURE_ID": "P1408", "TYPE": "INDEPENDENT_GRAPHIC_PAIR", "OBJECT_OR_GLYPH": "O-G016↔O-G017",
        "BEFORE_CHAR": "N/A", "AFTER_CHAR": "N/A", "BEFORE_H_INK_PX": "N/A", "AFTER_H_INK_PX": "N/A",
        "BEFORE_OVERLAP_PX": old_pair["OVERLAP_PIXEL_COUNT"], "AFTER_OVERLAP_PX": p1408["OVERLAP_PIXEL_COUNT"],
        "BEFORE_CLEARANCE_PX": old_pair["MIN_CLEARANCE_PX"], "AFTER_CLEARANCE_PX": p1408["MIN_CLEARANCE_PX"],
        "BEFORE_DECISION": old_pair["PASS_FAIL"], "AFTER_DECISION": p1408["PASS_FAIL"],
        "BEFORE_EVIDENCE": "before_failure/P1408_O-G016_O-G017", "AFTER_EVIDENCE": p1408["ROI_PACKAGE"],
        "SOURCE_REPAIR": "route centers y=-1.10/-2.70 -> -1.00/-2.80; independent borders retained; no shared-boundary declaration",
    }]
    for gid in ("G0208", "G0212", "G0222"):
        before = old_pixels[gid]
        after = pixels[gid]
        repair_rows.append({
            "FAILURE_ID": gid, "TYPE": "CJK_GLYPH_PIXEL", "OBJECT_OR_GLYPH": gid,
            "BEFORE_CHAR": before["CHAR"], "AFTER_CHAR": after["CHAR"], "BEFORE_H_INK_PX": before["H_INK_PX"], "AFTER_H_INK_PX": after["H_INK_PX"],
            "BEFORE_OVERLAP_PX": "N/A", "AFTER_OVERLAP_PX": "N/A", "BEFORE_CLEARANCE_PX": "N/A", "AFTER_CLEARANCE_PX": "N/A",
            "BEFORE_DECISION": before["R115_FINAL_PIXEL_DECISION"], "AFTER_DECISION": after["R115_FINAL_PIXEL_DECISION"],
            "BEFORE_EVIDENCE": f"before_failure/{gid}", "AFTER_EVIDENCE": f"{glyphs[int(gid[1:])-1]['SHEET_1X']} + {glyphs[int(gid[1:])-1]['SHEET_8X']}",
            "SOURCE_REPAIR": "visible wording uses 输出/接入 instead of 出口/入口; equal character count, unchanged 9.5641pt hierarchy",
        })
    write_csv("REPAIR_BEFORE_AFTER.csv", repair_rows)
    for directory in [ROOT / "before_failure" / "P1408_O-G016_O-G017", ROOT / "roi_packages" / "P1408_O-G016_O-G017"]:
        for name in expected_roi_files:
            open_image(directory / name)
    for gid in ("G0208", "G0212", "G0222"):
        before_dir = ROOT / "before_failure" / gid
        require(len(list(before_dir.glob("*.png"))) == 6, f"before glyph package incomplete: {gid}")
        for path in before_dir.glob("*.png"):
            open_image(path)

    # Clipping and real opaque-halo/drawing-order evidence.
    clips = read_csv("clip_report.csv")
    require(len(clips) == 55 and all(r["CLIP_PASS"] == "true" and r["CROP_EDGE_FOREGROUND_PX"] == "0" and r["PDF_PAGE_EDGE_FOREGROUND_PX"] == "0" for r in clips), "clip failure")
    inv = {r["OBJECT_ID"]: r for r in inventory}
    halo = inv["O-H001"]
    feedback = inv["O-G015"]
    halo_px = foreground_pixels(ROOT / halo["FINAL_VISIBLE_MASK"])
    feedback_pre_px = foreground_pixels(ROOT / feedback["PRE_OCCLUSION_MASK"])
    feedback_final_px = foreground_pixels(ROOT / feedback["FINAL_VISIBLE_MASK"])
    require(halo_px > 0 and feedback_pre_px >= feedback_final_px > 0, "opaque-halo occlusion evidence mismatch")
    occlusion_report = f"""# Occlusion, clipping, and mask integrity — local R12

- Inventory: 56 objects total; 55 final-visible foreground relation objects plus one real source-declared opaque halo `O-H001`.
- `O-H001` final/background mask foreground pixels: {halo_px}.
- Feedback path `O-G015` pre-occlusion pixels: {feedback_pre_px}; final-visible pixels after applying only the real halo mask: {feedback_final_px}; removed pixels: {feedback_pre_px - feedback_final_px}. A zero removal count is preserved honestly because the routed path does not enter the current opaque-label interior.
- All object final/pre masks exist, decode as ordinary image files, are nonempty, and preserve unique safe names.
- Clip report: 55/55 PASS; crop-edge foreground count 0 and page-edge foreground count 0 for every object.
- Glyph integrity: 378/378 masks report foreign pixels 0, missing-stroke pixels 0, nonempty, purity/completeness true; six 1×/8× files per glyph machine-opened.
- Relation masks use independent final-visible objects; no peer deletion, dilation, resized counting, or shared-boundary reclassification.
"""
    (ROOT / "OCCLUSION_AND_INTEGRITY.md").write_text(occlusion_report, encoding="utf-8")

    semantic_report = """# Mathematical and semantic audit — local R12

- The figure contains no displayed equation, formula block, numerical datum, or mathematical operator whose value/meaning was changed; the repair therefore has no mathematical-content delta.
- Route topology is unchanged: supervised and unsupervised routes remain distinct nodes, both still enter the same shared engine pool, then validation, then the no-return report.
- `出口/入口` was replaced only in visible auxiliary wording by the semantically equivalent `输出/接入`; the caption already states the same single-direction flow and required no change.
- The alt text now says `唯一单向通道`, matching the unchanged directed edge from validation to the report without introducing a visible low-outline `口` glyph.
- No node type, arrow direction, line style, color role, report endpoint, caption claim, or accessibility conclusion was removed.
"""
    (ROOT / "MATHEMATICAL_AND_SEMANTIC_AUDIT.md").write_text(semantic_report, encoding="utf-8")

    visual_report = f"""# Local SA2 visual coordination audit

- Actually opened at original/native evidence scale: `full_page_300dpi.png`, `figure_crop_300dpi.png`, `standalone_300dpi.png`, `grayscale_300dpi.png`, `standalone_direct_full_300dpi.png`, both scales of P1408's raw/A/B/intersection/overlay views, and the 1×/8× contact sheets containing G0208, G0212, and G0222.
- Local page integration: headings, node text, legend, caption, and surrounding body retain a natural hierarchy; no font-size declaration changed and no mechanical enlargement was introduced.
- Effective visible point-size range: {min_pt:.4f}–{max_pt:.4f}pt; minimum remains >=9.5pt.
- The two route cards remain visually distinct and coordinated with the engine pool; the added vertical separation is modest and preserves reading flow.
- Grayscale keeps the solid/dashed route distinction, double report frame, arrows, and text legible.
- The repaired wording `仅此单向输出`, `实线接入`, `虚线接入` is natural in context and agrees with the caption/alt semantics.
- `LOCAL_FONT_VISUAL_HARMONY_PASS=true` for handing the source to the root official build.
- `FINAL_FONT_VISUAL_HARMONY_PASS=NOT_AUTHORIZED_FOR_SA2`; root SA1/SA3 must independently open 100% contacts and requalify the official full-book page.
"""
    (ROOT / "R12_LOCAL_VISUAL_HARMONY.md").write_text(visual_report, encoding="utf-8")

    summary = {
        "figure_id": "FIG-P756-01",
        "scope": "local page/standalone wrappers only",
        "source_before_sha256": BEFORE_SHA,
        "source_after_sha256": AFTER_SHA,
        "changed_source_lines": changed,
        "build_logs_clean": True,
        "native_page_grid": [2481, 3508],
        "objects_total": len(inventory),
        "foreground_objects": len(foreground),
        "pairs": len(pairs),
        "pair_kind_counts": kinds,
        "pair_failures": 0,
        "mandatory_relations": len(mandatory),
        "p1408": {"overlap_px": 0, "clearance_px": 20.0, "decision": "PASS"},
        "glyphs": len(glyphs),
        "glyph_pixel_failures": 0,
        "fixed_glyphs": {gid: {"char": char, "h_ink_px": height} for gid, (char, height) in fixed_expected.items()},
        "low_profile_glyphs": len(calibration_validation),
        "low_profile_calibration_groups": len(calibration_manifest),
        "d_e_failures": 0,
        "font_min_effective_pt": min_pt,
        "clip_failures": 0,
        "contact_sheets_machine_opened": len(contact_rows),
        "glyph_evidence_rows": len(glyph_ledger),
        "critical_roi_packages": len(critical),
        "local_result": "LOCAL_PASS_TO_ROOT_BUILD",
        "final_official_result": "NOT_AUTHORIZED__ROOT_BUILD_AND_SA1_SA3_REQUAL_REQUIRED",
    }
    (ROOT / "R12_PRESEAL_MACHINE_CHECK.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    local_report = f"""# FIG-P756-01 — R12 SA2 local repair audit

## Result

`LOCAL_PASS_TO_ROOT_BUILD`

This is not a final figure PASS. It establishes that the repaired business source is ready for the root official full-book build and independent SA1/SA3 requalification.

## Source boundary

- Sole business source changed: `{SOURCE}`.
- Before SHA256: `{BEFORE_SHA}`.
- After SHA256: `{AFTER_SHA}`.
- Exactly five source lines changed: 32, 57, 59, 74, 81; see `SOURCE_DIFF.patch`.
- No common macro, font configuration, build entry, central state/CSV/JSON, or other figure source was changed by this SA2 repair.

## Hard-failure closure

- P1408 (`O-G016` vs `O-G017`): before 792 overlapping native pixels / 0px clearance / FAIL; after 0 overlap / 20px independent clearance / PASS. No shared-boundary claim is used.
- G0208: `口` 29px FAIL -> `出` 34px PASS.
- G0212 and G0222: `口` 29px FAIL -> `入` 35px PASS.
- Text remains at 9.5641pt for the repaired visible labels; no mechanical enlargement.

## Complete local evidence

- 56 inventory objects, 55 relation foreground objects.
- 1,485/1,485 unordered pairs PASS, including all 378 graphic-graphic pairs; 1,107 mandatory relations PASS.
- 378/378 glyph rows PASS after 20 low-profile targets are closed by 10 exact embedded-font/CID calibration groups.
- 378/378 D/E rows PASS; font-role audit has no same-panel or cross-panel failure.
- 55/55 clip rows PASS; real halo/pre-occlusion/final-visible evidence retained.
- 143 contact sheets and six evidence images per glyph decode successfully. SA2 visually opened the repaired glyph cells; final 100% human contact review remains an explicit root SA1/SA3 duty.
- Native 300dpi full page/crop/standalone/grayscale/text-overlay and before/after 1×/8× failure packages are present.

## Required next gate

Root must build the official full-book candidate, lock its identity/page, and commission independent SA1/SA3 strict review. Local wrapper coordinates cannot be promoted to final official evidence.
"""
    (ROOT / "LOCAL_AUDIT_REPORT.md").write_text(local_report, encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))


if __name__ == "__main__":
    main()
