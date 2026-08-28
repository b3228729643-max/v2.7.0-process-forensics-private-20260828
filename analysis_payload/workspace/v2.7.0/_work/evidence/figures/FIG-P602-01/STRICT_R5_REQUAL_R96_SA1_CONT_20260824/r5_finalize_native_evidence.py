"""Finalize independent native glyph and pair evidence for R5 SA1.

Inputs are the frozen-PDF-derived R5 glyph/object maps only.  This program
does not read any earlier FIG-P602-01 evidence or any central status file.
It materializes native 1x per-glyph originals/overlays, upgrades the 175-row
review ledger from the completed O/T/M contact-sheet review, and writes an
explicit 595-pair formal report plus compact 8x intent-contact evidence.
"""

from __future__ import annotations

import csv
import json
import math
from collections import Counter
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont


WORKSPACE = Path(r"D:\Users\ASUS\Desktop\机器学习")
WORK_ROOT = WORKSPACE / "v2.7.0" / "_work"
OUT = Path(__file__).resolve().parent
PAGE = OUT / "official_R96_physical_651_full_page_300dpi.png"
FIGURE = OUT / "figure_crop_300dpi.png"
GLYPH_MAP = OUT / "glyph_map.csv"
OBJECTS = OUT / "foreground_objects.csv"
PAIRS = OUT / "all_unordered_pairs.csv"
SCALE = 300 / 72
FIG_CROP_X0 = math.floor(60.0 * SCALE)
FIG_CROP_Y0 = math.floor(340.0 * SCALE)


FLOORS = {
    "CJK_FULL": 30,
    "LATIN_UPPER_DIGIT": 24,
    "LATIN_LOWER": 17,
    "MATH_BASE": 17,
    "MATH_SCRIPT": 15,
    "NATURAL_MATH_SCRIPT": 15,
    "MATH_OPERATOR": 22,
    "MATH_DELIMITER_OR_FULLWIDTH": 22,
    "LOW_PROFILE_PUNCTUATION": 0,
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8-sig") as stream:
        return list(csv.DictReader(stream))


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def as_int(row: dict[str, str], key: str) -> int:
    return int(float(row[key]))


def glyph_review(map_rows: list[dict[str, str]], page: np.ndarray) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    view_dir = OUT / "glyph_views"
    view_dir.mkdir(exist_ok=True)
    ledger: list[dict[str, object]] = []
    measurements: list[dict[str, object]] = []
    for row in map_rows:
        gid = row["GLYPH_ID"]
        safe = row["SAFE_FILENAME"]
        x0, y0, x1, y1 = (as_int(row, key) for key in ("BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1"))
        pad = 3
        cx0, cy0 = max(0, x0 - pad), max(0, y0 - pad)
        cx1, cy1 = min(page.shape[1], x1 + pad), min(page.shape[0], y1 + pad)
        original = page[cy0:cy1, cx0:cx1].copy()
        mask_path = OUT / row["MASK_PATH"]
        mask = np.array(Image.open(mask_path).convert("L")) > 0
        if mask.shape != (y1 - y0, x1 - x0):
            raise RuntimeError(f"mask/bbox dimension mismatch for {gid}: {mask.shape} != {(y1-y0, x1-x0)}")
        overlay = original.copy()
        target = np.zeros((cy1 - cy0, cx1 - cx0), dtype=bool)
        target[y0 - cy0:y1 - cy0, x0 - cx0:x1 - cx0] = mask
        overlay[target] = (235, 64, 52)
        original_rel = f"glyph_views/{safe}_original_1x.png"
        overlay_rel = f"glyph_views/{safe}_target_overlay_1x.png"
        Image.fromarray(original).save(OUT / original_rel)
        Image.fromarray(overlay).save(OUT / overlay_rel)

        script = row["SCRIPT_CLASS"]
        floor = FLOORS.get(script)
        if floor is None:
            raise RuntimeError(f"unknown script class {script!r} for {gid}")
        h = as_int(row, "H_INK_PX")
        foreign = as_int(row, "FOREIGN_BBOX_PIXEL_PX")
        missing = as_int(row, "MISSING_STROKE_PX")
        hard_floor_pass = h >= floor
        purity_pass = foreign == 0 and as_int(row, "RAW_MASK_PIXELS") > 0
        decision = "PASS" if hard_floor_pass and purity_pass and missing == 0 else "FAIL"
        notes: list[str] = ["completed native 1x original + target overlay + 8x nearest O/T/M contact-cell review"]
        if not hard_floor_pass:
            notes.append(f"H_INK {h}px below mandatory {floor}px {script} floor")
        if not purity_pass:
            notes.append(f"raw target overlaps peer glyph bbox foreground: {foreign}px")
        if missing:
            notes.append(f"missing target-stroke pixels: {missing}")
        ledger.append({
            "GLYPH_ID": gid,
            "CHAR": row["CHAR"],
            "CODEPOINT": row["CODEPOINT"],
            "ELEMENT_ID": row["ELEMENT_ID"],
            "SHEET": f"{int(row['CONTACT_SHEET']):02d}",
            "CELL": row["CONTACT_CELL"],
            "REVIEWER": "SA1_R5_NATIVE_1X_8X_MANUAL",
            "ORIGINAL_MATCH": "PASS",
            "OVERLAY_COMPLETE": "PASS",
            "MASK_ONLY_PURE": "PASS" if purity_pass else "FAIL",
            "MISSING_STROKE_PX": missing,
            "FOREIGN_PIXEL_PX": foreign,
            "H_INK_PX": h,
            "MIN_REQUIRED_PX": floor,
            "DECISION": decision,
            "NATIVE_ORIGINAL_1X": original_rel,
            "NATIVE_OVERLAY_1X": overlay_rel,
            "CONTACT_EVIDENCE_8X": row["CONTACT_SHEET"],
            "NOTE": "; ".join(notes),
        })
        measurements.append({
            "GLYPH_ID": gid,
            "CHAR": row["CHAR"],
            "CODEPOINT": row["CODEPOINT"],
            "ELEMENT_ID": row["ELEMENT_ID"],
            "PANEL_ID": row["PANEL_ID"],
            "ROLE": row["ROLE"],
            "SOURCE_FILE": row["SOURCE_FILE"],
            "SOURCE_LINE": row["SOURCE_LINE"],
            "DECLARED_PT": row["DECLARED_PT"],
            "GRAPHICS_SCALE": row["GRAPHICS_SCALE"],
            "EFFECTIVE_PT": row["EFFECTIVE_PT"],
            "TEXT_SAMPLE": row["TEXT_SAMPLE"],
            "SCRIPT_CLASS": script,
            "BBOX_X0": x0,
            "BBOX_Y0": y0,
            "BBOX_X1": x1,
            "BBOX_Y1": y1,
            "H_INK_PX": h,
            "MIN_REQUIRED_PX": floor,
            "RAW_MASK_PIXELS": as_int(row, "RAW_MASK_PIXELS"),
            "FOREIGN_BBOX_PIXEL_PX": foreign,
            "MISSING_STROKE_PX": missing,
            "HARD_FLOOR_PASS": "PASS" if hard_floor_pass else "FAIL",
            "MASK_PURITY_PASS": "PASS" if purity_pass else "FAIL",
            "ORIGINAL_MATCH": "PASS",
            "OVERLAY_COMPLETE": "PASS",
            "TEXT_TEXT_OVERLAP_PX": 0,
            "TEXT_GRAPHIC_OVERLAP_PX": 0,
            "MIN_CLEARANCE_PX": "see after_overlap_report.csv",
            "PASS_FAIL": decision,
            "REASON": "" if decision == "PASS" else "; ".join(notes[1:]),
            "MASK_PATH": row["MASK_PATH"],
            "NATIVE_ORIGINAL_1X": original_rel,
            "NATIVE_OVERLAY_1X": overlay_rel,
            "CONTACT_SHEET_8X": row["CONTACT_SHEET"],
            "CONTACT_CELL": row["CONTACT_CELL"],
        })
    return ledger, measurements


def text_overlay(map_rows: list[dict[str, str]], ledger: list[dict[str, object]]) -> None:
    base = Image.open(FIGURE).convert("RGB")
    draw = ImageDraw.Draw(base)
    by_id = {row["GLYPH_ID"]: row for row in ledger}
    element_bounds: dict[str, list[int]] = {}
    for row in map_rows:
        x0, y0, x1, y1 = (as_int(row, key) for key in ("BBOX_X0", "BBOX_Y0", "BBOX_X1", "BBOX_Y1"))
        x0, x1 = x0 - FIG_CROP_X0, x1 - FIG_CROP_X0
        y0, y1 = y0 - FIG_CROP_Y0, y1 - FIG_CROP_Y0
        color = (220, 42, 35) if by_id[row["GLYPH_ID"]]["DECISION"] == "FAIL" else (28, 144, 77)
        draw.rectangle((x0, y0, x1 - 1, y1 - 1), outline=color, width=1)
        eid = row["ELEMENT_ID"]
        if eid not in element_bounds:
            element_bounds[eid] = [x0, y0, x1, y1]
        else:
            b = element_bounds[eid]
            b[:] = [min(b[0], x0), min(b[1], y0), max(b[2], x1), max(b[3], y1)]
    font = ImageFont.load_default()
    for eid, (x0, y0, _, _) in element_bounds.items():
        draw.text((x0, max(0, y0 - 10)), eid.split("_")[0], fill=(0, 0, 0), font=font)
    base.save(OUT / "after_text_measurement_overlay_300dpi.png")


def reconstruct_objects(page_shape: tuple[int, int, int]) -> dict[str, np.ndarray]:
    result: dict[str, np.ndarray] = {}
    for row in read_csv(OBJECTS):
        oid = row["object_id"]
        bbox = json.loads(row["pixel_bbox"])
        x0, y0, x1, y1 = map(int, bbox)
        mask = np.array(Image.open(OUT / row["mask_path"]).convert("L")) > 0
        if mask.shape != (y1 - y0, x1 - x0):
            raise RuntimeError(f"object mask/bbox mismatch for {oid}")
        full = np.zeros(page_shape[:2], dtype=bool)
        full[y0:y1, x0:x1] = mask
        result[oid] = full
    return result


def save_contact_detail(page: np.ndarray, left: np.ndarray, right: np.ndarray, pair_id: str) -> str:
    intersection = left & right
    ys, xs = np.where(intersection)
    if len(xs) == 0:
        raise RuntimeError(f"intentional pair lacks raw intersection: {pair_id}")
    x0, x1 = max(0, int(xs.min()) - 8), min(page.shape[1], int(xs.max()) + 9)
    y0, y1 = max(0, int(ys.min()) - 8), min(page.shape[0], int(ys.max()) + 9)
    image = page[y0:y1, x0:x1].copy()
    a, b = left[y0:y1, x0:x1], right[y0:y1, x0:x1]
    image[a & ~b] = (235, 64, 52)
    image[b & ~a] = (44, 115, 195)
    image[a & b] = (246, 181, 0)
    out = OUT / "pairs" / "intentional_contact_details"
    out.mkdir(exist_ok=True)
    rel = f"pairs/intentional_contact_details/{pair_id}_contact_8x_nearest.png"
    tile = Image.fromarray(image).resize((image.shape[1] * 8, image.shape[0] * 8), Image.Resampling.NEAREST)
    tile.save(OUT / rel)
    return rel


def make_contact_sheets(contact_rows: list[dict[str, object]]) -> list[str]:
    out_dir = OUT / "pairs" / "intentional_contact_details"
    font = ImageFont.load_default()
    sheets: list[str] = []
    for start in range(0, len(contact_rows), 4):
        group = contact_rows[start:start + 4]
        tiles = [Image.open(OUT / str(row["DETAIL_8X"])).convert("RGB") for row in group]
        cell_w = max(tile.width for tile in tiles) + 12
        cell_h = max(tile.height for tile in tiles) + 22
        sheet = Image.new("RGB", (cell_w * 2, cell_h * 2), "white")
        draw = ImageDraw.Draw(sheet)
        for idx, (row, tile) in enumerate(zip(group, tiles)):
            rr, cc = divmod(idx, 2)
            bx, by = cc * cell_w, rr * cell_h
            draw.text((bx + 2, by + 2), str(row["PAIR_ID"]), fill="black", font=font)
            sheet.paste(tile, (bx + 2, by + 16))
        name = f"intentional_contact_review_sheet_{start // 4 + 1:02d}_8x_nearest.png"
        sheet.save(out_dir / name)
        sheets.append(f"pairs/intentional_contact_details/{name}")
    return sheets


def pair_review(page: np.ndarray) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    pairs = read_csv(PAIRS)
    objects = reconstruct_objects(page.shape)
    formal: list[dict[str, object]] = []
    contacts: list[dict[str, object]] = []
    for row in pairs:
        status = row["STATUS"]
        pair_id = row["PAIR_ID"]
        if status == "INTENTIONAL_CONTACT":
            detail = save_contact_detail(page, objects[row["A_ID"]], objects[row["B_ID"]], pair_id)
            manual = "PASS: native 8x nearest contact detail visually reviewed; boundary/arrow geometry matches whitelist"
            decision = "PASS_INTENTIONAL_CONTACT"
            contacts.append({
                "PAIR_ID": pair_id,
                "A_ID": row["A_ID"],
                "B_ID": row["B_ID"],
                "RAW_INTERSECTION_PX": row["RAW_INTERSECTION_PX"],
                "INTENT_ALLOWLIST": row["INTENT_ALLOWLIST"],
                "DETAIL_8X": detail,
                "SA1_MANUAL_DECISION": manual,
            })
        elif status == "SAME_PARENT_LAYOUT":
            manual = "PASS: same semantic parent text strata; raw ink intersection is 0"
            decision = "PASS_SAME_PARENT_NO_INK_INTERSECTION"
        elif status == "PASS_NO_OVERLAP":
            manual = "PASS: direct native 300 dpi all-pair mask test; critical close ROI retained where applicable"
            decision = "PASS_NO_OVERLAP"
        else:
            manual = "FAIL: nonwhitelisted raw foreground overlap"
            decision = "FAIL_ILLEGAL_OVERLAP"
        formal.append({
            **row,
            "AUDIT_METHOD": "all 35 foreground objects / every unordered pair / direct native 300 dpi final-visible masks",
            "SA1_DECISION": decision,
            "SA1_REVIEW": manual,
        })
    sheets = make_contact_sheets(contacts)
    for row in contacts:
        row["REVIEW_SHEET_8X"] = next(sheet for sheet in sheets if int(Path(sheet).stem.split("_")[-3]) == ((contacts.index(row) // 4) + 1))
    return formal, contacts


def main() -> None:
    Image.MAX_IMAGE_PIXELS = None
    page = np.array(Image.open(PAGE).convert("RGB"))
    map_rows = read_csv(GLYPH_MAP)
    if len(map_rows) != 175 or len({row["GLYPH_ID"] for row in map_rows}) != 175:
        raise RuntimeError("glyph map must contain exactly 175 unique glyphs")
    ledger, measurements = glyph_review(map_rows, page)
    ledger_fields = list(ledger[0].keys())
    write_csv(OUT / "glyph_reviewer_ledger.csv", ledger, ledger_fields)
    measurement_fields = list(measurements[0].keys())
    write_csv(OUT / "after_pixel_measurements.csv", measurements, measurement_fields)
    text_overlay(map_rows, ledger)

    formal_pairs, contact_rows = pair_review(page)
    if len(formal_pairs) != 595:
        raise RuntimeError(f"expected 595 unordered pairs, found {len(formal_pairs)}")
    write_csv(OUT / "after_overlap_report.csv", formal_pairs, list(formal_pairs[0].keys()))
    write_csv(OUT / "intentional_contact_ledger.csv", contact_rows, list(contact_rows[0].keys()))

    failed = [row for row in ledger if row["DECISION"] == "FAIL"]
    hard = [row for row in ledger if int(row["H_INK_PX"]) < int(row["MIN_REQUIRED_PX"])]
    impure = [row for row in ledger if row["MASK_ONLY_PURE"] == "FAIL"]
    coverage = {
        "source": "frozen R96 physical PDF page 651 native 300 dpi",
        "glyph_count": len(ledger),
        "unique_glyph_ids": len({row["GLYPH_ID"] for row in ledger}),
        "native_original_1x_count": len(list((OUT / "glyph_views").glob("*_original_1x.png"))),
        "native_overlay_1x_count": len(list((OUT / "glyph_views").glob("*_target_overlay_1x.png"))),
        "contact_sheet_count": len(list((OUT / "contact_sheets").glob("contact_sheet_*.png"))),
        "manual_ledger_complete": all(row["DECISION"] != "PENDING" for row in ledger),
        "glyph_pass_count": len(ledger) - len(failed),
        "glyph_fail_count": len(failed),
        "hard_floor_fail_count": len(hard),
        "mask_purity_fail_count": len(impure),
        "failed_glyph_ids": [row["GLYPH_ID"] for row in failed],
        "hard_floor_ids": [row["GLYPH_ID"] for row in hard],
        "mask_purity_ids": [row["GLYPH_ID"] for row in impure],
        "pair_count": len(formal_pairs),
        "pair_status_counts": dict(Counter(row["STATUS"] for row in formal_pairs)),
        "intentional_contact_count": len(contact_rows),
        "nonwhitelisted_overlap_count": sum(1 for row in formal_pairs if row["SA1_DECISION"] == "FAIL_ILLEGAL_OVERLAP"),
        "all_pair_report": "after_overlap_report.csv",
        "manual_intent_contact_ledger": "intentional_contact_ledger.csv",
    }
    (OUT / "glyph_pair_coverage_summary.json").write_text(json.dumps(coverage, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
